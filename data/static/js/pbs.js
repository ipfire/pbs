
$(document).ready(
	function() {
		$('.dropdown-toggle').dropdown();
	}
);

function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

jQuery.postJSON = function(url, args, callback) {
    args._xsrf = getCookie("_xsrf");
    $.ajax({url: url, data: $.param(args), dataType: "text", type: "POST",
        success: function(response) {
        callback(eval("(" + response + ")"));
    }});
};

$(function() {
	var $search = $('#search');
	original_val = $search.val();

	$search.focus(function() {
		if($(this).val() === original_val) {
			$(this).val('');
		}
	})

	.blur(function() {
		if($(this).val() === '') {
			$(this).val(original_val);
		}
	});
});

action_run = function(action_id) {
	$.postJSON("/api/action/run", { "id" : action_id }, function() {});

	$("#action-" + action_id).hide();
}

action_remove = function(action_id) {
	$.postJSON("/api/action/remove", { "id" : action_id }, function() {});

	$("#action-" + action_id).hide();
}
