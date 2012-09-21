
var $current_vnc = '';


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
    query_settings();
}

function restore_settings() {
    query_settings();
}

function restore_default_settings_ask() {
        var agree=confirm("Are you sure you want to restore default settings?");
        if (agree)
            restore_default_settings();
        else
            return false ;


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
    $('#presets_list').removeClass('hide');
    $('#machine_detailed_info').addClass('hide');
    $('#noVNC_screen').addClass('hide');
    $('#project_info').addClass('hide');
    $('#edit_machine_screen').addClass('hide');
    $('#users_screen').addClass('hide');
    $('#settings_screen').addClass('hide');
    $('#help_screen').addClass('hide');
    $('#main_entry').addClass('active');
    $('#vnc_entry').removeClass('active').addClass('hide');
    $('#view_entry').removeClass('active').addClass('hide');
    $('#edit_entry').removeClass('active').addClass('hide');

    $('#users_settings').addClass('hide');

    $('#unvnc_button').addClass('hide');
    $('#vnc_button').removeClass('hide');

    $('#users_entry').removeClass('active');
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
        if ($stopping_machines.indexOf($active_objects[0]) != -1) { // Is in array?
            $('#run_button').addClass('disabled');
            $('#pause_button').addClass('disabled');
            $('#stop_button').removeClass('disabled');
            $('#destroy_button').removeClass('hide');
        }
        else if (status == 'Stopped'){
            $('#run_button').removeClass('disabled');
            $('#pause_button').addClass('disabled');
            $('#stop_button').addClass('disabled');
            $('#destroy_button').addClass('hide');
        }
        else if (status == 'Running') {
            $('#run_button').addClass('disabled');
            $('#pause_button').removeClass('disabled');
            $('#stop_button').removeClass('disabled');
            $('#destroy_button').addClass('hide');
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
        $('#vnc_button').removeClass('disabled');
    }
    else {
        $multiple = true;
        $('#detailed_info_button').addClass('disabled');
        $('#vnc_button').addClass('disabled');
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
    $('#vnc_button').addClass('disabled');
    $('#destroy_button').addClass('hide');
    $('#detailed_info_button').addClass('disabled');
}

function activate_vnc_screen() {
    if ($active_objects.length == 1) {
        noVNC_connect($active_objects[0]);
    }
}

function show_vnc_screen() {
    show_default_screen(false)

    $current_vnc = $active_objects[0];
    $('#machines_list').addClass('hide');
    $('#noVNC_screen').removeClass('hide');
    $('#main_entry').removeClass('active');
    $('#vnc_entry').addClass('active');
    $('#vnc_entry').removeClass('hide');

    $('#vnc_button').addClass('hide');
    $('#unvnc_button').removeClass('hide');
}


function show_users_list() {
    show_default_screen(false);
    query_users_list();
}



function unshow_vnc_screen() {
    noVNC_release();
    //show_default_screen(false);
}