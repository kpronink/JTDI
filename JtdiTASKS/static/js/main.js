$(function() {


    // This function gets cookie with a given name
    function getCookie(name) {
        var cookieValue = null;
        if (document.cookie && document.cookie != '') {
            var cookies = document.cookie.split(';');
            for (var i = 0; i < cookies.length; i++) {
                var cookie = jQuery.trim(cookies[i]);
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) == (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    var csrftoken = getCookie('csrftoken');

    /*
    The functions below will create a header with csrftoken
    */

    function csrfSafeMethod(method) {
        // these HTTP methods do not require CSRF protection
        return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
    }
    function sameOrigin(url) {
        // test that a given url is a same-origin URL
        // url could be relative or scheme relative or absolute
        var host = document.location.host; // host + port
        var protocol = document.location.protocol;
        var sr_origin = '//' + host;
        var origin = protocol + sr_origin;
        // Allow absolute or scheme relative URLs to same origin
        return (url == origin || url.slice(0, origin.length + 1) == origin + '/') ||
            (url == sr_origin || url.slice(0, sr_origin.length + 1) == sr_origin + '/') ||
            // or any other URL that isn't scheme relative or absolute i.e relative.
            !(/^(\/\/|http:|https:).*/.test(url));
    }

    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!csrfSafeMethod(settings.type) && sameOrigin(settings.url)) {
                // Send the token to same-origin, relative URLs only.
                // Send the token only if the method warrants CSRF protection
                // Using the CSRFToken value acquired earlier
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });

});

// Submit post on submit
$('#commentForm').on('submit', function(event){
    event.preventDefault();
    console.log("form submitted!")  // sanity check
    create_post();
});

// AJAX for posting
function create_post() {
    console.log("create post is working!") // sanity check
    $.ajax({
        url : $("#url_ajax_add_comment").attr('url_ajax_add_comment'), // the endpoint
        type : "POST", // http method
        data : { the_post : $('#id_addComment').val()}, // data sent with the post request

        // handle a successful response
        success : function(json) {
            $('#id_addComment').val(''); // remove the value from the input
            console.log(json); // log the returned json to the console
            $("#comments").append("<div class='media' id='comment'><p class='pull-right'><small>"+json.created+"</small></p><a class='media-left' href='#'>" +
                "<img src="+json.avatar+" class='circle-avatar' width='40' height='40' border='20'></a><div class='media-body'>" +
                "<h4 class='media-heading user_name'>"+json.author+"</h4>"+json.text+"</div></div>");
            console.log("success"); // another sanity check
        },

        // handle a non-successful response
        error : function(xhr,errmsg,err) {
            $('#results').html("<div class='alert-box alert radius' data-alert>Oops! We have encountered an error: "+errmsg+
                " <a href='#' class='close'>&times;</a></div>"); // add the error to the dom
            console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
        }
    });
};


$(document).ready(setInterval(function get_comments() {
    $.ajax({
        url : $("#url_ajax_get_comments").attr('url_ajax_get_comments'), // the endpoint
        type : "POST", // http method
        data : { the_post : $('#id_addComment').val()}, // data sent with the post request

        // handle a successful response
        success : function(json) {
            console.log(json); // log the returned json to the console
            $('.comments-list').empty();
            for (var item in json){
            $("#comments").append("<div class='media' id='comment'><p class='pull-right'><small>"+json[ item ].created+"</small></p><a class='media-left' href='#'>" +
                "<img src="+json[ item ].avatar+" class='circle-avatar' width='40' height='40' border='20'></a><div class='media-body'>" +
                "<h4 class='media-heading user_name'>"+json[ item ].author+"</h4>"+json[ item ].text+"</div></div>");
            console.log("success");} // another sanity check
        }

    });
}, 5000))

function remove(id)
            {
                return (elem=document.getElementById(id)).parentNode.removeChild(elem);
            }