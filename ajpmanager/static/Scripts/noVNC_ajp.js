/*jslint white: false */
/*global window, $, Util, RFB, */
"use strict";

var rfb;

function passwordRequired(rfb) {
    var msg;
    msg = '<form onsubmit="return setPassword();"';
    msg += '  style="margin-bottom: 0px">';
    msg += 'Password Required: ';
    msg += '<input type=password size=10 id="password_input" class="noVNC_status">';
    msg += '<\/form>';
    $D('noVNC_status_bar').setAttribute("class", "noVNC_status_warn");
    $D('noVNC_status').innerHTML = msg;
}
function setPassword() {
    rfb.sendPassword($D('password_input').value);
    return false;
}
function sendCtrlAltDel() {
    rfb.sendCtrlAltDel();
    return false;
}
function updateState(rfb, state, oldstate, msg) {
    var s, sb, cad, level;
    s = $D('noVNC_status');
    sb = $D('noVNC_status_bar');
    cad = $D('sendCtrlAltDelButton');
    switch (state) {
        case 'failed':       level = "error";  break;
        case 'fatal':        level = "error";  break;
        case 'normal':       level = "normal"; break;
        case 'disconnected': level = "normal"; break;
        case 'loaded':       level = "normal"; break;
        default:             level = "warn";   break;
    }

    if (state === "normal") { cad.disabled = false; }
    else                    { cad.disabled = true; }

    if (typeof(msg) !== 'undefined') {
        sb.setAttribute("class", "noVNC_status_" + level);
        s.innerHTML = msg;
    }
}

function noVNC_connect (machine_name) {

    /*
    Step 1: Ask server to create new TCP-server for `machine_name`
     */

    //var host = '127.0.0.1';
    //var port = '6080';
    var password = '';
    var token;
    var path;

    $.ajax({
        type: "POST",
        url: "/engine.ajax",
        data: JSON.stringify({'query': 'create_vnc_connection', 'machine': machine_name}),
        contentType: 'application/json; charset=utf-8'
    }).done(function ( data ) {
            if (data.status) {

                console.log(data);

                setCookie('ajpvnc_key', data.data.cookie);

                var host = data.data.host;
                var port = data.data.port;

//              var host, port, password, path, token;

                $D('sendCtrlAltDelButton').style.display = "inline";
                $D('sendCtrlAltDelButton').onclick = sendCtrlAltDel;

                //document.title = unescape(WebUtil.getQueryVar('title', 'noVNC'));
                // By default, use the host and port of server that served this file
                //host = WebUtil.getQueryVar('host', window.location.hostname);
                //port = WebUtil.getQueryVar('port', window.location.port);

                // If a token variable is passed in, set the parameter in a cookie.
                // This is used by nova-novncproxy.
                token = WebUtil.getQueryVar('token', null);
                if (token) {
                    WebUtil.createCookie('token', token, 1)
                }

                //password = WebUtil.getQueryVar('password', '');
                path = WebUtil.getQueryVar('path', 'websockify');

                if ((!host) || (!port)) {
                    updateState('failed',
                        "Must specify host and port in URL");
                    return;
                }


                rfb = new RFB({'target':       $D('noVNC_canvas'),
                    'encrypt':      WebUtil.getQueryVar('encrypt',
                        (window.location.protocol === "https:")),
                    'repeaterID':   WebUtil.getQueryVar('repeaterID', ''),
                    'true_color':   WebUtil.getQueryVar('true_color', true),
                    'local_cursor': WebUtil.getQueryVar('cursor', true),
                    'shared':       WebUtil.getQueryVar('shared', true),
                    'view_only':    WebUtil.getQueryVar('view_only', false),
                    'updateState':  updateState,
                    'onPasswordRequired':  passwordRequired});
                rfb.connect(host, port, password, path);

            }
            else {
                jgrowl_error(1, 'Error message from the server during attempt to create new VNC connection: <br>' + data.data);
            }
        });

    return true;

}


function noVNC_release (machine_name) {
    //console.log(rfb);

    rfb.disconnect();

    $.ajax({
        type: "POST",
        url: "/engine.ajax",
        data: JSON.stringify({'query': 'release_vnc_connection'}), // Rest data will be taken from cookies
        contentType: 'application/json; charset=utf-8'
    }).done(function ( data ) {
        if (data.status){
            $current_vnc = '';
            show_default_screen(false);
        }
        else {
            ;
        }
    });
}