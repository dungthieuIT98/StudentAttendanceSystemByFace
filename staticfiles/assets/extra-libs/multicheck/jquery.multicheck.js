/* jquery.multicheck.js — minimal stub */
(function ($) {
    "use strict";

    $.fn.multiCheck = function (options) {
        return this.each(function () {
            var $table = $(this);
            // "Check all" header checkbox toggles every row checkbox
            $table.on("change", "thead input[type='checkbox']", function () {
                var checked = $(this).prop("checked");
                $table.find("tbody input[type='checkbox']").prop("checked", checked);
            });
            // When all row checkboxes are manually checked, tick the header too
            $table.on("change", "tbody input[type='checkbox']", function () {
                var total = $table.find("tbody input[type='checkbox']").length;
                var checkedCount = $table.find("tbody input[type='checkbox']:checked").length;
                $table.find("thead input[type='checkbox']").prop("checked", total === checkedCount);
            });
        });
    };
})(jQuery);
