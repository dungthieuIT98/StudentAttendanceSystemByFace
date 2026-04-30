(function () {
  function showModal(id) {
    const el = document.getElementById(id);
    if (!el || typeof bootstrap === "undefined") return;
    bootstrap.Modal.getOrCreateInstance(el).show();
  }

  $(document).on("click", "#addLecturer", function (e) {
    e.preventDefault();
    showModal("addNewLecturerModal");
  });
})();

window.confirmDeleteLecturer = function (lecturerId) {
  const form = document.getElementById("lecturerDeleteForm");
  if (form && window.AdminCrudUrls) {
    form.action = window.AdminCrudUrls.lecturerDelete(lecturerId);
  }
  const span = document.getElementById("lecturerIdToDelete");
  if (span) span.textContent = lecturerId;
  const el = document.getElementById("confirmDeleteLecturerModal");
  if (el && typeof bootstrap !== "undefined") {
    bootstrap.Modal.getOrCreateInstance(el).show();
  }
};

window.editLecturer = function (lecturerId) {
  const form = document.getElementById("editLecturerForm");
  if (form && window.AdminCrudUrls) {
    form.action = window.AdminCrudUrls.lecturerEdit(lecturerId);
  }
  if (!window.AdminCrudUrls) return;
  fetch(window.AdminCrudUrls.lecturerGetInfo(lecturerId), {
    headers: { "X-Requested-With": "XMLHttpRequest" },
  })
    .then((r) => r.json())
    .then((data) => {
      const lec = data.lecturer;
      const set = (id, v) => {
        const el = document.getElementById(id);
        if (el) el.value = v;
      };
      set("id_lecturer", lec.id_staff);
      set("lecture_name", lec.staff_name);
      set("email", lec.email);
      set("phone", lec.phone);
      set("address", lec.address);
      set("birthday", lec.birthday);
      const modal = document.getElementById("editLecturerModal");
      if (modal && typeof bootstrap !== "undefined") {
        bootstrap.Modal.getOrCreateInstance(modal).show();
      }
    })
    .catch((err) => console.error(err));
};
