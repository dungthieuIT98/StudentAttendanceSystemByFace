"""
main/model_registry.py
======================
Process-wide singleton for every AI model used by the face-attendance pipeline.

All heavy assets (RetinaFace DNN, MiniFASNet weights, FaceNet frozen graph,
sklearn classifier) are loaded ONCE on the first call to ``get_registry()``.
Subsequent calls return the already-initialised instance immediately.

This eliminates:
  - FaceNet re-load on every new MJPEG stream connection
  - Repeated torch.load() calls caused by the broken single-slot cache in the
    old AntiSpoofPredict.predict() (alternating between 2 .pth files = 2 disk
    reads per frame)
  - Two separate RetinaFace DNN networks (reg.py + lecturer_views.py both
    instantiated AntiSpoofPredict at module level)
"""

from __future__ import annotations

import logging
import math
import os
import pickle
import threading
from collections import OrderedDict

import cv2
import numpy as np
import torch
import torch.nn.functional as F
import tensorflow as tf

from main.src.model_lib.MiniFASNet import (
    MiniFASNetV1,
    MiniFASNetV2,
    MiniFASNetV1SE,
    MiniFASNetV2SE,
)
from main.src.utility import get_kernel, parse_model_name
from main.src.data_io import transform as trans
from main import facenet

logger = logging.getLogger(__name__)

_MODEL_MAP = {
    "MiniFASNetV1": MiniFASNetV1,
    "MiniFASNetV2": MiniFASNetV2,
    "MiniFASNetV1SE": MiniFASNetV1SE,
    "MiniFASNetV2SE": MiniFASNetV2SE,
}

_LOCK = threading.Lock()
_INSTANCE: ModelRegistry | None = None


