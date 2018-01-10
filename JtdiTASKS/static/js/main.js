$(function () {

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
        beforeSend: function (xhr, settings) {
            if (!csrfSafeMethod(settings.type) && sameOrigin(settings.url)) {
                // Send the token to same-origin, relative URLs only.
                // Send the token only if the method warrants CSRF protection
                // Using the CSRFToken value acquired earlier
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });

});

// AJAX for posting comment
function create_post() {
    get_comments();
    $.ajax({
        url: $("#url_ajax_add_comment").attr('url_ajax_add_comment'), // the endpoint
        type: "POST", // http method
        data: {the_post: $('#id_addComment').val()}, // data sent with the post request

        // handle a successful response
        success: function (result) {
            $('#id_addComment').val(''); // remove the value from the input
            $('#comments').append(result.comments)
            // $("#comments").append("<div class='media' id='comment'><p class='pull-right'><small>" + result.created + "</small></p><a class='media-left' href='#'>" +
            //     "<img src=" + result.avatar + " class='circle' width='40' height='40' border='20'></a><div class='media-body'>" +
            //     "<h4 class='media-heading user_name'>" + result.author + "</h4>" + result.text + "</div></div>");
        },

        // handle a non-successful response
        error: function (xhr, errmsg, err) {
            $('#results').html("<div class='alert-box alert radius' data-alert>Oops! We have encountered an error: " + errmsg +
                "<a href='#' class='close'>&times;</a></div>"); // add the error to the dom
            console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
        }
    });

    return false
}


function get_comments() {
    if ($('*').is('#comments')) {
        $.ajax({
            url: $("#url_ajax_get_comments").attr('url_ajax_get_comments'), // the endpoint
            type: "POST", // http method
            data: {the_post: $('#id_addComment').val()}, // data sent with the post request

            // handle a successful response
            success: function (result) {
                $('#comments').empty();
                $('#comments').prepend(result.comments)
                // for (var item in result) {
                //     $("#comments").append("<div class='media' id='comment'><p class='pull-right'><small>" + result[item].created + "</small></p><a class='media-left' href='#'>" +
                //         "<img src=" + result[item].avatar + " class='circle' width='40' height='40' border='20'></a><div class='media-body'>" +
                //         "<h4 class='media-heading user_name'>" + result[item].author + "</h4>" + result[item].text + "</div></div>");
                // } // another sanity check
            }

        });
    }
}

function remove(id) {
    return (elem = document.getElementById(id)).parentNode.removeChild(elem);
}

function StartStop() {
    $.ajax({
        type: "GET",
        url: $("#url_ajax_start").attr('url_ajax_start'),
        data: {},
        success: function (result) {
            Alert(result.msg);
            $("#form_start_stop").empty();
            $("#task_status").empty();
            $("#task_full_time").empty();
            var status = result["status"]
            var full_time = result["full_time"]
            $("#task_status").append("<label>Состояние задачи: </label>" + status + "</div>");
            $("#task_full_time").append("<label>Общее время работы над задачей: </label>" + full_time + "</div>");
            if (result["status"] === "Wait") {
                $("#form_start_stop").append("<button class='btn-floating btn-large red' id='btn_start_stop' onclick='StartStop()'> <i class='material-icons' style='size: 50px'>play_circle_filled</i> </button>");
            }
            else if (result["status"] === "Started") {
                $("#form_start_stop").append("<button class='btn-floating btn-large red' id='btn_start_stop' onclick='StartStop()'><i class='material-icons' style='size: 50px'>pause_circle_filled</i> </button>");
            } else if (result["status"] === "Stoped") {
                $("#form_start_stop").append("<button class='btn-floating btn-large red' id='btn_start_stop' onclick='StartStop()'> <i class='material-icons' style='size: 50px'>play_circle_filled</i> </button>");
            }
        },
        error: function (result) {
            alert('error');
        }
    });
}

