jQuery(function($) {
    $('form[data-async]').live('submit', function(event) {
        var $form = $(this);
        var $target = $($form.attr('action'));

        $.ajax({
            type: $form.attr('method'),
            url: $form.attr('action'),
            data: $form.serialize(),

            success: function(data, status) {
                $target.html(data);
                $('#myModal').modal('hide');
            }
        });
       event.defaultPrevented();
    });
});