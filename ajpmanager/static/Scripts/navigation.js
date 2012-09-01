
function show_detailed_info($edit) {

    var $result = false;

    if ($multiple){
        return $result;
    }
    if ($active_objects.length == 0) {
        return $result;
    }

    $.ajax({
        type: "POST",
        url: "/engine.ajax",
        data: JSON.stringify({'query': 'get_machine_info', 'item': $active_objects[0]}),
        contentType: 'application/json; charset=utf-8'
    }).done(function ( data ) {
            if (data.status) {
                // Set content
                //
                // ^^^^^^^^^^
                // Here we are pushing server info into EDIT and VIEW forms (!)
                //
                if (!$edit) {
                    $('#running_machines_list').addClass('hide');
                    $('#machine_detailed_info').removeClass('hide');
                    $('#project_info').removeClass('hide');
                    $('#main_entry').removeClass('active');
                    $('#view_entry').addClass('active').removeClass('hide');
                    $('#quick_manage_block').addClass('hide');
                }
                $result = true;
            }
            else {
                jgrowl_error(1, 'Error message from the server during attempt to recieve machine info: <br>' + data.answer);
            }
    });

}

function show_settings() {
    show_default_screen(false);

    $.ajax({
        type: "POST",
        url: "/engine.ajax",
        data: JSON.stringify({'query': 'get_settings'}),
        contentType: 'application/json; charset=utf-8'
    }).done(function ( data ) {
            console.log(data);
            if (data.status) {
                // Set content
                //
                // ^^^^^^^^^^
                $('#running_machines_list').addClass('hide');
                $('#settings_screen').removeClass('hide');
                $('#project_info').removeClass('hide');
                $('#main_entry').removeClass('active');
                $('#settings_entry').addClass('active').removeClass('hide');
                $('#quick_manage_block').addClass('hide');
            }
            else {
                jgrowl_error(1, 'Error message from the server during attempt to recieve settings: <br>' + data.answer);
            }
        });

}

function show_help() {
    show_default_screen(false);

    $('#running_machines_list').addClass('hide');
    $('#help_screen').removeClass('hide');
    $('#project_info').removeClass('hide');
    $('#main_entry').removeClass('active');
    $('#help_entry').addClass('active').removeClass('hide');
    $('#quick_manage_block').addClass('hide');

}

function show_default_screen(query_server) {

    if (query_server) {
       query_all();
    }

    $('#machines_list').removeClass('hide');
    $('#machine_detailed_info').addClass('hide');
    $('#project_info').addClass('hide');
    $('#edit_machine_screen').addClass('hide');
    $('#settings_screen').addClass('hide');
    $('#help_screen').addClass('hide');
    $('#main_entry').addClass('active');
    $('#view_entry').removeClass('active').addClass('hide');
    $('#edit_entry').removeClass('active').addClass('hide');

    $('#settings_entry').removeClass('active');
    $('#help_entry').removeClass('active');

    $('#quick_manage_block').removeClass('hide');

}


var $active_objects = new Array();
var $multiple = false;


function edit_selected_item(){

    if (!show_detailed_info(true)) {
        return
    }

    $('#machines_list').addClass('hide');
    $('#edit_machine_screen').removeClass('hide');
    $('#project_info').removeClass('hide');
    $('#main_entry').removeClass('active');
    $('#edit_entry').addClass('active').removeClass('hide');
    $('#quick_manage_block').addClass('hide');


}


function note_checkboxes(id, name, type, status, object){
    console.log(id, name, type);

    if (object.checked) {
        $active_objects.push(name);
    }
    else {
        $active_objects.pop(name);
    }
    check_multiple_select();

    if ($active_objects.length == 1) {
        $('#selected_id').text(id);
        $('#selected_name').text(name);
        $('#selected_type').text(type);
        // Query to the server for object's information (also with detailed info);
        if (status == 'Stopped'){
            $('#run_button').removeClass('disabled');
            $('#pause_button').addClass('disabled');
            $('#stop_button').addClass('disabled');
        }
        else if (status == 'Running') {
            $('#run_button').addClass('disabled');
            $('#pause_button').removeClass('disabled');
            $('#stop_button').removeClass('disabled');
        }
    }
    else{
        clear_select_menu();
        return
    }

}

function check_multiple_select(){

    if ($active_objects.length == 1) {
        $multiple = false;
        $('#detailed_info_button').removeClass('disabled');
        $('#edit_button').removeClass('disabled');
    }
    else {
        $multiple = true;
        $('#detailed_info_button').addClass('disabled');
        $('#edit_button').addClass('disabled');
    }
}

function clear_select_menu() {
    $active_objects = new Array();
    $('#selected_id').text('-');
    $('#selected_name').text('');
    $('#selected_type').text('');
    $('#run_button').addClass('disabled');
    $('#pause_button').addClass('disabled');
    $('#stop_button').addClass('disabled');
    $('#edit_button').addClass('disabled');
    $('#detailed_info_button').addClass('disabled');
}
