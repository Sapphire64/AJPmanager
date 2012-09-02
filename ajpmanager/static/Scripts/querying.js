var $online = new Array();
var $offline = new Array();
var $presets = new Array();
var $processed = false;


function query_all(){
    // TODO: Also this function should query for running processes
    $.ajax({
        type: "POST",
        url: "/engine.ajax",
        data: JSON.stringify({'query': 'get_vms_list'}),
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
                $presets = data.presets;
                //console.log(data.data);
            }
            else {
                jgrowl_error(1, 'Error message from the server during attempt to recieve presets list: <br>' + data.answer);
            }
        });

}


function operate_machine(query) {

    if ($active_objects.length == 1) {
        name = $active_objects[0];
    }
    else {
        return
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
                $presets = data.presets;
                query_all();
                //console.log(data.data);
            }
            else {
                jgrowl_error(1, 'Error message from the server during attempt to recieve presets list: <br>' + data.answer);
            }
        });


}

