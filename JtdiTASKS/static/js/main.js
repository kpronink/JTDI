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
// $('#commentForm').on('submit', function(event){
//     event.preventDefault();
//     console.log("form submitted!")  // sanity check
//     create_post();
// });

// AJAX for posting comment
function create_post() {
    //console.log("create post is working!") // sanity check
    get_comments()
    $.ajax({
        url : $("#url_ajax_add_comment").attr('url_ajax_add_comment'), // the endpoint
        type : "POST", // http method
        data : { the_post : $('#id_addComment').val()}, // data sent with the post request

        // handle a successful response
        success : function(json) {
            $('#id_addComment').val(''); // remove the value from the input
            //console.log(json); // log the returned json to the console
            $("#comments").append("<div class='media' id='comment'><p class='pull-right'><small>"+json.created+"</small></p><a class='media-left' href='#'>" +
                "<img src="+json.avatar+" class='circle-avatar' width='40' height='40' border='20'></a><div class='media-body'>" +
                "<h4 class='media-heading user_name'>"+json.author+"</h4>"+json.text+"</div></div>");
            //console.log("success"); // another sanity check
        },

        // handle a non-successful response
        error : function(xhr,errmsg,err) {
            $('#results').html("<div class='alert-box alert radius' data-alert>Oops! We have encountered an error: "+errmsg+
                " <a href='#' class='close'>&times;</a></div>"); // add the error to the dom
            console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
        }
    });

    return false
};


function get_comments() {
    if($('*').is('.comments-list')) {
    $.ajax({
        url : $("#url_ajax_get_comments").attr('url_ajax_get_comments'), // the endpoint
        type : "POST", // http method
        data : { the_post : $('#id_addComment').val()}, // data sent with the post request

        // handle a successful response
        success : function(json) {
            //console.log(json); // log the returned json to the console
            $('.comments-list').empty();
            for (var item in json){
            $("#comments").append("<div class='media' id='comment'><p class='pull-right'><small>"+json[ item ].created+"</small></p><a class='media-left' href='#'>" +
                "<img src="+json[ item ].avatar+" class='circle-avatar' width='40' height='40' border='20'></a><div class='media-body'>" +
                "<h4 class='media-heading user_name'>"+json[ item ].author+"</h4>"+json[ item ].text+"</div></div>");
            //console.log("success");
                } // another sanity check
        }

    });
}}

function remove(id)
            {
                return (elem=document.getElementById(id)).parentNode.removeChild(elem);
            }

function StartStop() {
    $.ajax({
        type: "GET",
        url: $("#url_ajax_start").attr('url_ajax_start'),
        data: {},
        success: function(result) {
            $("#form_start_stop").empty();
            $("#task_status").empty();
            $("#task_full_time").empty();
            var status = result["status"]
            var full_time = result["full_time"]
            $("#task_status").append("<label>Состояние задачи: </label>" + status + "</div>");
            $("#task_full_time").append("<label>Общее время работы над задачей: </label>" + full_time + "</div>");
            if(result["status"] === "Wait"){
                $("#form_start_stop").append("<button class='btn-floating btn-large red' id='btn_start_stop' onclick='StartStop()'> <i class='material-icons' style='size: 50px'>play_circle_filled</i> </button>");
            }
            else if (result["status"] === "Started"){$("#form_start_stop").append("<button class='btn-floating btn-large red' id='btn_start_stop' onclick='StartStop()'><i class='material-icons' style='size: 50px'>pause_circle_filled</i> </button>");}else if (result["status"] === "Stoped"){$("#form_start_stop").append("<button class='btn-floating btn-large red' id='btn_start_stop' onclick='StartStop()'> <i class='material-icons' style='size: 50px'>play_circle_filled</i> </button>");};;
        },
        error: function(result) {
            alert('error');
        }
    });
}

$("#modal-task").on("submit", ".task-create-form", function () {
    var form = $(this);
    $.ajax({
      url: form.attr("action"),
      data: form.serialize(),
      type: form.attr("method"),
      dataType: 'json',
      success: function (data) {
        if (data.form_is_valid) {
          //alert("Task created!");  // <-- This is just a placeholder for now for testing
            $("#task_active_table").html(data.html_active_tasks_list);
            $('#dataTables-example').dataTable();
            $("[data-dismiss=modal]").trigger({ type: "click" });
        }
        else {
          $("#modal-task .modal-content").html(data.html_form);
        }
      }
    });
    return false;
  });


function UpdateTask(url) {
      var btn = $(this);
      $("#modal-task .modal-content").html("<div class='cssload-thecube'> <div class='cssload-cube cssload-c1'></div> <div class='cssload-cube cssload-c2'></div> <div class='cssload-cube cssload-c'></div> <div class='cssload-cube cssload-c3'></div> </div>");
    $.ajax({
      url: url,
      type: 'get',
      dataType: 'json',
      success: function (data) {
          $("#modal-task .modal-content").html(data.html_form);
          if($('*').is('#id_project_field')) {
              ProjectSelect($("#id_project_field")[0].value);
          }
      }
    });
  }


function TaskDetail(task_url) {

    $.ajax({
      url: task_url,
      type: 'get',
      dataType: 'json',
      success: function (data) {
        $("#modal-task .modal-content").html(data.html_form);
        get_comments();
      }
    });
}

function UniversalFun(task_url, param) {
    $.ajax({
        type: "POST",
        url: task_url,
        data: {'param':param},
        dataType: 'json',
        success: function(result) {
            //$("[data-dismiss=modal]").trigger({ type: "click" });
            $("#task_active_table").html(result.html_active_tasks_list);
            if (result.html_finished_tasks_list !== ''){
                $("#task_finish_table").html(result.html_finished_tasks_list);
            }
            $('#dataTables-example').dataTable();
        }
    });
}

$("#invite_user_in_proj").on("submit", ".user_inv_form_in_proj", function () {
    var form = $(this);
    $.ajax({
      url: form.attr("action"),
      data: form.serialize(),
      type: form.attr("method"),
      dataType: 'json',
      success: function (data) {
        if (data.form_is_valid) {
          //alert("Task created!");  // <-- This is just a placeholder for now for testing
            //$("#task_active_table").html(data.html_active_tasks_list);
            //$('#dataTables-example').dataTable();
            $("#user_collection").append(data.html_new_user);
        }
        else {
          //$("#modal-task .modal-content").html(data.html_form);
            alert("Пользователь уже состоит в проекте");
        }
      }
    });
    return false;
  });

$("#rename_proj").on("submit", ".rename_proj_form", function () {
    var form = $(this);
    $.ajax({
      url: form.attr("action"),
      data: form.serialize(),
      type: form.attr("method"),
      dataType: 'json',
      success: function (data) {
        if (data.form_is_valid) {
          //alert("Task created!");  // <-- This is just a placeholder for now for testing
            //$("#task_active_table").html(data.html_active_tasks_list);
            //$('#dataTables-example').dataTable();
            $("#project_title").html("<h1 class='page-header'>Задачи проекта " + data.title + "</h1>");
        }
        else {
          //$("#modal-task .modal-content").html(data.html_form);
        }
      }
    });
    return false;
  });

$(document).ready(function(){
    var task_id = window.location.hash.replace("#","");
    if (task_id !== ''){
    TaskDetail("/task/det/"+task_id+"/")
    $('#modal-task').modal('show')
    }
});