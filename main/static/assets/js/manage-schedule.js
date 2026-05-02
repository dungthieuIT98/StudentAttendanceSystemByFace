(function () {
  function showModal(id) {
    const el = document.getElementById(id);
    if (!el || typeof bootstrap === "undefined") return;
    bootstrap.Modal.getOrCreateInstance(el).show();
  }

  $(document).on("click", "#addSchedule", function (e) {
    e.preventDefault();
    showModal("addNewScheduleModal");
  });

  $(document).on("click", ".js-delete-schedule", function (e) {
    e.preventDefault();
    const groupKey = this.getAttribute("data-id");
    if (!groupKey || !window.AdminCrudUrls) return;
    const a = document.getElementById("confirmDeleteButton");
    if (a) a.setAttribute("href", window.AdminCrudUrls.scheduleGroupDelete(groupKey));
    const span = document.getElementById("classroomIdToDelete");
    if (span) span.textContent = groupKey;
    showModal("confirmDeleteModal");
  });

  $(document).on("click", ".js-edit-schedule", function (e) {
    e.preventDefault();
    const groupKey = this.getAttribute("data-id");
    if (!groupKey || !window.AdminCrudUrls) return;

    const form = document.getElementById("editScheduleForm");
    if (form) form.setAttribute("action", window.AdminCrudUrls.scheduleGroupEdit(groupKey));

    fetch(window.AdminCrudUrls.scheduleGroupGetInfo(groupKey), {
      headers: { "X-Requested-With": "XMLHttpRequest" },
    })
      .then((r) => r.json())
      .then((data) => {
        const s = data.schedule;
        const idField = document.getElementById("id_classroom_edit");
        const nameField = document.getElementById("name_edit");
        const beginDateField = document.getElementById("begin_date_edit");
        const endDateField = document.getElementById("end_date_edit");
        const dayField = document.getElementById("day_of_week_begin_edit");
        const beginTimeField = document.getElementById("begin_time_edit");
        const endTimeField = document.getElementById("end_time_edit");
        const lecturerIdField = document.getElementById("id_lecturer_edit");

        if (idField) idField.value = s.id_classroom ?? "";
        if (nameField) nameField.value = s.name ?? "";
        if (beginDateField) beginDateField.value = s.begin_date ?? "";
        if (endDateField) endDateField.value = s.end_date ?? "";
        if (dayField) {
          const values = (s.day_of_week_begin_list || []).map((x) => String(x));
          Array.from(dayField.options).forEach((opt) => {
            opt.selected = values.includes(opt.value);
          });
          if (typeof $ !== "undefined" && $(dayField).data("select2")) {
            $(dayField).trigger("change");
          }
        }

        const bt = (s.begin_time || "").toString().slice(0, 5);
        const et = (s.end_time || "").toString().slice(0, 5);
        if (beginTimeField) beginTimeField.value = bt;
        if (endTimeField) endTimeField.value = et;

        if (lecturerIdField) lecturerIdField.value = s.id_lecturer ?? "";

        showModal("editScheduleModal");
      })
      .catch((err) => console.error("schedule get-info error", err));
  });
})();