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

    if ($privileged) {
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



function query_users_groups() {
    $.ajax({
        type: "POST",
        url: "/engine.ajax",
        data: JSON.stringify({'query': 'get_groups_list'}),
        contentType: 'application/json; charset=utf-8'
    }).done(function ( data ) {
            $('#groups_select').empty();
            for (var i=0; i<data.data.length; i++) {
                console.log(data.data);
                $('#groups_select').append(new Option(data.data[i], ' ' + data.data[i], true, false));
            }
            $('#usersModal').modal('show');
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
                jgrowl_error(1, 'Error message from the server during attempt to restore settings: <br>' + data.answer);
            }
        });

}



function add_user() {
    $('#user_success_block').empty();
    $('#user_success_block').addClass('hide');
    $('#user_danger_block').empty();
    $('#user_danger_block').addClass('hide');


    var answer = new Object();

    // APPENDING BLOCK
    answer.username = document.getElementById('new_username').value;
    answer.email = document.getElementById('new_email').value;
    answer.first_name = document.getElementById('new_first_name').value;
    answer.last_name = document.getElementById('new_last_name').value;
    answer.new_password = document.getElementById('new_password').value;
    answer.new_password_repeat = document.getElementById('new_password_repeat').value;

    var e = document.getElementById("groups_select")
    try {
        answer.selected_group = e.options[e.selectedIndex].text;
    }
    catch (TypeError) {
        answer.selected_group = "";
    }

    answer.new_group = document.getElementById('add_new_group_input').value;

    answer.send_email = document.getElementById('send_email').checked;

    // DATA PROCESSING BLOCK

    if (!answer.username || !answer.email || !answer.new_password || !answer.new_password_repeat) {
        adduser_notification(2, 'Please fill all required fields!')
        return
    }

    else if (!validateEmail(answer.email)) {
        adduser_notification(2, 'Bad email address provided');
        return
    }

    else if (answer.new_password != answer.new_password_repeat) {
        adduser_notification(2, 'Password fields does not match!')
        document.getElementById('new_password').value = '';
        document.getElementById('new_password_repeat').value = '';
        return
    }

    else {
        $.ajax({
            type: "POST",
            url: "/engine.ajax",
            data: JSON.stringify({'query': 'add_user', 'data': answer}),
            contentType: 'application/json; charset=utf-8'
        }).done(function ( data ) {
                console.log(data);
                var status;
                var message;
                if (data.status) {
                    status = 1;
                    message = 'User was successfully added.'

                    document.getElementById('new_username').value = '';
                    document.getElementById('new_email').value = '';
                    document.getElementById('new_first_name').value = '';
                    document.getElementById('new_last_name').value = '';
                    document.getElementById('new_password').value = '';
                    document.getElementById('new_password_repeat').value = '';
                    document.getElementById('add_new_group_input').value = '';
                }
                else {
                    status = 2;
                    message = data.answer;
                }
                adduser_notification(status, message);
            });
    }


    console.log(answer)
}


function delete_user() {
    if (!$selected_user) {
        return;
    }

    var id = $('#selected_user_id').html();
    if (id != $selected_user) {
        jgrowl_error(1, "Interface error, deletion user_id is not the ID you are viewing. Please try to refresh this page.");
        return;
    }
    var username = $('#selected_user_name').html();


    var agree=confirm("Are you sure you want to delete " + username + " account? This cannot be undone.");
    if (agree) {
        $.ajax({
            type: "POST",
            url: "/engine.ajax",
            data: JSON.stringify({'query': 'delete_user', 'data': $selected_user}),
            contentType: 'application/json; charset=utf-8'
        }).done(function ( data ) {
                console.log(data);
                if (data.status) {
                    jgrowl_success("User " + username + " was successfully deleted!");
                    show_users_list();
                }
                else {
                    jgrowl_error(-1, 'User deletion failed:<br>' + data.answer);
                }
            });
    }
    else {
        return;
    }
}


function prepare_usersinfo_modal() {
    var $send_data, $by_name;
    if ($selected_user != null) {
        $send_data = $selected_user;
        $by_name = false;
    }
    else {
        // definitely user clicked 'your info'
        $send_data = $self_username; // setted username by template engine
        $by_name = true;
    }

    $.ajax({
        type: "POST",
        url: "/engine.ajax",
        data: JSON.stringify({'query': 'get_user_info', 'data': [$send_data, $by_name]}),
        contentType: 'application/json; charset=utf-8'
    }).done(function ( data ) {
            console.log(data);
            if (data.status) {
                append_user_info(data.answer);
            }
            else {
                jgrowl_error(1, 'Error message from the server during attempt to get user info: <br>' + data.answer);
            }
        });

}



function apply_settings() {

    var answer = new Object();

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


