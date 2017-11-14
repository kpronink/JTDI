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
            Alert(result.msg);
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
            else if (result["status"] === "Started"){$("#form_start_stop").append("<button class='btn-floating btn-large red' id='btn_start_stop' onclick='StartStop()'><i class='material-icons' style='size: 50px'>pause_circle_filled</i> </button>");}else if (result["status"] === "Stoped"){$("#form_start_stop").append("<button class='btn-floating btn-large red' id='btn_start_stop' onclick='StartStop()'> <i class='material-icons' style='size: 50px'>play_circle_filled</i> </button>");}
        },
        error: function(result) {
            alert('error');
        }
    });
}

$("#modal-task").on("submit", ".task-create-form", function () {
    var form = $(this);
    var form_data = form.serialize();
    form_data = form_data + '&param='+ $("#views").attr("views")
    $.ajax({
      url: form.attr("action"),
      data: form_data,
      type: form.attr("method"),
      dataType: 'json',
      success: function (data) {
        if (data.form_is_valid) {
          //alert("Task created!");  // <-- This is just a placeholder for now for testing
            $("#task_active_table").html(data.html_active_tasks_list);
            $('#dataTables-example').dataTable();
            $("[data-dismiss=modal]").trigger({ type: "click" });
            Alert('Задача успешно обновлена');
        }
        else {
          $("#modal-task .modal-content").html(data.html_form);
        }
      }
    });
    return false;
  });


function UpdateTask(url) {
    
    PreloadModal();
    $.ajax({
      url: url,
      type: 'get',
      dataType: 'json',
      data: {'param':$("#views").attr("views"), 'project':$("#project").attr("project")},
      success: function (data) {
          $("#modal-task .modal-content").html(data.html_form);
          if($('*').is('#id_project_field')) {
              ProjectSelect($("#id_project_field")[0].value);
          }
      }
    });
  }


function TaskDetail(task_url) {
    if (task_url !==''){
    if ($("#modal-task").is(':visible')) {}
    else{PreloadModal();
    }
    $.ajax({
      url: task_url,
      type: 'post',
      dataType: 'json',
      data: {'param':$("#views").attr("views")},
      success: function (data) {
        $("#modal-task .modal-content").html(data.html_form);
        get_comments();
      }
    });
}}

function UniversalFun(task_url) {
    if (task_url !==''){
    if ($("#modal-task").is(':visible')) {}
    else{PreloadModal();
    }

    $.ajax({
        url: task_url,
        type: 'post',
        dataType: 'json',
        data: {'param':$("#views").attr("views")},
        success: function(result) {
            //$("[data-dismiss=modal]").trigger({ type: "click" });
            if (result.project_param !== '') {
                $("#modal-task .modal-content").html(result.project_param);
            }
            if (result.html_active_tasks_list !== '') {
                $("#task_active_table").html(result.html_active_tasks_list);
            }
            if (result.html_finished_tasks_list !== ''){
                $("#task_finish_table").html(result.html_finished_tasks_list);
            }
            if (result.html_form !== '') {
                $("#modal-task .modal-content").html(result.html_form);
                get_comments();
            }
            $('#dataTables-example').dataTable();
            
            Alert(result.msg);
        }
    });}
}

$("#modal-task").on("submit", ".user_inv_form_in_proj", function () {
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

$("#modal-task").on("submit", ".rename_proj_form", function () {
    var form = $(this);
    $.ajax({
      url: form.attr("action"),
      data: form.serialize(),
      type: form.attr("method"),
      dataType: 'json',
      success: function (data) {
        if (data.form_is_valid) {
            $("#project_title").html("<h1 class='page-header'>Задачи проекта " + data.title + "</h1>");
            $("#project_button_param").html("Параметры проекта " + data.title);
            if (data.project_list !== '') {
                $("#projects_list").html(data.project_list);
            }
        }
        else {
        }
      }
    });
    return false;
  });

$("#project_create").on("submit", ".project_create_form", function () {
    var form = $(this);
    $.ajax({
      url: form.attr("action"),
      data: form.serialize(),
      type: form.attr("method"),
      dataType: 'json',
      success: function (data) {
        if (data.form_is_valid) {
            if (data.project_list !== '') {
                $("#projects_list").html(data.project_list);
            }
        }
        else {
        }
      }
    });
    return false;
  });

$(document).ready(function(){
    var task_id = Number(window.location.hash.replace("#",""));
    if (isFinite(task_id) && task_id !== 0) {
    TaskDetail("/task/det/"+String(task_id)+"/", 'today')
    $('#modal-task').modal('show')
    }
    GetNotifications();
    GetPushNotifications();
    setInterval(GetNotifications, 50000);
    setInterval(GetPushNotifications, 50000);
});

function Alert(msg) {
    if (msg !== "") {
            Materialize.toast(msg, 3000, 'rounded')
        } else {
            Materialize.toast(msg, 3000, 'rounded')
        }

}

function PreloadModal() {
    $("#modal-task .modal-content").html("<div class='cssload-thecube'> <div class='cssload-cube cssload-c1'></div> <div class='cssload-cube cssload-c2'></div> <div class='cssload-cube cssload-c'></div><div class='cssload-cube cssload-c3'></div> </div>");
}

function GetNotifications() {
    $.ajax({
      url: '/ajax/get_notifycation/',
      data: {},
      type: 'get',
      dataType: 'json',
      success: function (data) {

        var tasks_today_notify = Number(data.tasks_today_notify);
        if (isFinite(tasks_today_notify) && tasks_today_notify !== 0) {
            $('#tasks_today_notify').html(data.tasks_today_notify)
            $('.tab_counter_today')[0].style.display = "block";
            }
        var tasks_overdue_notify = Number(data.tasks_overdue_notify);
        if (isFinite(tasks_overdue_notify) && tasks_overdue_notify !== 0) {
            $('#tasks_overdue_notify').html(data.tasks_overdue_notify)
            $('.tab_counter_overdue')[0].style.display = "block";
            }
        if (data.notify_tasks !== '') {
            $('#dropdown2').prepend(data.notify_tasks)
            }
        var count_notify = Number(data.count_notify);
        var count_notify_now = Number($("#all_notify").text());
        count_notify = count_notify + count_notify_now;
        if (isFinite(count_notify) && count_notify !== 0) {
            $('#all_notify').html(count_notify);
            $('.tab_counter_top')[0].style.display = "block";
            }
      }
    });
    
}

function GetPushNotifications() {
    $.ajax({
      url: '/ajax/get_push_notifycation/',
      data: {},
      type: 'get',
      dataType: 'json',
      success: function (data) {
          for (var item in data){
            notifyMe(data[item].body, data[item].title, data[item].url)
          }
      }
    });
}

// request permission on page loadd
document.addEventListener('DOMContentLoaded', function () {
  if (!Notification) {
    alert('Desktop notifications not available in your browser. Try Chromium.'); 
    return;
  }

  if (Notification.permission !== "granted")
    Notification.requestPermission();
});

function notifyMe(notify_body, notify_title, notify_url) {
  if (Notification.permission !== "granted")
    Notification.requestPermission();
  else {
    var notification = new Notification(notify_title, {
      icon: '/static/img/logo_push.png',
      body: notify_body
    });

    notification.onclick = function () {
      TaskDetail(notify_url);
      $('#modal-task').modal('show')
      notification.close()
    };

  }

}