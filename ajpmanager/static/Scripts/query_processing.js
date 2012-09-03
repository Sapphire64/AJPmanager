var $per_page = 15
var $displayed_list = new Array();

function generate_machines_list(page) {
    if (!$processed){
        $displayed_list = new Array();

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