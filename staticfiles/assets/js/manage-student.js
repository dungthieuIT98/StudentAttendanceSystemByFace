(function () {
  let addStudentChecking = false;
  let addStudentIntervalId = null;
  let captureIntervalId = null;

  function showModal(id) {
    const el = document.getElementById(id);
    if (!el || typeof bootstrap === "undefined") return;
    bootstrap.Modal.getOrCreateInstance(el).show();
  }

  $(document).on("click", "#addStudent", function (e) {
    e.preventDefault();
    showModal("addNewStudentModal");
  });

  $(document).on("click", "#addStudentButton", function (event) {
    event.preventDefault();
    const idStudentField = document.getElementById("id_student");
    const studentNameField = document.getElementById("student_name");
    const emailField = document.getElementById("email");
    const phoneField = document.getElementById("phone");
    const addressField = document.getElementById("address");
    const birthdayField = document.getElementById("birthday");
    const pathImageFolderField = document.getElementById("PathImageFolder");
    const videoElement = document.getElementById("video-feed");
    if (
      !idStudentField ||
      !studentNameField ||
      !emailField ||
      !phoneField ||
      !addressField ||
      !birthdayField ||
      !pathImageFolderField ||
      !videoElement ||
      !window.AdminCrudUrls
    )
      return;

    if (
      idStudentField.value === "" ||
      studentNameField.value === "" ||
      emailField.value === "" ||
      phoneField.value === "" ||
      addressField.value === "" ||
      birthdayField.value === "" ||
      pathImageFolderField.value === ""
    ) {
      alert("Vui lòng điền thông tin");
      return;
    }

    const studentId = idStudentField.value;
    if (addStudentChecking) {
      clearInterval(addStudentIntervalId);
      addStudentIntervalId = null;
      addStudentChecking = false;
      return;
    }
    videoElement.src = window.AdminCrudUrls.studentLiveVideoFeed(studentId);
    addStudentIntervalId = setInterval(() => {
      fetch(window.AdminCrudUrls.studentCheckCapture)
        .then((response) => response.json())
        .then((data) => {
          if (data.capture_status === 1) {
            alert("Success");
            const form = document.getElementById("addStudentForm");
            if (form) form.submit();
            clearInterval(addStudentIntervalId);
            addStudentIntervalId = null;
            addStudentChecking = false;
          }
        })
        .catch((error) => console.error("Error:", error));
    }, 1000);
    addStudentChecking = true;
  });

  $(document).on("change", "#id_student", function () {
    const idStudentField = document.getElementById("id_student");
    const pathImageFolderField = document.getElementById("PathImageFolder");
    if (idStudentField && pathImageFolderField) {
      pathImageFolderField.value =
        "./main/Dataset/FaceData/processed/" + idStudentField.value;
    }
  });

  $(document).on("click", "#train-button", function () {
    let timerInterval;
    Swal.fire({
      title: "Thông báo!",
      html: "Quá trình training đang được diễn ra, vui lòng đợi !!!!",
      timer: 20000,
      timerProgressBar: true,
      didOpen: () => {
        Swal.showLoading();
        timerInterval = setInterval(() => {}, 100);
      },
      willClose: () => {
        clearInterval(timerInterval);
      },
    }).then((result) => {
      if (result.dismiss === Swal.DismissReason.timer) {
        console.log("I was closed by the timer");
      }
    });
    if (!window.AdminCrudUrls) return;
    fetch(window.AdminCrudUrls.studentTrain)
      .then((response) => response.json())
      .then((data) => {
        Swal.fire({
          position: "center",
          icon: "success",
          title: data.resuil,
          showConfirmButton: false,
          timer: 3000,
        });
        setTimeout(function () {
          location.reload();
        }, 2000);
      })
      .catch((error) => {
        Swal.fire({
          icon: "error",
          title: "Lỗi",
          text: "Có lỗi xảy ra trong quá trình thực hiện yêu cầu.",
        });
        console.error("Fetch Error:", error);
      });
  });

  window.capture = function (studentId) {
    if (!window.AdminCrudUrls) return;
    if (captureIntervalId) {
      clearInterval(captureIntervalId);
      captureIntervalId = null;
    }
    fetch(window.AdminCrudUrls.studentGetInfo(studentId), {
      headers: { "X-Requested-With": "XMLHttpRequest" },
    })
      .then((r) => r.json())
      .then((data) => {
        const s = data.student;
        $("#id_student_capture").val(s.id_student);
        $("#student_name_capture").val(s.student_name);
        $("#email_capture").val(s.email);
        $("#phone_capture").val(s.phone);
        $("#address_capture").val(s.address);
        $("#birthday_capture").val(s.birthday);
        $("#PathImageFolder_capture").val(
          "./main/Dataset/FaceData/processed/" + studentId
        );
        const modal = document.getElementById("captureStudentModal");
        if (modal && typeof bootstrap !== "undefined") {
          bootstrap.Modal.getOrCreateInstance(modal).show();
        }
      });

    const videoElement = document.getElementById("video-feed_student");
    if (!videoElement) return;
    videoElement.src = window.AdminCrudUrls.studentLiveVideoFeed(studentId);
    captureIntervalId = setInterval(() => {
      fetch(window.AdminCrudUrls.studentCheckCapture)
        .then((response) => response.json())
        .then((data) => {
          if (data.capture_status === 1) {
            alert("Capture Success");
            const captureForm = document.getElementById("captureStudentForm");
            if (captureForm) {
              captureForm.action =
                window.AdminCrudUrls.studentCapture(studentId);
              captureForm.submit();
            }
            clearInterval(captureIntervalId);
            captureIntervalId = null;
          }
        })
        .catch((error) => console.error("Error:", error));
    }, 1000);
  };
})();

window.confirmDeleteStudent = function (studentId) {
  const form = document.getElementById("studentDeleteForm");
  if (form && window.AdminCrudUrls) {
    form.action = window.AdminCrudUrls.studentDelete(studentId);
  }
  const span = document.getElementById("studentIdToDelete");
  if (span) span.textContent = studentId;
  const el = document.getElementById("confirmDeleteStudentModal");
  if (el && typeof bootstrap !== "undefined") {
    bootstrap.Modal.getOrCreateInstance(el).show();
  }
};

window.editStudent = function (studentId) {
  const editForm = document.getElementById("editStudentForm");
  if (editForm && window.AdminCrudUrls) {
    editForm.action = window.AdminCrudUrls.studentEdit(studentId);
  }
  if (!window.AdminCrudUrls) return;
  fetch(window.AdminCrudUrls.studentGetInfo(studentId), {
    headers: { "X-Requested-With": "XMLHttpRequest" },
  })
    .then((r) => r.json())
    .then((data) => {
      const s = data.student;
      $("#id_student_edit").val(s.id_student);
      $("#student_name_edit").val(s.student_name);
      $("#email_edit").val(s.email);
      $("#phone_edit").val(s.phone);
      $("#address_edit").val(s.address);
      $("#birthday_edit").val(s.birthday);
      $("#PathImageFolder_edit").val(s.PathImageFolder);
      const modal = document.getElementById("editStudentModal");
      if (modal && typeof bootstrap !== "undefined") {
        bootstrap.Modal.getOrCreateInstance(modal).show();
      }
    });
};
