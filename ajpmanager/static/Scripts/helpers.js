
function jgrowl_error($type, $err) {

    var header;

    if ($type == 1) {
        header = 'Server error';
    }
    else if ($type == 2) {
        header = 'Connection error';
    }

    else {
        header = 'Error';
    }

    $.jGrowl($err , {
        theme:  'danger',
        header: header,
        life: 10000,
        closer: false
    });

}


function jgrowl_success($msg) {

    var header = 'Success';

    $.jGrowl($msg , {
        theme:  'success',
        header: header,
        life: 10000,
        closer: false
    });

}