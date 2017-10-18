// These global variables are filled using info from the back-end at load time
var g_reserved_word_url = "";
var g_reserved_words = [];
var TEMPLATE_SUFFIX = "";
var SEPARATOR = "";
var SpecialInputs = {};
var fields_to_show_by_field_type = {};
var websocket_url = "";
var field_name_regex = null;


// Dynamically generate HTML specifying input elements for a new field
function generateFieldHtml() {
    var field_index = getCurrNumFields();
    var $html = $('.fieldTemplate').clone();
    var template_id_objects = $("[id$=" + TEMPLATE_SUFFIX + "]");

    for (var i = 0, len = template_id_objects.length; i < len; i++) {
        // change the element clone's template id to field-specific id
        var curr_object = template_id_objects[i];
        var curr_id_selector = getIdSelectorFromId(curr_object.id);
        var new_id = getNewIdentifierFromTemplateAndIndex(curr_object.id, field_index);
        var new_id_selector = getIdSelectorFromId(new_id);
        $html.find(curr_id_selector).prop('id', new_id);

        // if the element has a name attribute, change its element clone's name to a field-specific one
        // see https://stackoverflow.com/a/1318091
        var name_attr = $(curr_object).attr('name');
        // For some browsers, `attr` is undefined; for others,
        // `attr` is false.  Check for both.
        if (typeof name_attr !== typeof undefined && name_attr !== false) {
            var new_name = getNewIdentifierFromTemplateAndIndex(curr_object.name, field_index);
            $html.find(new_id_selector)[0].name = new_name;
        }
    }

    return $html.html();
}

// Add events/validations to dynamically created input elements for new field
function decorateNewElements() {
    var newest_field_index = getCurrNumFields() - 1;

    for (i = 0, len = NEW_ELEMENT_SET_UP_FUNCTIONS.length; i < len; i++) {
        NEW_ELEMENT_SET_UP_FUNCTIONS[i](newest_field_index);
    }
}

// For JQuery validation plugin, custom validator functions always have
// first argument: the current value of the validated element. Second argument: the element to be validated
$.validator.addMethod("nameIsUnique", function(value, element) {
    var return_val = true; // default: assume unique
    var num_fields = getCurrNumFields();
    var found_field_names = $.extend({}, package_fields);
    for (i = 0; i < num_fields; i++) {
        var curr_field_name_id_selector = getIdSelectorFromBaseNameAndFieldIndex(SpecialInputs.FIELD_NAME, i);
        var curr_field_name_value = $(curr_field_name_id_selector).val();
        if (curr_field_name_value !== "") {
            if( found_field_names[curr_field_name_value] ){
                return_val = false;
                break;
            } else {
                found_field_names[curr_field_name_value] = true;
            }
        }
    }

    return return_val;
}, "Field name must be unique");

// For JQuery validation plugin, custom validator functions always have
// first argument: the current value of the validated element. Second argument: the element to be validated
$.validator.addMethod("nameIsNotReserved", function(value, element) {
    // if the value in the name element appears in the list of reserved words, then it is invalid
    return (g_reserved_words.indexOf(value) <= -1);
}, "Field name must not be a reserved word.");

var allowed_date_formats = ["YYYY-MM-DD hh:mm:ss", "YYYY-MM-DD hh:mm", "YYYY-MM-DD hh", "YYYY-MM-DD", "YYYY-MM",
    "YYYY"];
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

    return return_val;
}, "DateTime must be a valid timestamp in one of these formats: " + allowed_date_formats.join(" or "));

var package_fields = {};

var NEW_ELEMENT_SET_UP_FUNCTIONS = [
    function(field_index) { //make field name required and also unique
        addAlwaysRequiredRule(field_index, SpecialInputs.FIELD_NAME);
        addUniqueNameRule(field_index);
        addNameIsNotReservedRule(field_index);
        addLowerCaseLettersAndUnderscoreRule(field_index, SpecialInputs.FIELD_NAME);
    },
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
            var raw_reserved_words = jsyaml.load( text );
            for (var i=0, len = raw_reserved_words.length; i < len; i++) {
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


    ws = new WebSocket(websocket_url);
    ws.onmessage = function(evt) {
        var fields_message = "<br />The following fields will be added to your metadata template: " +  evt.data +
            ".<br /><strong>Note that none of these names will be available for custom fields.</strong><br /><br />";
        $(getIdSelectorFromId("package_details_div")).html(fields_message);

        var fields_list = evt.data.split(", ");
        var temp_package_fields = {};
        for (var i = 0, len = fields_list.length; i < len; i++) {
            temp_package_fields[fields_list[i]] = true;
        }
        package_fields = $.extend({}, temp_package_fields);
        $(getIdSelectorFromId("metadata_form")).removeClass('hidden');
    };

    ws.onopen = function () {};
    ws.onclose = function () {};

    // set up validators
    $("#package_form").validate({
        submitHandler: getPackage
    });

    $("#metadata_form").validate({
	        rules: {
	            "study_name": {
	                required: true,
	                pattern: /^[a-zA-Z0-9 ]*$/,
                    minlength: 2,
	                maxlength: 400

	            }
	        },
	        messages: {
	            "study_name": {
	                required: "This field is required.",
	                pattern: "Only letters, numbers, and spaces are permitted.",
	                maxlength: "This field must be 400 characters or fewer."
	            }
	        }
	    }
    );

    // Get the html from template and add a set of elements for the first field
    var new_html = $('<div/>', {
        'class' : 'row field', html: generateFieldHtml()
    });
    new_html.appendTo('#container');

    // once the new elements exist, set up events/etc
    decorateNewElements();

    // Add event so that when someone clicks to add a row, a new set of elements
    // is added to represent that new field and *its* events are set up
    $('#addField').click(function () {
        $('<div/>', {
            'class' : 'row field', html: generateFieldHtml()
        }).hide().appendTo('#container').slideDown('slow');

        // once the new elements exist, set up events/etc
        decorateNewElements();
    });
});
