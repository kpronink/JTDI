$(document).ready(function(){


  $(".submenu > a").click(function(e) {
    e.preventDefault();
    var $li = $(this).parent("li");
    var $ul = $(this).next("ul");

    if($li.hasClass("open")) {
      $ul.slideUp(350);
      $li.removeClass("open");
    } else {
      $(".nav > li > ul").slideUp(350);
      $(".nav > li").removeClass("open");
      $ul.slideDown(350);
      $li.addClass("open");
    }
  });
  
});


$("#id_username").change(function () {
    $.ajax({
        url: "/ajax/validate_username/",
        data: {'username': $("#id_username")[0].value},
        dataType: 'json',
        success: function (data) {
            if (data.is_taken != true) {
                alert(data.error_message);
            }
        }
    });
});



