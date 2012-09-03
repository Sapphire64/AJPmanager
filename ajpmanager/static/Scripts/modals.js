

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

function show_operations_modal($model_id) {
    $('#op_modal_content').text(load_new_model_description($model_id))
    $('#opModal').modal('show');
}

