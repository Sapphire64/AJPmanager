

function load_new_model_description($model_id){
    /* HERE WE SHOULD SEND AJAX QUERY TO SERVER
     * TO GET CONTENT OF THE MODEL'S DESCRIPTION
     * FILE.*/
    var content = 'I am description of the model ' + $model_id;
    return content;
}

function show_description_modal($model_id) {
    $('#modal_content').text(load_new_model_description($model_id))
    $('#myModal').modal('show');
}