class ModelRegistry:
    """Holds all AI models loaded exactly once per process."""

    DETECTOR_CONFIDENCE = 0.9

    def __init__(self) -> None:
        self._ready = False

        # --- RetinaFace (OpenCV DNN / Caffe) ---
        self.detector: cv2.dnn_Net | None = None

        # --- Anti-spoof (MiniFASNet, PyTorch) ---
        # Maps full .pth path → (torch model, h_input, w_input, scale)
        self.antispoof_models: dict[str, tuple] = {}
        self.antispoof_device = torch.device(
            "cuda:0" if torch.cuda.is_available() else "cpu"
        )

        # --- FaceNet (TF v1 frozen graph) ---
        self.facenet_graph: tf.Graph | None = None
        self.facenet_sess = None
        self._images_ph = None
        self._embeddings_tensor = None
        self._phase_train_ph = None

        # --- Sklearn classifier ---
        self.classifier = None
        self.class_names: list[str] = []

    # ------------------------------------------------------------------
    # Initialisation
    # ------------------------------------------------------------------

    def load_all(
        self,
        detector_prototxt: str = "main/resources/detection_model/deploy.prototxt",
        detector_caffemodel: str = "main/resources/detection_model/Widerface-RetinaFace.caffemodel",
        antispoof_dir: str = "main/resources/anti_spoof_models",
        facenet_pb: str = "main/Models/20180402-114759.pb",
        classifier_pkl: str = "main/Models/facemodel.pkl",
    ) -> None:
        logger.info("[Registry] Loading all AI models …")
        self._load_detector(detector_prototxt, detector_caffemodel)
        self._load_antispoof_models(antispoof_dir)
        self._load_facenet(facenet_pb)
        self._load_classifier(classifier_pkl)
        self._ready = True
        logger.info("[Registry] All models ready  device=%s", self.antispoof_device)

    def _load_detector(self, prototxt: str, caffemodel: str) -> None:
        self.detector = cv2.dnn.readNetFromCaffe(prototxt, caffemodel)
        logger.info("[Registry] RetinaFace DNN loaded")

    def _load_antispoof_models(self, antispoof_dir: str) -> None:
        for fname in sorted(os.listdir(antispoof_dir)):
            if not fname.endswith(".pth"):
                continue
            fpath = os.path.join(antispoof_dir, fname)
            h, w, model_type, scale = parse_model_name(fname)
            model = _MODEL_MAP[model_type](conv6_kernel=get_kernel(h, w)).to(self.antispoof_device)
            state = torch.load(fpath, map_location=self.antispoof_device)
            if next(iter(state)).startswith("module."):
                state = OrderedDict((k[7:], v) for k, v in state.items())
            model.load_state_dict(state)
            model.eval()
            self.antispoof_models[fpath] = (model, h, w, scale)
            logger.info("[Registry] Anti-spoof loaded: %s  device=%s", fname, self.antispoof_device)

    def _load_facenet(self, facenet_pb: str) -> None:
        self.facenet_graph = tf.Graph()
        with self.facenet_graph.as_default():
            facenet.load_model(facenet_pb)
            self._images_ph = self.facenet_graph.get_tensor_by_name("input:0")
            self._embeddings_tensor = self.facenet_graph.get_tensor_by_name("embeddings:0")
            self._phase_train_ph = self.facenet_graph.get_tensor_by_name("phase_train:0")
        self.facenet_sess = tf.compat.v1.Session(graph=self.facenet_graph)
        logger.info("[Registry] FaceNet loaded  graph=%s", id(self.facenet_graph))

    def _load_classifier(self, classifier_pkl: str) -> None:
        with open(classifier_pkl, "rb") as f:
            self.classifier, self.class_names = pickle.load(f)
        logger.info("[Registry] Classifier loaded — %d classes", len(self.class_names))

    # ------------------------------------------------------------------
    # Inference helpers — called from the hot loop in reg.py
    # ------------------------------------------------------------------

    def get_bbox(self, img: np.ndarray) -> list[int] | None:
        """
        Run RetinaFace on *img* and return [x, y, w, h] for the highest-confidence
        face, or None if confidence is below threshold.
        """
        h, w = img.shape[:2]
        aspect = w / h
        small = img
        if w * h >= 192 * 192:
            small = cv2.resize(
                img,
                (int(192 * math.sqrt(aspect)), int(192 / math.sqrt(aspect))),
                interpolation=cv2.INTER_LINEAR,
            )
        blob = cv2.dnn.blobFromImage(small, 1, mean=(104, 117, 123))
        self.detector.setInput(blob, "data")
        out = self.detector.forward("detection_out").squeeze()
        if out.ndim == 1:
            out = out[np.newaxis, :]
        best = int(np.argmax(out[:, 2]))
        if float(out[best, 2]) < self.DETECTOR_CONFIDENCE:
            return None
        l = out[best, 3] * w
        t = out[best, 4] * h
        r = out[best, 5] * w
        b = out[best, 6] * h
        return [int(l), int(t), int(r - l + 1), int(b - t + 1)]

    def predict_antispoof(
        self, frame: np.ndarray, bbox: list[int], cropper
    ) -> np.ndarray:
        """
        Run ALL pre-loaded anti-spoof models and return the summed softmax scores
        (shape: (1, 3)).  No disk I/O — weights were loaded in load_all().
        """
        transform = trans.Compose([trans.ToTensor()])
        total = np.zeros((1, 3), dtype=np.float32)
        for fpath, (model, h_in, w_in, scale) in self.antispoof_models.items():
            param = {
                "org_img": frame,
                "bbox": bbox,
                "scale": scale,
                "out_w": w_in,
                "out_h": h_in,
                "crop": scale is not None,
            }
            img_patch = cropper.crop(**param)
            t = transform(img_patch).unsqueeze(0).to(self.antispoof_device)
            with torch.no_grad():
                result = model(t)
                result = F.softmax(result, dim=1).cpu().numpy()
            total += result
        return total

    def get_embedding(self, face_array: np.ndarray) -> np.ndarray:
        """
        Return FaceNet embedding for a prewhitened (1, 160, 160, 3) float array.
        Thread-safe: TF sessions support concurrent run() calls from different
        threads when using the default (non-GIL-releasing) CPU kernel.
        """
        return self.facenet_sess.run(
            self._embeddings_tensor,
            feed_dict={
                self._images_ph: face_array,
                self._phase_train_ph: False,
            },
        )

    def reload_classifier(self, path: str = "main/Models/facemodel.pkl") -> None:
        """Hot-reload the sklearn classifier after retraining, without restarting."""
        with open(path, "rb") as f:
            self.classifier, self.class_names = pickle.load(f)
        logger.info("[Registry] Classifier reloaded — %d classes", len(self.class_names))


def get_registry() -> ModelRegistry:
    """Return the process-level singleton, initialising it on the first call."""
    global _INSTANCE
    if _INSTANCE is None:
        with _LOCK:
            if _INSTANCE is None:
                _INSTANCE = ModelRegistry()
                _INSTANCE.load_all()
    return _INSTANCE
