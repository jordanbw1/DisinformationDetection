$(document).ready(function(){
    $(".edit-button").click(function(){
        var $container = $(this).closest('li');
        $container.find(".edit-button").toggle();
        $container.find(".submit-button").toggle();
        $container.find(".cancel-button").toggle();
        $container.find(".input-field").attr("readonly", false);
    });

    $(".cancel-button").click(function(){
        var $container = $(this).closest('li');
        $container.find(".edit-button").toggle();
        $container.find(".submit-button").toggle();
        $container.find(".cancel-button").toggle();
        $container.find(".input-field").attr("readonly", true);
        var inputField = $container.find(".input-field");
        var originalField = $container.find(".original-field");
        inputField.val(originalField.val());
    });
});
