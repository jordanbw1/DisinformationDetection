$(document).ready(function(){
    $(".edit-button").click(function(){
        var $container = $(this).closest('li');
        $container.find(".edit-button").toggle();
        $container.find(".submit-button").toggle();
        $container.find(".cancel-button").toggle();
    });

    $(".cancel-button").click(function(){
        var $container = $(this).closest('li');
        $container.find(".edit-button").toggle();
        $container.find(".submit-button").toggle();
        $container.find(".cancel-button").toggle();
    });
});
