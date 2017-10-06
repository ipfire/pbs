$(document).ready(function() {
	// Activate Google Prettify for pretty-printing code.
	window.prettyPrint && prettyPrint()

	// Activate tooltips.
	$("a[rel=tooltip]").tooltip();
	$("span[rel=tooltip]").tooltip();

	$(".typeahead-packages-autocomplete").typeahead({
		source: function(query, process) {
			$.get("/api/packages/autocomplete", { q: query }, function(data) {
				if (data.query == query) {
					process(data.packages);
				}
			});
		},
	});
});

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