$(".modal").on("submit", "#task_create_form", function () {
    var form = $(this);
    var form_data = form.serialize();
    form_data = form_data + '&param=' + $("#views").attr("views") + '&project_param=' + $("#project").attr("project")
    $.ajax({
        url: form.attr("action"),
        data: form_data,
        type: form.attr("method"),
        dataType: 'json',
        success: function (result) {
            if (result.form_is_valid) {
                $("#TaskActive").html(result.html_active_tasks_list);
                $('#TasksTables').dataTable({pageLength: result.count_visible_tasks});
                // $('.card-content').html(result.kanban);
                CloseModal()
                Alert('Задача успешно обновлена');
            }
            else {
                $("#modal_content").html(result.html_form);
            }
        }
    });
    return false;
});

$(".modal").on("submit", "#note_create_form", function () {
    var form = $(this);
    var form_data = form.serialize();

    $.ajax({
        url: form.attr("action"),
        data: form_data,
        type: form.attr("method"),
        dataType: 'json',
        success: function (result) {
            if (result.form_is_valid) {
                $("#NotesTables").html(result.html_active_notes_list);
                $('#TasksTables').dataTable();
                // $('.card-content').html(result.kanban);
                CloseModal()
                Alert('Заметка успешно обновлена');
            }
            else {
                $("#modal_content").html(result.html_form);
            }
        }
    });
    return false;
});


function UpdateTask(url) {
    LoaderActive();
    $.ajax({
        url: url,
        type: 'get',
        dataType: 'json',
        data: {'param': $("#views").attr("views"), 'project_param': $("#project").attr("project")},
        success: function (result) {
            if (result.html_form !== undefined) {
                $("#modal_content").html(result.html_form);
                if ($('*').is('#id_project_field')) {
                    ProjectSelect($("#id_project_field")[0].value);
                }
                OpenModal();
            }
            else {
                Alert(result.msg)
            }
            LoaderDeactive();
        }
    });
}

function UpdateNote(url) {
    LoaderActive();
    $.ajax({
        url: url,
        type: 'get',
        dataType: 'json',
        data: {},
        success: function (result) {
            $("#modal_content").html(result.html_form);
            OpenModal();
            LoaderDeactive();
        }

    });
}


function TaskDetail(task_url) {
    if (task_url !== '') {
        if ($("#modal-task").is(':visible')) {
        }
        else {
        }
        LoaderActive();
        $.ajax({
            url: task_url,
            type: 'post',
            dataType: 'json',
            data: {'param': $("#views").attr("views")},
            success: function (result) {
                $("#modal_content").html(result.html_form);
                get_comments();
                OpenModal();
                LoaderDeactive();
            }
        });
    }
}

function UniversalFun(task_url, close_modal) {
    if (task_url !== '') {
        if ($("#modal-task").is(':visible')) {
        }
        else {
        }
        LoaderActive();
        $.ajax({
            url: task_url,
            type: 'post',
            dataType: 'json',
            data: {'param': $("#views").attr("views")},
            success: function (result) {
                //$("[data-dismiss=modal]").trigger({ type: "click" });
                if (result.project_param !== '' && result.project_param !== undefined) {
                    // $("#modal-task .modal-content").html(result.project_param);
                    $("#modal_content").html(result.project_param);
                    OpenModal();
                }
                if (result.html_active_tasks_list !== '') {
                    $("#TaskActive").html(result.html_active_tasks_list);
                    drawChartGantt();
                }
                if (result.html_active_notes_list !== '') {
                    $("#NotesTables").html(result.html_active_notes_list);
                }
                if (result.html_finished_tasks_list !== '') {
                    $("#TasksFinished").html(result.html_finished_tasks_list);
                    drawChartGantt();
                }
                if (result.html_form !== '') {
                    $("#modal-task .modal-content").html(result.html_form);
                    get_comments();
                }
                $('#TasksTables').dataTable();
                $('#TasksTablesFinished').dataTable();
                if (close_modal !== undefined) {
                    CloseModal();
                }

                Alert(result.msg);
                LoaderDeactive();
            }
        });
    }
}

$(".modal").on("submit", "#user_inv_form_in_proj", function () {
    var form = $(this);
    $.ajax({
        url: form.attr("action"),
        data: form.serialize(),
        type: form.attr("method"),
        dataType: 'json',
        success: function (result) {
            if (result.form_is_valid) {
                $("#user_collection").append(result.html_new_user);
            }
            else {
                alert("Пользователь уже состоит в проекте");
            }
        }
    });
    return false;
});

