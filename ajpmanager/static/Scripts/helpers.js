
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
        //theme:  'danger',
        header: header,
        closer: false
        // Should set up timeout (increase)
    });

}