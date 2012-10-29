

function load_new_model_description($model_id){
     var content = 'Unknown';
     for (var i=0; i<$presets.length; i++) {
        if ($presets[i].name == $model_id) {
            content = $presets[i].description;
            break;
        }
    }

    return content;
}

var $active_preset = '';

function show_description_modal($model_id) {
    $('#modal_content').text(load_new_model_description($model_id));

    $active_preset = $model_id;

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