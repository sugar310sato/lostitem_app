document.addEventListener("DOMContentLoaded", function () {
    // 全て選択ボタン
    document.getElementById("selectAll").addEventListener("click", function () {
        const checkboxes = document.querySelectorAll('input[type="checkbox"][name="item_ids"]');
        checkboxes.forEach((checkbox) => {
            checkbox.checked = true;
        });
    });

    // 選択解除ボタン
    document.getElementById("deselectAll").addEventListener("click", function () {
        const checkboxes = document.querySelectorAll('input[type="checkbox"][name="item_ids"]');
        checkboxes.forEach((checkbox) => {
            checkbox.checked = false;
        });
    });
});