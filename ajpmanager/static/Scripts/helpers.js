
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
