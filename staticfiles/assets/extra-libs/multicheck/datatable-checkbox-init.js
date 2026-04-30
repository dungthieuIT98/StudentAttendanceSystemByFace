/* datatable-checkbox-init.js — initialises multicheck on every DataTable */
(function ($) {
    "use strict";

    $(function () {
        $("table.dataTable").multiCheck();

        // Re-attach after DataTables redraws (paging, search, etc.)
        $(document).on("draw.dt", function () {
            $("table.dataTable").multiCheck();
        });
    });
})(jQuery);
