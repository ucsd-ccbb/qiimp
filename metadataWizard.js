// These global variables are filled using info from the back-end at load time
var g_reserved_word_url = "";
var g_reserved_words = [];
var TEMPLATE_SUFFIX = "";
var SEPARATOR = "";
var SpecialInputs = {};
var fields_to_show_by_field_type = {};
var field_name_regex = null;
var text_type_value = null;
var no_default_radio_value = null;
var max_selectbox_size = null;
var existing_field_names = {};
var next_field_num = 0;
var package_fields = {};


// Dynamically generate HTML specifying input elements for a new field
function generateFieldHtml(fieldName) {
    var field_index = next_field_num;
    var $html = $('.fieldTemplate').clone();
    var template_id_objects = $("[id$=" + TEMPLATE_SUFFIX + "]");

    for (var i = 0, len = template_id_objects.length; i < len; i++) {
        // change the element clone's template id to field-specific id
        var curr_object = template_id_objects[i];
        var curr_id_selector = getIdSelectorFromId(curr_object.id);
        var new_id = getNewIdentifierFromTemplateAndIndex(curr_object.id, field_index);
        var new_id_selector = getIdSelectorFromId(new_id);
        $html.find(curr_id_selector).prop('id', new_id);
        var new_object_html_element = $html.find(new_id_selector)[0];

        // if the element has a name attribute, change its element clone's name to a field-specific one
        // see https://stackoverflow.com/a/1318091
        var name_attr = $(curr_object).attr('name');
        // For some browsers, `attr` is undefined; for others,
        // `attr` is false.  Check for both.
        if (typeof name_attr !== typeof undefined && name_attr !== false) {
            var new_name = getNewIdentifierFromTemplateAndIndex(curr_object.name, field_index);
            new_object_html_element.name = new_name;
        }

        // TODO: remove hard-coding of field name
        if (curr_object.id.startsWith("field_name")){
            // If current element is the field_name field, set its value to the input value
            new_object_html_element.value = fieldName;
        }
    }

    var return_val = $html.html();
    return return_val;
}

// Add events/validations to dynamically created input elements for new field
function decorateNewElements(newest_field_index) {
    for (var i = 0, len = NEW_ELEMENT_SET_UP_FUNCTIONS.length; i < len; i++) {
        NEW_ELEMENT_SET_UP_FUNCTIONS[i](newest_field_index);
    }
}

var allowed_date_formats = ["YYYY-MM-DD HH:mm:ss", "YYYY-MM-DD HH:mm", "YYYY-MM-DD HH", "YYYY-MM-DD", "YYYY-MM",
    "YYYY"];

// For JQuery validation plugin, custom validator functions always have
// first argument: the current value of the validated element. Second argument: the element to be validated
$.validator.addMethod("isValidDateTime", function(value, element){
    // From Austin re collection_timestamp: "The only formats allowed are:
    // yyyy-mm-dd hh:mm:ss or
    // yyyy-mm-dd hh:mm or
    // yyyy-mm-dd hh or
    // yyyy-mm-dd or
    // yyyy-mm or
    // yyyy"

    var return_val = false;  // default assumes validation failure
    for (i = 0; i < allowed_date_formats.length; i++) {
        var curr_format = allowed_date_formats[i];
        var curr_val = moment(value, curr_format, true).isValid();
        if (curr_val){
            return_val = curr_val;
            break;
        }
    }

    return this.optional(element) || return_val;
}, "DateTime must be a valid timestamp in one of these formats: " + allowed_date_formats.join(" or "));

