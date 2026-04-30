(function () {
  function showModal(id) {
    const el = document.getElementById(id);
    if (!el || typeof bootstrap === "undefined") return;
    bootstrap.Modal.getOrCreateInstance(el).show();
  }

  function getClassroomIdFromPage() {
    const el =
      document.querySelector(".js-delete-all-students[data-classroom-id]") ||
      document.querySelector(".js-delete-student-in-class[data-classroom-id]");
    return el ? el.getAttribute("data-classroom-id") : null;
  }

  $(document).on("click", "#addStudentInClass", function (e) {
    e.preventDefault();
    const classroomId = getClassroomIdFromPage();
    const form = document.getElementById("addNewStudentInClassForm");
    if (form && classroomId && window.AdminCrudUrls) {
      form.setAttribute("action", window.AdminCrudUrls.studentInClassAdd(classroomId));
    }
    showModal("addNewStudentInClassModal");
  });

  $(document).on("click", "#addListStudentInClass", function (e) {
    e.preventDefault();
    const classroomId = getClassroomIdFromPage();
    const form = document.getElementById("addStudentIntoClassroomForm");
    if (form && classroomId && window.AdminCrudUrls) {
      form.setAttribute("action", window.AdminCrudUrls.studentInClassAddList(classroomId));
    }
    showModal("addListStudentInClassModal");
  });

  $(document).on("click", ".js-delete-student-in-class", function (e) {
    e.preventDefault();
    const classroomId = this.getAttribute("data-classroom-id");
    const studentId = this.getAttribute("data-student-id");
    if (!classroomId || !studentId || !window.AdminCrudUrls) return;
    const a = document.getElementById("confirmDeleteButton");
    if (a) a.setAttribute("href", window.AdminCrudUrls.studentInClassDelete(classroomId, studentId));
    const span = document.getElementById("studentIdToDelete");
    if (span) span.textContent = studentId;
    showModal("confirmDeleteModal");
  });

  $(document).on("click", ".js-delete-all-students", function (e) {
    e.preventDefault();
    const classroomId = this.getAttribute("data-classroom-id");
    if (!classroomId || !window.AdminCrudUrls) return;
    const a = document.getElementById("confirmDeleteAllButton");
    if (a) a.setAttribute("href", window.AdminCrudUrls.studentInClassDeleteAll(classroomId));
    showModal("confirmDeleteAllModal");
  });
})();

