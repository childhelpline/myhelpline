// Custom javascripts

// toggle event for forms
$(function() {

    $("#form_collapse").on('hidden.bs.collapse', function() {
        $('#toggle_btn_i_span').text(gettext('Open search'));
        $('#toggle_btn_i').attr('class', 'glyphicon glyphicon-zoom-in');
    });

    $("#form_collapse").on('shown.bs.collapse', function() {
        $('#toggle_btn_i_span').text(gettext('Hide search'));
        $('#toggle_btn_i').attr('class', 'glyphicon glyphicon-zoom-out');
    });
});
