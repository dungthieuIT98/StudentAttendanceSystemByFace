(function () {
  function showModal(id) {
    const el = document.getElementById(id);
    if (!el || typeof bootstrap === "undefined") return;
    bootstrap.Modal.getOrCreateInstance(el).show();
  }

  function ensureCkeditor(textareaId) {
    if (typeof CKEDITOR === "undefined") return;
    const inst = CKEDITOR.instances[textareaId];
    if (inst) return;
    CKEDITOR.replace(textareaId);
  }

  $(document).on("click", "#addNotification", function (e) {
    e.preventDefault();
    // BlogForm uses "id_body"
    ensureCkeditor("id_body");
    showModal("addNewNotification");
  });

  $(document).on("click", ".js-delete-notification", function (e) {
    e.preventDefault();
    const id = this.getAttribute("data-id");
    if (!id || !window.AdminCrudUrls) return;
    const a = document.getElementById("confirmDeleteButton");
    if (a) a.setAttribute("href", window.AdminCrudUrls.notificationDelete(id));
    const span = document.getElementById("blog_postID");
    if (span) span.textContent = id;
    showModal("notificationDeleteModal");
  });

  $(document).on("click", ".js-edit-notification", function (e) {
    e.preventDefault();
    const id = this.getAttribute("data-id");
    if (!id || !window.AdminCrudUrls) return;

    const form = document.getElementById("editNotificationForm");
    if (form) form.setAttribute("action", window.AdminCrudUrls.notificationEdit(id));

    fetch(window.AdminCrudUrls.notificationGetInfo(id), {
      headers: { "X-Requested-With": "XMLHttpRequest" },
    })
      .then((r) => r.json())
      .then((data) => {
        const p = data.blog_post;
        const title = document.getElementById("id_title_edit");
        const type = document.getElementById("id_type_edit");
        if (title) title.value = p.title || "";
        if (type) type.value = p.type || "ALL";

        ensureCkeditor("id_body_edit");
        if (typeof CKEDITOR !== "undefined" && CKEDITOR.instances.id_body_edit) {
          CKEDITOR.instances.id_body_edit.setData(p.body || "");
        } else {
          const body = document.getElementById("id_body_edit");
          if (body) body.value = p.body || "";
        }

        showModal("editNotificationModal");
      })
      .catch((err) => console.error("notification get-info error", err));
  });
})();