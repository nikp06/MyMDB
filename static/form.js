// this function replaces all commas in a list of directors with a new line, so that table in select is more clear
$(".wrap-directors:contains(', ')").each(function(){
  var directors = $(this).text();
  $(this).html(directors.replace(', ', ',<br />'));
});

// confirmation popup for clearing watchlist/movies + making background blurry
$( document ).ready( function() {
    $('.fa.fa-minus-circle, .clearer').click(function(e) {
        var idClicked = e.target.name;
        $('input[name="amount"]').val(idClicked);
        $("div#confirm.popup-overlay").center(),
        $( "#content" ).addClass( "blurry" );
        $("#confirm.popup-overlay, #confirm.popup-content").addClass("active");
    });
  return false;
});

// opens popup for rating a movie and hides movie_id which is the buttons id in h4#movie_id of the "form" in the popup
$( document ).ready( function() {
    $('button[name="ratepopup"]').click(function(e) {
        var idClicked = e.target.id;
        $("#movie_id").text(idClicked),
        $("div#popup.popup-overlay").center(),
        $( "#content" ).addClass( "blurry" );
        $("#popup.popup-overlay, #popup.popup-content").addClass("active");
    });
  return false;
});

// hand rating popup-input to application and return with update, also checking whether input is invalid (>10 or <1) and extracting rating, notes and (hidden) movie_id from "form" in h4 and input fields
$(function() {
$('a#rate').bind('click', function() {
    var rating = parseFloat($("#rating").val());
    if (($("#rating").val() > 10) || ($("#rating").val() < 1))
    {
        $("#rating").val('');
        alert('Rating must be between 1 and 10');
        return false;
    }
  $.getJSON($SCRIPT_ROOT + '/add_rate', {
    a: $("#movie_id").text(),
    b: rating,
    c: $("#notes").val(),
  }, function(data) {
      if (data.oldnotes !== 0)
      {
        $('button#'+data.oldnotes).attr("id",data.notes);
        $('td[name="'+data.movie_id+'"]').text(String(data.user_rating));
      }
    $("#rating").val(''),
    $("#notes").val(''),
    // $("#myId").attr("id", "mySecondId"),
    // $('#'+String(data.notes)).attr("id",String(data.notes)),
    $( "#content" ).removeClass( "blurry" ),
    $(".popup-overlay, .popup-content").removeClass("active"),
    $('button#'+data.movie_id).css("color", "white"),
    $('button#'+data.movie_id).css("color", "transparent"),
    $('button#'+data.movie_id).css("text-shadow", "0 0 0 white"),
    $("button#"+data.movie_id).html(String.fromCharCode(10004) + data.calculate);
    $('button#'+data.movie_id).attr("disabled", true);
    $('buttonwl#'+data.movie_id).attr("disabled", true);
    $('button#'+data.movie_id). unbind('click');
    $('button#wl'+data.movie_id). unbind('click');
  });
  return false;
});
});

// popup for seeing the notes of a movie: on button click (which id is notes of movie) notes are stored in text attribute of h4#notes -> popup overlay centered 
$( document ).ready( function() {
    $('button[name="notespopup"]').click(function(e) {
        var idClicked = e.target.id;
        $("h4#notes").text(idClicked),
        $("div#notespopup.popup-overlay").center(),
        $( "#content" ).addClass( "blurry" );
        $("#notespopup.popup-overlay, #notespopup.popup-content").addClass("active");
    });
  return false;
});

// definition of the closing function on startup of page load when site is redirected from popup button-press (otherwise remains blurry) AND when close button is pressed in overlay
$( document ).ready( function() {
    $( "#content" ).removeClass( "blurry" );
    $(".popup-overlay, .popup-content").removeClass("active");
    $(".close").on("click", function() {
        $( "#content" ).removeClass( "blurry" );
        $(".popup-overlay, .popup-content").removeClass("active");
    });
  return false;
});

// center function for centering the popup overlay
jQuery.fn.center = function () {
    this.css("position","absolute");
    this.css("top", Math.max(0, (($(window).height() - $(this).outerHeight()) / 2) + 
                                                $(window).scrollTop()) + "px");
    this.css("left", Math.max(0, (($(window).width() - $(this).outerWidth()) / 2) + 
                                                $(window).scrollLeft()) + "px");
    return this;
};

// function for adding movie into the watchlist on button press
$(function() {
$('button[name="addwl"]').click(function(e) {
    var movie_id = e.target.id;
    movie_id = movie_id.replace('wl','');
  $.getJSON($SCRIPT_ROOT + '/add_watchlist', {
      a: movie_id
}, function(data) {
    $('button#wl'+data.movie_id).css("color", "white"),
    $('button#wl'+data.movie_id).css("color", "transparent"),
    $('button#wl'+data.movie_id).css("text-shadow", "0 0 0 white"),
    $('button#wl'+data.movie_id).text(String.fromCharCode(10004) + data.calculate);
    // $('button#wl'+data.movie_id).unbind('click');
    $('button#wl'+data.movie_id).attr("disabled", true);
    $('button#'+data.movie_id).unbind('click');
  });
  return false;
});
});


// function for various sorting buttons in tables (copied from some internet source)
$('.sort').click(function(){
    var table = $(this).parents('table').eq(0);
    var rows = table.find('tr:gt(0)').toArray().sort(comparer($(this).index()));
    this.asc = !this.asc;
    if (!this.asc){rows = rows.reverse()}
    for (var i = 0; i < rows.length; i++){table.append(rows[i])}
});
function comparer(index) {
    return function(a, b) {
        var valA = getCellValue(a, index), valB = getCellValue(b, index);
        return $.isNumeric(valA) && $.isNumeric(valB) ? valA - valB : valA.toString().localeCompare(valB);
    };
}
function getCellValue(row, index){ return $(row).children('td').eq(index).text() }


// execution for shuffling on randomizer page where you can make same query again: hands method (in button id) and query (e.g. year, directorname, starname in base on column)
$(function() {
$('button[name="shuffle"]').click(function(e) {
    $.getJSON($SCRIPT_ROOT + '/shuffle', {
      method: e.target.id,
      query: $('#query').attr('name')
  }, function(data) {
      $('button[name="addwl"]').text("+ Watchlist");
    //   $('button[name="addwl"]').bind('click');
      $('button[name="addwl"]').attr("disabled", false);
      $('button[name="addwl"]').attr("id",'wl'+data.movie_id);
      $('th[name="a"]').text(data.movie_id);
      $('a[name="title"]').attr("href", data.link+data.movie_id+"/");
      $('a[name="title"]').text(data.title);
      $('th[name="rating"]').text(data.rating);
      $('th[name="year"]').text(data.year);
      if (data.name)
        {
      $('#query').text(data.name);}
    });
  return false;
});
});


// for little preview popupwindow when link is hovered over (IMDb)
$(".tiptext").mouseover(function() {
    $(this).children(".description").show();
}).mouseout(function() {
    $(this).children(".description").hide();
});