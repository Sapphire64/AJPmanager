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