$(".modal").on("submit", "#rename_proj_form", function () {
    var form = $(this);
    $.ajax({
        url: form.attr("action"),
        data: form.serialize(),
        type: form.attr("method"),
        dataType: 'json',
        success: function (result) {
            if (result.form_is_valid) {
                if (result.project_list !== '') {
                    $("#projects_list").html(result.project_list);
                    $('.ui.accordion').accordion({exclusive: false});
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
        success: function (result) {
            if (result.form_is_valid) {
                if (result.project_list !== '') {
                    $("#projects_list").html(result.project_list);
                }
            }
            else {
            }
        }
    });
    return false;
});


$(document).ready(function () {
    var task_id = Number(window.location.hash.replace("#", ""));
    if (isFinite(task_id) && task_id !== 0) {
        TaskDetail("/task/det/" + String(task_id) + "/", 'today')

    }
    GetNotifications();
    GetPushNotifications();
    setInterval(GetNotifications, 10000);
    setInterval(GetPushNotifications, 10000);
    $('.ui.dropdown').dropdown();
    $('.ui.accordion').accordion({exclusive: false});
    $('.menu .item').tab();

    google.charts.load("current", {packages: ["gantt", "table"]});
});

function Alert(msg) {
    if (msg !== "" && msg !== undefined) {
        $.uiAlert({
            textHead: '',
            text: msg,
            bgcolor: '#252525',
            textcolor: '#fff',
            position: 'top-right', // top And bottom ||  left / center / right
            icon: 'checkmark box',
            time: 3
        });
    } else {
        // Materialize.toast(msg, 3000, 'rounded')
    }

}


function GetNotifications() {
    $.ajax({
        url: '/get_notify/',
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

function getStory(project) {
    LoaderActive();
    $.ajax({
        url: '/ajax/get_story/' + String(project) + '/',
        data: {},
        type: 'get',
        dataType: 'json',
        success: function (result) {
            if (result.story !== '') {
                $('#StoryLine').html(result.story)
            }
            LoaderDeactive();
        }
    });

}

function GetNotificationsList(elem) {
    elem.addClass('loading');
    $.ajax({
        url: '/get_notify_event/',
        data: {},
        type: 'get',
        dataType: 'json',
        success: function (result) {
            if (result.notify_tasks !== '') {
                $('#notify_list').html(result.notify_tasks)
                $('#all_notify').html(0);
                $('.tab_counter_top')[0].style.display = "none";
                elem.removeClass('loading')
            }
        }
    });

}

function GetPushNotifications() {
    $.ajax({
        url: '/get_push_notify/',
        data: {},
        type: 'get',
        dataType: 'json',
        success: function (result) {
            for (var item in result) {
                notifyMe(result[item].body, result[item].title, result[item].url)
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
            OpenUrl(notify_url);
            notification.close()
        }
    }

}

function OpenUrl(any_url) {
    LoaderActive();
    if (any_url.indexOf('invite') + 1) {
        document.location.href = any_url;
    }
    else {
        TaskDetail(any_url);
        OpenModal();
    }
    LoaderDeactive();
}

function ProjectSelect(val) {
    $("#id_performer")[0].style.display = (val == '') ? 'none' : ''
    $.ajax({
        type: "GET",
        url: "/ajax/get_performers/" + val + "/",
        data: {},
        success: function (result) {
            $("#id_performer").empty();
            for (var item in result) {
                var option = document.createElement("option");
                option.text = result[item][1];
                option.value = result[item][0];
                var select = document.getElementById("id_performer");
                select.appendChild(option);
            }
        }
    });
}


function GetKanban(update) {
    $('.loader').addClass('active');
    if ($("#kanban_switch").prop("checked")) {
        $.ajax({
            type: "GET",
            url: "/ajax/kanban/" + $("#project").attr("project") + "/",
            data: {},
            success: function (result) {
                if (update === undefined) {
                    InstallFilter('kanban', true);
                }
                $('#TaskActive').html(result.kanban);
                $('.loader').removeClass('active');
                $('.loader').addClass('disable');
            }
        });
    }
    else {
        $.ajax({
            type: "GET",
            url: "/ajax/project_task_list/" + $("#project").attr("project") + "/",
            data: {},
            success: function (result) {
                if (update === undefined) {
                    InstallFilter('kanban', false);
                }
                $('#TaskActive').html(result.project);
                $('.loader').removeClass('active');
                $('.loader').addClass('disable');
            }
        });
    }
}

function AddNewColumn() {
    LoaderActive();
    $.ajax({
        type: "GET",
        url: "/ajax/add_kanban_column/" + $("#project").attr("project") + "/",
        data: {},
        dataType: 'json',
        success: function (result) {
            if (result.kanban_column_form !== '') {
                $("#modal_content").html(result.kanban_column_form);
                OpenModal();
                Alert(result.msg)
                LoaderDeactive();
            }
        }
    });
}

function HideColumn(id_elem) {
    $.ajax({
        type: "GET",
        url: "/ajax/hide_vis_kanban_column/" + String(id_elem),
        data: {},
        success: function (result) {
            var visible = result.visible;
            var kanban_column = $('#' + String(id_elem) + ', .ol.kanban');
            var icon = $('#hide_icon' + String(id_elem));
            if (!visible) {
                kanban_column[0].style.width = '27px';
                kanban_column[0].style.minWidth = '27px';
                kanban_column[0].style.maxWidth = '27px';
                icon.removeClass('hide');
                icon.addClass('unhide');
                if (kanban_column[0].lastElementChild.className === 'dd-list') {
                    kanban_column[0].lastElementChild.style.display = 'none';
                }
                kanban_column[0].firstElementChild.firstElementChild.style.display = 'none';
            }
            else {
                kanban_column[0].style.width = '100%';
                kanban_column[0].style.minWidth = '220px';
                kanban_column[0].style.maxWidth = '220px';
                icon.removeClass('unhide');
                icon.addClass('hide');
                if (kanban_column[0].lastElementChild.className === 'dd-list') {
                    kanban_column[0].lastElementChild.style.display = 'block';
                }
                kanban_column[0].firstElementChild.firstElementChild.style.display = 'flex';
            }
        }
    })

}

$(".modal").on("submit", "#add_kanban_column_form", function () {
    var form = $(this);
    $.ajax({
        url: form.attr("action"),
        data: form.serialize(),
        type: form.attr("method"),
        dataType: 'json',
        success: function (data) {
            if (data.form_is_valid) {
                if (data.new_column !== '') {
                    $('.dd').append(data.new_column);
                    CloseModal();
                    Alert(data.msg);
                }
            }
            else {
            }
        }
    });
    return false;
});

function AddNewKanbanTask() {
    $.ajax({
        type: "GET",
        url: "/ajax/add_kanban_task/",
        data: {},
        success: function (result) {
            $('.kanban To-do').append(result.new_task)
        }
    });
}

function ChangeKanbanStatus(task_pk, status_kanban_pk) {
    $.ajax({
        type: "POST",
        url: "/ajax/change_kanban_status/",
        data: {'task_pk': task_pk, 'status_kanban_pk': status_kanban_pk},
        success: function (result) {
            Alert(result.msg)
        }
    });
}

function InstallFilter(filter, value) {
    $.ajax({
        type: "POST",
        dataType: 'json',
        url: "/ajax/install_filter/" + $("#project").attr("project") + "/",
        data: {'filter': filter, 'value': value},
        success: function (result) {
            GetKanban(true)
        }
    });
}

function ChangeRules(filter, value) {
    $.ajax({
        type: "POST",
        dataType: 'json',
        url: "/ajax/set_access/" + $("#project").attr("project") + "/",
        data: {'filter': filter, 'value': value},
        success: function (result) {
        }
    });
}

function OpenSidebarLeft() {
    $('#sidebar_left').sidebar('toggle');
}

function OpenSidebarRight() {
    $('#sidebar_right').sidebar('toggle');
}

function OpenModal() {
    $('.ui.modal').modal({
        observeChanges: true,
        onHide: function () {
            $("#modal_content").html("");
        }
    })
        .modal('show');
}

function LoaderActive() {
    $('#loader').addClass('active')
}

function LoaderDeactive() {
    $('#loader').removeClass('active')
}

function CloseModal() {
    $('.ui.modal')
        .modal('hide')
    ;

}

function switchStoryTab() {
    $.tab('change tab', 'StoryLine');
}