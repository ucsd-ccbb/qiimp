// Dynamically generate HTML specifying input elements for a new field
function generateFieldHtml() {
    var field_index = getCurrNumFields();
    var $html = $('.fieldTemplate').clone();
    var template_suffix = "_template";
    var template_id_objects = $("[id$=" + template_suffix + "]");

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

function addAlwaysRequiredRule(field_index, required_base_name) {
    var id_selector = getIdSelectorFromBaseNameAndFieldIndex(required_base_name, field_index);
    $(id_selector).rules("add", {
       required: true
    });
}

function addConditionalRequiredRule(field_index, condition_base_name, required_base_name) {
    var id_selector = getIdSelectorFromBaseNameAndFieldIndex(condition_base_name, field_index);

    // For JQuery validation plugin, custom validator functions always have
    // first argument: the current value of the validated element. Second argument: the element to be validated
    $(id_selector).rules("add", {
        required: function(value, element) {
            return doesElementHaveValue(required_base_name, field_index);
        }
    });
}

// TODO: This is a temporary setting to prevent submission during debugging.
// REMOVE FOR PRODUCTION CODE.
$.validator.setDefaults({
    submitHandler: function() {
        alert("submitted!");
    }
});

// For JQuery validation plugin, custom validator functions always have
// first argument: the current value of the validated element. Second argument: the element to be validated
$.validator.addMethod("nameIsUnique", function(value, element) {
    var return_val = true; // default: assume unique
    var num_fields = getCurrNumFields();
    var found_field_names = {};
    for (i = 0; i < num_fields; i++) {
        var curr_field_name_id_selector = getIdSelectorFromBaseNameAndFieldIndex("field_name", i);
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

// TODO: Ask Gail/Austin: must continuous default val conform to min, max, min_compare, or max_compare?
// TODO: Ask Gail/Austin: what date and/or time options to support?
// TODO: Ask Gail/Austin: length, other limits on field names (besides unique)?
// TODO: Ask Gail/Austin: should there be a default option for free-form text field type?

// TODO: ensure validation attaches to correct fields when there is more than one
// TODO: attach to back end and see what I receive :)


// Note that these are to be the bases (without template suffix or separator) of form element NAMES, not IDs
var SpecialInputs = {
    FIELD_NAME: "field_name",
    FIELD_TYPE: "field_type",
    ALLOWED_MISSINGS: "allowed_missing_vals_fieldset",
    DATA_TYPE: "data_type",
    TRUE_VALUE: "true_value",
    FALSE_VALUE: "false_value",
    MINIMUM: "minimum_value",
    MIN_COMPARE: "minimum_comparison",
    MAXIMUM: "maximum_value",
    MAX_COMPARE: "maximum_comparison",
    CATEGORY_VALS: "categorical_values",
    DEFAULT_MISSINGS: "allowed_missing_default_select",
    DEFAULT_OPTION: "default_value",
    DEFAULT_CATEGORICAL: "categorical_default_select",
    DEFAULT_BOOLEAN: "boolean_default_select",
    DEFAULT_CONTINUOUS: "continuous_default"
};

var TEMPLATE_SUFFIX = "template";
var SEPARATOR = "_";

var NEW_ELEMENT_SET_UP_FUNCTIONS = [
    function(field_index) { //make field name required and also unique
        addAlwaysRequiredRule(field_index, SpecialInputs.FIELD_NAME);
        addUniqueNameRule(field_index);
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
         // TODO: should I also make these radio buttons required, or is that moot since one is pre-selected?
         var name_selector = "input:radio[name='" + SpecialInputs.DEFAULT_OPTION + SEPARATOR + field_index + "']";
         $(name_selector).on("change", {field_index:field_index}, enableDisableDefaultSelects);
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
    }
];

// Code to run as soon code as the document is ready to be manipulated
$(document).ready(function () {
    // set up validator
    $("#metadata_form").validate({
        rules: {
                study_name: {
                    required: true
                }
            }
        });

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
