

function load_new_model_description($model_id){
    /* HERE WE SHOULD SEND AJAX QUERY TO SERVER
     * TO GET CONTENT OF THE MODEL'S DESCRIPTION
     * FILE.*/
     var content = 'Unknown';
     for (var i=0; i<$presets.length; i++) {
        if ($presets[i].name == $model_id) {
            content = $presets[i].description;
            break;
        }
    }

    return content;
}


function show_description_modal($model_id) {
    $('#modal_content').text(load_new_model_description($model_id));
    get_storage_info($model_id);
    $('#descModal').modal('show');
}

function show_operations_modal($op_id) {
    $('#opModal').modal('show');
}

function show_addusers_modal() {
    query_users_groups();
}

function show_usersinfo_modal(flag) {
    if (flag != undefined) {
        $selected_user = null;
    }
    prepare_usersinfo_modal();
}