// For JQuery validation plugin, custom validator functions always have
// first argument: the current value of the validated element. Second argument: the element to be validated
$.validator.addMethod("isValidFieldNamesList", function(value, element){
    var input_field_names = getValuesFromMultilineTextArea(value);

    var full_err_msgs = [];
    for (var i = 0; i < input_field_names.length; i++) {
        var curr_field_name = input_field_names[i];
        if (curr_field_name !== "") {
            var curr_err_msgs = validatePutativeFieldName(curr_field_name);
            if (curr_err_msgs.length > 0){
                // TODO: refactor hardcoding of ul/li generation and class setting
                full_err_msgs.push(curr_field_name + ":<ul class='error_list'><li class='error_item'>" + curr_err_msgs.join("</li><li class='error_item'>") + "</li></ul>");
            }
        }
    }

    var return_val = full_err_msgs.length <= 0;
    if (full_err_msgs.length > 0){
        full_err_msgs.unshift("Please address the following issues:")
    }
    $(element).data('error_msg', full_err_msgs.join("<br />"));

    return this.optional(element) || return_val;
}, function(params, element) {
  return $(element).data('error_msg');
});

var NEW_ELEMENT_SET_UP_FUNCTIONS = [
    function(field_index) {  // set onchange handler on field type and make required
        addAlwaysRequiredRule(field_index, SpecialInputs.FIELD_TYPE);
        addOnChangeEvent(field_index, SpecialInputs.FIELD_TYPE, resetFieldDetails);
    },
    function (field_index) { //set special onchange handler on allowed values checkboxes group
        var id_selector = getIdSelectorFromBaseNameAndFieldIndex(SpecialInputs.ALLOWED_MISSINGS, field_index);
        var id_and_state_selector = id_selector + " :checkbox"; //selector for all checkboxes inside group fieldset
        $(id_and_state_selector).on("change", {field_index:field_index}, updateDefaultsWithMissings);
    },
     function (field_index) { // set onchange handler for radio buttons specifying kind of default
         var name_selector = "input:radio[name='" + SpecialInputs.DEFAULT_OPTION + SEPARATOR + field_index + "']";
         $(name_selector).on("change", {field_index:field_index}, enableDisableDefaultSelectsOnDefaultChange);
    },
    function (field_index) { //make data_type required and set onchange handler to update type validation of default
        addAlwaysRequiredRule(field_index, SpecialInputs.DATA_TYPE);
        addOnChangeEvent(field_index, SpecialInputs.DATA_TYPE, updateTypeValidations);
    },
    function (field_index) { //make boolean true value required and set onchange handler to update defaults
        addAlwaysRequiredRule(field_index, SpecialInputs.TRUE_VALUE);
        addOnChangeEvent(field_index, SpecialInputs.TRUE_VALUE, updateDefaultsWithBooleanVals);
    },
    function (field_index) { //make boolean false value required and set onchange handler to update defaults
        addAlwaysRequiredRule(field_index, SpecialInputs.FALSE_VALUE);
        addOnChangeEvent(field_index, SpecialInputs.FALSE_VALUE, updateDefaultsWithBooleanVals);
    },
    function (field_index) { //make categorical values required and add onchange handler to update defaults
        addAlwaysRequiredRule(field_index, SpecialInputs.CATEGORY_VALS);
        addOnChangeEvent(field_index, SpecialInputs.CATEGORY_VALS, updateDefaultsWithCategories);
    },
    function (field_index){ //make minimum comparison required if minimum is filled in
         addConditionalRequiredRule(field_index, SpecialInputs.MINIMUM, SpecialInputs.MIN_COMPARE);
    },
    function (field_index){ //make minimum required if minimum comparison is filled in
         addConditionalRequiredRule(field_index, SpecialInputs.MIN_COMPARE, SpecialInputs.MINIMUM);
    },
    function (field_index){ //make maximum comparison required if maximum is filled in
         addConditionalRequiredRule(field_index, SpecialInputs.MAXIMUM, SpecialInputs.MAX_COMPARE);
    },
    function (field_index){ //make minimum required if minimum comparison is filled in
         addConditionalRequiredRule(field_index, SpecialInputs.MAX_COMPARE, SpecialInputs.MAXIMUM);
    },
    function (field_index) { //make datetime default pass datetime validation
        addDateTimeValidationRule(field_index, SpecialInputs.DEFAULT_DATETIME);
    },
    function (field_index){ //add onclick event handler to remove button for field
        addEventHandler("click", field_index, SpecialInputs.REMOVE_FIELD, removeField)
    }
];

