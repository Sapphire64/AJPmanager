
function jgrowl_error($type, $err) {

    var header;

    if ($type == 1) {
        header = 'Server error';
    }
    else if ($type == 2) {
        header = 'Connection error';
    }
    else if ($type == 3) {
        header = 'Form error';
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


function adduser_notification($type, $message) {
    var $block;
    var $prefix;

    if ($type == 1) { // Success
        $block = $('#user_success_block')
        $prefix = '<b>Success!</b> ';
    }
    else if ($type == 2) { // Success
        $block = $('#user_danger_block')
        $prefix = '<b>Error!</b> ';
    }
    $block.append($prefix + $message);
    $block.removeClass('hide');
}


function setCookie(name, value, props) {
    props = props || {};
    var exp = props.expires;
    if (typeof exp == "number" && exp) {
        var d = new Date();
        d.setTime(d.getTime() + exp*1000);
        exp = props.expires = d;
    }
    if(exp && exp.toUTCString) { props.expires = exp.toUTCString(); }

    value = encodeURIComponent(value);
    var updatedCookie = name + "=" + value;
    for(var propName in props){
        updatedCookie += "; " + propName;
        var propValue = props[propName];
        if(propValue !== true){ updatedCookie += "=" + propValue; }
    }
    document.cookie = updatedCookie;
}

function validateEmail(email) {
    var re = /^(([^<>()[\]\\.,;:\s@\"]+(\.[^<>()[\]\\.,;:\s@\"]+)*)|(\".+\"))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/;
    return re.test(email);
}
