// $(document).ready(function () {
//     var $item_class_M = $('#item_class_M');
//     var $item_class_S = $('#item_class_S');

//     $('#item_class_L').change(function () {
//         var itemClassLVal = $(this).val();

//         // Initially hide all options
//         $item_class_M.find('option').hide();

//         // Then show only those options that match the selected value
//         $item_class_M.find('option').each(function () {
//             var itemClassMVal = $(this).data('val');
//             if (itemClassLVal === itemClassMVal) {
//                 $(this).show();
//             }
//         });

//         // Reset the selections
//         $item_class_M.val('');
//         $item_class_S.val('');
//         $item_class_S.find('option').hide();
//     });

//     $('#item_class_M').change(function () {
//         var itemClassMVal = $(this).val();

//         // Initially hide all options
//         $item_class_S.find('option').hide();

//         // Then show only those options that match the selected value
//         $item_class_S.find('option').each(function () {
//             var itemClassSVal = $(this).data('val');
//             if (itemClassMVal === itemClassSVal) {
//                 $(this).show();
//             }
//         });

//         // Reset the selection
//         $item_class_S.val('');
//     });
// });

$(document).ready(function () {
    var $item_class_L = $('#item_class_L');
    var $item_class_M = $('#item_class_M');
    var $item_class_S = $('#item_class_S');

    function filterOptions() {
        var itemClassLVal = $item_class_L.val();
        $item_class_M.find('option').hide().filter(function () {
            return $(this).data('val') === itemClassLVal;
        }).show();

        var itemClassMVal = $item_class_M.find('option:visible:first').val();
        $item_class_M.val(itemClassMVal).trigger('change');

        $item_class_S.find('option').hide().filter(function () {
            return $(this).data('val') === itemClassMVal;
        }).show();

        var itemClassSVal = $item_class_S.find('option:visible:first').val();
        $item_class_S.val(itemClassSVal);
    }

    $item_class_L.change(function () {
        filterOptions();
    });

    $item_class_M.change(function () {
        var itemClassMVal = $(this).val();
        $item_class_S.find('option').hide().filter(function () {
            return $(this).data('val') === itemClassMVal;
        }).show();
        $item_class_S.val('');
    });

    // ページが読み込まれたときにデフォルト値に基づいてフィルタリングを実行
    filterOptions();
});