// Code to run as soon code as the document is ready to be manipulated
$(document).ready(function () {
    $.ajax({
        method: "GET",
        url: g_reserved_word_url,
        async: false,
        data: "text",
        success: function(text) {
            var raw_reserved_words = jsyaml.load(text);
            for (var i = 0, len = raw_reserved_words.length; i < len; i++) {
                var curr_word = raw_reserved_words[i];
                if (curr_word === null) {
                    curr_word = "null";
                } else {
                    curr_word = curr_word.toString();
                }
                g_reserved_words.push(curr_word.toLowerCase())
            }
        }
    });

    // From https://www.tutorialrepublic.com/twitter-bootstrap-tutorial/bootstrap-accordion.php
    // Add minus icon for collapse element which is open by default
    $(".collapse.in").each(function(){
        $(this).siblings(".panel-heading").find(".glyphicon").addClass("glyphicon-minus").removeClass("glyphicon-plus");
    });
    // Toggle plus minus icon on show hide of collapse element
    $(".collapse").on('show.bs.collapse', function(){
        $(this).parent().find(".glyphicon").removeClass("glyphicon-plus").addClass("glyphicon-minus");
    }).on('hide.bs.collapse', function(){
        $(this).parent().find(".glyphicon").removeClass("glyphicon-minus").addClass("glyphicon-plus");
    });

    // From https://blueimp.github.io/jQuery-File-Upload/basic.html
    var url = "http://localhost:8898/upload";
    $('#fileupload').fileupload({
        url: url,
        dataType: 'json',
        done: function (e, data) {
            $.each(data.result.files, function (index, file) {
                $('<p/>').text(file.name).appendTo('#files');
            });

            // NB: I do NOT care (or require) that the fields go in with the same field indexes they did in the original
            // form that we are recreating.  The only thing I care about is that they go in in the same ORDER.
            addFields(data.result["fields"]);
        },
        progressall: function (e, data) {
            var progress = parseInt(data.loaded / data.total * 100, 10);
            $('#progress .progress-bar').css(
                'width',
                progress + '%'
            );
        }
    }).prop('disabled', !$.support.fileInput).parent().addClass($.support.fileInput ? undefined : 'disabled');

    var submitted = false;
    $("#metadata_form").validate({
        ignore: [],
        errorClass: "error_msg",
        rules: {
            "study_name": {
                required: true,
                pattern: /^[a-zA-Z0-9 ]*$/,
                minlength: 2,
                maxlength: 400
            },
            "field_names": {
                isValidFieldNamesList: true
            },
            "files[]": {
                extension: "xlsx"
            }
        },
        messages: {
            "study_name": {
                required: "This field is required.",
                pattern: "Only letters, numbers, and spaces are permitted.",
                maxlength: "This field must be 400 characters or fewer."
            },
            "files[]": {
                extension: "Only .xlsx files produced by the metadata wizard may be uploaded."
            }
        },
        onfocusout: function(element) {
           $(element).valid();
        },
        showErrors: function(errorMap, errorList) {
            if (submitted) {
                submitted = false;
                // TODO: refactor hard-coding of msg prefix, ul/li creation, class setting
                var summary = "Please correct the following issues:<br /><ul class='error_list'>";
                for (var curr_index in errorList){
                    // NB: ignore pycharm warning about hasOwnProperty() check per https://stackoverflow.com/a/25724382
                    var curr_item = errorList[curr_index];
                    var curr_id = curr_item.element.id;
                    var label_text = $("#label_" + curr_id).text();
                    var field_index = findFieldIndexFromNameOrId(curr_id);
                    if (field_index !== null){
                        var curr_field_name = getFieldNameValueByIndex(field_index);
                        label_text = curr_field_name + " " + label_text;
                    }
                    if (!label_text.endsWith(":")) {
                        label_text += ":";
                    }
                    var new_msg_pieces = ["<li class='error_item'>", label_text, curr_item.message, "</li>"];
                    summary += new_msg_pieces.join(" ")
                }

                summary += "</ul>";
                $("#error_summary_div").html(summary);
            }

            this.defaultShowErrors();
        },
        invalidHandler: function(form, validator) {
            submitted = true;
        }
    });
});
