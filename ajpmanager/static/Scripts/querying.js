var $online = new Array();
var $offline = new Array();
var $presets = new Array();
var $processed = false;


function query_all(){
    // TODO: Also this function should query for running processes

    var no_cache = false;

    if ($stopping_machines.length > 0) {
        no_cache = true;
    }

    $.ajax({
        type: "POST",
        url: "/engine.ajax",
        data: JSON.stringify({'query': 'get_vms_list', 'no_cache': no_cache}),
        contentType: 'application/json; charset=utf-8'
    }).done(function ( data ) {
            console.log(data);
            if (data.status) {
                $online = data.data.online;
                $offline = data.data.offline;
                $processed = false;
                generate_machines_list(0);
            }
            else {
                jgrowl_error(1, 'Error message from the server during attempt to recieve machines list: <br>' + data.answer);
            }
        });

    $.ajax({
        type: "POST",
        url: "/engine.ajax",
        data: JSON.stringify({'query': 'get_presets_list'}),
        contentType: 'application/json; charset=utf-8'
    }).done(function ( data ) {
            console.log(data);
            if (data.status) {
                $presets = data.data;
                append_presets();
                //console.log(data.data);
            }
            else {
                jgrowl_error(1, 'Error message from the server during attempt to recieve presets list: <br>' + data.answer);
            }
        });

}

var $stopping_machines = new Array();

function operate_machine(query) {

    if ($active_objects.length == 1) {
        name = $active_objects[0];
    }
    else {
        return
    }

    if (query == 'stop') {
        $stopping_machines.push(name);
        query_all();
    }

    $.ajax({
        type: "POST",
        url: "/engine.ajax",
        data: JSON.stringify({'query': 'machines_control', 'data': name, 'operation': query}),
        contentType: 'application/json; charset=utf-8'
    }).done(function ( data ) {
            console.log ('Answered!')
            console.log(data);
            if (data.status) {
                query_all();
                //console.log(data.data);
            }
            else {
                jgrowl_error(1, 'Error message from the server during attempt to recieve presets list: <br>' + data.answer);
            }
        });


}

var $total;
var $free;
var $used;
var $preset_size;

function get_storage_info(machine) {

    $.ajax({
        type: "POST",
        url: "/engine.ajax",
        data: JSON.stringify({'query': 'get_storage_info', 'machine': machine}),
        contentType: 'application/json; charset=utf-8'
    }).done(function ( data ) {
            console.log(data);
            if (data.status) {

                $total = data.data.total;
                $free = data.data.free;
                $used = data.data.used;
                $preset_size = data.data.preset_size;

                //var total = ($total/1024/1024/1024).toFixed(2) + 'GB';
                //var used = ($used/1024/1024/1024).toFixed(2) + 'GB';
                var free = ($free/1024/1024/1024).toFixed(2) + 'GB';
                var preset_size = ($preset_size/1024/1024/1024).toFixed(2) + 'GB';
                append_storage_info(free, preset_size)
            }
            else {
                jgrowl_error(1, 'Error message from the server during attempt to recieve storage info: <br>' + data.answer);
            }
        });


}


function query_settings() {
    $.ajax({
        type: "POST",
        url: "/engine.ajax",
        data: JSON.stringify({'query': 'get_settings'}),
        contentType: 'application/json; charset=utf-8'
    }).done(function ( data ) {
            console.log(data);
            if (data.status) {
                // Set content
                document.getElementById('vmprovider_settings').value = data.data.provider;
                document.getElementById('vmmanager_settings').value = data.data.vmmanager;
                document.getElementById('path_settings').value = data.data.path;
                document.getElementById('images_settings').value = data.data.images;
                document.getElementById('presets_settings').value = data.data.presets;
                document.getElementById('image_settings').value = data.data.vmimage;
                document.getElementById('config_settings').value = data.data.config;
                document.getElementById('description_settings').value = data.data.description;


                // ^^^^^^^^^^
                $('#machines_list').addClass('hide');
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


function query_users_list() {
    $.ajax({
        type: "POST",
        url: "/engine.ajax",
        data: JSON.stringify({'query': 'get_users_list'}),
        contentType: 'application/json; charset=utf-8'
    }).done(function ( data ) {
            console.log(data);

            $('#machines_list').addClass('hide');
            $('#presets_list').addClass('hide');
            $('#users_screen').removeClass('hide');

            $('#users_settings').removeClass('hide');

            $('#main_entry').removeClass('active');
            $('#users_entry').addClass('active').removeClass('hide');
            $('#quick_manage_block').addClass('hide');
            generate_users_list(data.data);
        });
}





function restore_default_settings() {
    $.ajax({
        type: "POST",
        url: "/engine.ajax",
        data: JSON.stringify({'query': 'restore_default_settings'}),
        contentType: 'application/json; charset=utf-8'
    }).done(function ( data ) {
            console.log(data);
            if (data.status) {
                // Set content
                jgrowl_success('Default settings were restored');
                query_settings();

            }
            else {
                jgrowl_error(1, 'Error message from the server during attempt to recieve settings: <br>' + data.answer);
            }
        });

}




function apply_settings() {

    answer = new Object();

    answer.provider = document.getElementById('vmprovider_settings').value;
    answer.vmmanager = document.getElementById('vmmanager_settings').value;
    answer.path = document.getElementById('path_settings').value;
    answer.images = document.getElementById('images_settings').value;
    answer.presets = document.getElementById('presets_settings').value;;
    answer.vmimage = document.getElementById('image_settings').value;
    answer.config = document.getElementById('config_settings').value;
    answer.description = document.getElementById('description_settings').value;


    $.ajax({
        type: "POST",
        url: "/engine.ajax",
        data: JSON.stringify({'query': 'apply_settings', 'data': answer}),
        contentType: 'application/json; charset=utf-8'
    }).done(function ( data ) {
            console.log(data);
            if (data.status) {
                jgrowl_success('Settings were applied');
                query_settings();
            }
            else {
                jgrowl_error(1, 'Error message from the server during attempt to apply new settings: <br>' + data.answer);
            }
        });

}