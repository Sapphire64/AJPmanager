function query_all(){
    // TODO: Also this function should query for running processes
    $.ajax({
        type: "POST",
        url: "/engine.ajax",
        data: JSON.stringify({'query': 'get_vms_list'}),
        contentType: 'application/json; charset=utf-8'
    }).done(function ( data ) {
            if (data.status) {
                // Set content
                //
                // ^^^^^^^^^^
                console.log(data.data);
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
            if (data.status) {
                // Set content
                //
                // ^^^^^^^^^^
                console.log(data.data);
            }
            else {
                jgrowl_error(1, 'Error message from the server during attempt to recieve presets list: <br>' + data.answer);
            }
        });
}