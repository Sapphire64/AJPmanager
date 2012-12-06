var $per_page = 15
var $displayed_list = new Array();

function generate_machines_list(page) {
    if (!$processed){
        $displayed_list = new Array();

        // This must be rewritten :)
        var $machines = $online;
        for (var i=0; i<$machines.length; i++){
            machine = $machines[i];
            machine.status = 'Running';
            machine.memory = machine.memory + 'M';
            $displayed_list.push(machine);
            if ($stopping_machines.indexOf(machine.name) != -1) { // Is in array?
                machine.status = 'Stopping';
            }
        }

        var $machines = $offline;
        for (var i=0; i<$machines.length; i++){
            machine = $machines[i];
            machine.status = 'Stopped';
            machine.memory = machine.memory + 'M';
            $displayed_list.push(machine);

            if ($stopping_machines.indexOf(machine.name) != -1) { // Is in array?
                $stopping_machines.pop(machine.name);
            }
        }
        $processed = true;
        $displayed_list.sort();
    }
    append_vms()
}


/*
function machines_sort(a, b){
//Compare "a" and "b" in some fashion, and return -1, 0, or 1
}
*/

function append_vms() {
    $('#machines_table tbody').empty();

    var row = new Array();
    var label_;

    for (var i=0; i<$displayed_list.length; i++){
        if ($displayed_list[i].status == 'Running') {
            label_ = 'success';
        }
        else if ($displayed_list[i].status == 'Stopped') {
            label_ = 'important';
        }
        else {
            label_ = 'warning';
        }
        row.push('<tr>');
        row.push('<td>'+ $displayed_list[i].id + '</td>');
        row.push('<td>'+ $displayed_list[i].name + '</td>');
        row.push('<td>'+ $displayed_list[i].type + '</td>');
        row.push('<td><span class="label label-info">0.00 0.00 0.00</span></td>');
        row.push('<td><span class="label label-info">'+ $displayed_list[i].cpu + '</span></td>');
        row.push('<td><span class="label label-info">'+ $displayed_list[i].memory + '</span></td>');
        row.push('<td><span class="label label-' + label_ + '">'+ $displayed_list[i].status + '</span></td>');
        row.push('<td><input type="checkbox" onchange="note_checkboxes(\'' + $displayed_list[i].id + '\',\''+
            $displayed_list[i].name + '\',\'' +  $displayed_list[i].type + '\',\'' +
            $displayed_list[i].status + '\', this);"></td>'); // this is odd, but anyway
        row.push('</tr>');
    }
    row = row.join('\n');
    $("#machines_table > tbody").append(row);
    clear_select_menu();
}



function append_presets() {
    $('#presets_table tbody').empty();

    var row = new Array();
    var label_;

    for (var i=0; i<$presets.length; i++){
        row.push('<tr>');
        row.push('<td>1</td>');
        row.push('<td>'+ $presets[i].name + '</td>');
        row.push('<td><div class="label label-success pointer" onclick="show_description_modal(\'' + $presets[i].name + '\');">Install</div></td>');
        row.push('</tr>');
    }
    row = row.join('\n');
    $("#presets_table > tbody").append(row);
}

function append_storage_info(free, preset_size) {
    $('#storage_info').empty();
    var $storage =  'Required:<b> ' + preset_size + '</b><br>' + 'Available:<b> ' + free + ' </b>';
    $('#storage_info').append($storage);
}

$users_list = new Array();

function generate_users_list(data) {
    $('#users_table tbody').empty();

    $users_list = new Array();

    var row = new Array();
    var label_;

    for (var i=0; i<data.length; i++){

        if (data[i].status == 'True') {
            label_ = 'success';
            text_ = 'online';
        }
        else {
            label_ = 'warning';
            text_ = 'offline'
        }
        row.push('<tr>');
        row.push('<td>'+ data[i].uid + '</td>');
        row.push('<td>'+ data[i].username + '</td>');
        row.push('<td>'+ data[i].first_name + '</td>');
        row.push('<td>'+ data[i].last_name + '</td>');
        row.push('<td>'+ data[i].group + '</td>');
        row.push('<td><span class="label label-' + label_ + '">'+ text_ + '</span></td>');
        row.push('<td><input id="user' + data[i].uid + '" type="checkbox" onchange="users_note_checkboxes(\'' + data[i].uid + '\',\''+
            data[i].username + '\',\'' +  data[i].group + '\',\'' +
            data[i].status + '\', this);"></td>'); // this is odd, but anyway
        row.push('</tr>');

        $users_list.push(data[i].uid);
    }
    row = row.join('\n');
    $("#users_table > tbody").append(row);


}

function append_user_info(data) {
    $('#machines_select').empty();

    $('#change_password_container').addClass('hide');
    $('#update_user_info_btn').addClass('hide');
    $('#old_password_group').addClass('hide');

    $('#view_email').attr('disabled');
    $('#view_first_name').attr('disabled');
    $('#view_last_name').attr('disabled');
    $('#view_group').attr('disabled');

    document.getElementById('view_username').value = data.username;

    if (data.online) {
        status = 'btn btn-success';
    }
    else {
        status = 'btn btn-danger';
    }
    document.getElementById('online_img').setAttribute('class', status);

    document.getElementById('view_email').value = data.email;
    document.getElementById('mailto').href = 'mailto:' + data.email;

    document.getElementById('view_group').value = data.group.split(':')[1];

    if (data.first_name) {
        first_name = data.first_name;;
    }
    else {
        first_name = '- Not specified -';
    }
    document.getElementById('view_first_name').value = first_name;

    if (data.last_name) {
        last_name = data.last_name;
    }
    else {
        last_name = '- Not specified -';
    }
    document.getElementById('view_last_name').value = last_name;

    // Allow to edit:
    if ($privileged || data.self_profile) {
        if (!$privileged || data.self_profile) {
            $('#old_password_group').removeClass('hide');
        }
        else {
            $('#view_group').removeAttr('disabled');
        }

        $('#change_password_container').removeClass('hide');

        $('#update_user_info_btn').removeClass('hide');
        $('#view_email').removeAttr('disabled');
        $('#view_first_name').removeAttr('disabled');
        $('#view_last_name').removeAttr('disabled');


        if (document.getElementById('view_first_name').value == '- Not specified -') {
            document.getElementById('view_first_name').value = '';
        }

        if (document.getElementById('view_last_name').value == '- Not specified -') {
            document.getElementById('view_last_name').value = '';
        }

        if ($privileged && !data.self_profile) {
            for (var i=0; i<data.all_machines.length; i++) {
                $('#machines_select').append(new Option(data.all_machines[i], '' + data.all_machines[i], true, false));

                if (data.machines.indexOf(data.all_machines[i]) != -1) {
                    $("#machines_select").val( data.all_machines[i] ).attr('selected',true);
                }
            }
        }
        else if ($privileged && (data.self_profile || data.group == 'group:admins' || data.group == 'group:moderators')) {
            $('#machines_select').append(new Option("Only for regular users", "None", true, false));
        }


    }

    $('#infoModal').modal('show'); // Showing actual modal
}

