$.validator.setDefaults({
    submitHandler: function() {
        alert("submitted!");
    }
});

// TODO: have continuous default onblur to ensure it meets data type, any min/max for its field
// TODO: have onblur for min and max to ensure they are data type for field
// TODO: figure out validation for if selectbox selected value is now disabled
// TODO: figure out what date and/or time options to support (ask Gail/Austin)


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
    function(field_index) { //make field name required
        addAlwaysRequiredRule(field_index, SpecialInputs.FIELD_NAME);
    },
    function(field_index) {  // set onchange handler on field type and make required
        addAlwaysRequiredRule(field_index, SpecialInputs.FIELD_TYPE);
        addOnChangeEvent(field_index, SpecialInputs.FIELD_TYPE, displayFieldDetails);
    },
    function (field_index) { //set special onchange handler on allowed values checkboxes group
        var id_selector = getIdSelectorFromBaseNameAndFieldIndex(SpecialInputs.ALLOWED_MISSINGS, field_index);
        var id_and_state_selector = id_selector + " :checkbox"; //selector for all checkboxes inside group fieldset
        $(id_and_state_selector).on("change", {field_index:field_index}, updateDefaultsWithMissings);
    },
     function (field_index) {
        var name_selector = "input:radio[name='" + SpecialInputs.DEFAULT_OPTION + SEPARATOR + field_index + "']";
        $(name_selector).on("change", {field_index:field_index}, enableDisableDefaultSelects);
    },
    function (field_index) { //make data_type required and set onchange handler to update type validation of default
        addAlwaysRequiredRule(field_index, SpecialInputs.DATA_TYPE);
        addOnChangeEvent(field_index, SpecialInputs.DATA_TYPE, updateTypeValidationOnDefault);
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

function addOnChangeEvent(field_index, base_name, onChangeFunc){
        var id_selector = getIdSelectorFromBaseNameAndFieldIndex(base_name, field_index);
        $(id_selector).on("change", {field_index:field_index}, onChangeFunc)
}

function addAlwaysRequiredRule(field_index, required_base_name) {
        var id_selector = getIdSelectorFromBaseNameAndFieldIndex(required_base_name, field_index);
        $(id_selector).rules("add", {
           required: true
        });
}

function addConditionalRequiredRule(field_index, condition_base_name, required_base_name) {
        var id_selector = getIdSelectorFromBaseNameAndFieldIndex(condition_base_name, field_index);
        $(id_selector).rules("add", {
            required: function() {
                return doesElementHaveValue(required_base_name, field_index);
            }
        });
}

function doesElementHaveValue(base_name, field_index) {
    var result = true; //default
    var element_id = getIdSelectorFromBaseNameAndFieldIndex(base_name, field_index);
    var element_val = $(element_id)[0].value;
    // see https://stackoverflow.com/a/1854584
    if (!($.trim(element_val)).length) {result = false;}
    return result;
}

function decorateNewElements() {
    var newest_field_index = getCurrNumFields() - 1;

    for (i = 0, len = NEW_ELEMENT_SET_UP_FUNCTIONS.length; i < len; i++) {
        NEW_ELEMENT_SET_UP_FUNCTIONS[i](newest_field_index);
    }
}

function displayFieldDetails(event) {
    var fields_to_show_by_field_type = {
        "":[],
        "text":[],
        "boolean": ["field_details_div","boolean_true_div", "boolean_false_div", "boolean_default_div"],
        "continuous": ["field_details_div","data_type_div", "minimum_div", "maximum_div", "units_div", "continuous_default_div"],
        "categorical": ["field_details_div","data_type_div", "categorical_div", "units_div", "categorical_default_div"]
    };

    var selected_field_type = $(event.target).val();
    var field_index = event.data.field_index;
    var elements_to_show = fields_to_show_by_field_type[selected_field_type];
    var conditional_settings = $('[id$=_' + field_index + '].initially_hidden');

    for (var i = 0, len = conditional_settings.length; i < len; i++){
        var do_show = false; // default is hide
        var curr_setting_id = conditional_settings[i].id;
        var curr_setting_selector = "#" + curr_setting_id;

        for (var j = 0, len2 = elements_to_show.length; j < len2; j++) {
            var potential_element_to_show = elements_to_show[j];
            if (curr_setting_id.startsWith(potential_element_to_show)){
                do_show = true;
                break;
            }
        }

        if (!do_show)  {
            $(curr_setting_selector).addClass('hidden');
        } else {
            $(curr_setting_selector).removeClass('hidden');
            //$(curr_setting_selector).slideDown();
        }
    }
}

function updateDefaultsWithMissings(event){
    var the_target = $(event.target);
    var field_index = event.data.field_index;
    var checkbox_value = the_target.val();
    var checkbox_ischecked = the_target.is(":checked");

    var default_missings_id_selector = getIdSelectorFromBaseNameAndFieldIndex(SpecialInputs.DEFAULT_MISSINGS,
        field_index);
    var selected_option = $(default_missings_id_selector + " option").filter( "[value='" + checkbox_value + "']" );

    if (checkbox_ischecked) {
        selected_option.removeAttr("disabled")
    } else {
        selected_option.prop("disabled", "disabled")
    }
}

function enableDisableDefaultSelects(event) {
    var field_index = event.data.field_index;
    var curr_val = this.value;

    enableOrDisableByValue(SpecialInputs.DEFAULT_MISSINGS, field_index, curr_val, "allowed_missing_default");
    enableOrDisableByValue(SpecialInputs.DEFAULT_CATEGORICAL, field_index, curr_val, "categorical_default");
    enableOrDisableByValue(SpecialInputs.DEFAULT_BOOLEAN, field_index, curr_val, "boolean_default");
    enableOrDisableByValue(SpecialInputs.DEFAULT_CONTINUOUS, field_index, curr_val, "continuous_default");
}

function enableOrDisableByValue(base_name, field_index, curr_val, enable_value) {
    var element_id_selector = getIdSelectorFromBaseNameAndFieldIndex(base_name, field_index);
    if (curr_val === enable_value) {
        $(element_id_selector).removeAttr("disabled");
    } else {
        $(element_id_selector).prop('disabled', 'disabled');
    }
}

function updateSelectWithNewCategories(select_id_selector, values_list){
    // remove existing options
    $(select_id_selector).empty();

    // add new options
    var new_options = ['<option value="">--Select One--</option>'];
    for (var i = 0; i < values_list.length; i++) {
        var new_val = values_list[i];
        new_options.push('<option value="' + new_val + '">' + new_val + '</option>');
    }

    $(select_id_selector).html(new_options.join(''));
}

function updateDefaultsWithCategories(event) {
    var field_index = event.data.field_index;
    // remove existing options
    var default_categorical_id_selector = getIdSelectorFromBaseNameAndFieldIndex(SpecialInputs.DEFAULT_CATEGORICAL,
        field_index);

    // add new options
    var split = $(this).val().split('\n');
    var lines = [];
    for (var i = 0; i < split.length; i++) {
        if (split[i]) { lines.push(split[i]);}
    }

    updateSelectWithNewCategories(default_categorical_id_selector, lines);
}

function updateTypeValidationOnDefault(event){
    alert("In updateTypeValidationOnDefault (not yet implemented)");
}

function updateDefaultsWithBooleanVals(event){
    var field_index = event.data.field_index;
    var new_options = [];
    var base_names = [SpecialInputs.TRUE_VALUE, SpecialInputs.FALSE_VALUE];
    for (i = 0; i < base_names.length; i++) {
        var val_id_selector = getIdSelectorFromBaseNameAndFieldIndex(base_names[i], field_index);
        var found_val = $(val_id_selector).val();
        if (found_val) {new_options.push(found_val);}
    }

    var default_boolean_id_selector = getIdSelectorFromBaseNameAndFieldIndex(SpecialInputs.DEFAULT_BOOLEAN,
        field_index);
    updateSelectWithNewCategories(default_boolean_id_selector, new_options);
}

function getTemplateFromBaseIdentifier(base_name){
    return base_name + SEPARATOR + TEMPLATE_SUFFIX;
}

function getIdSelectorFromBaseNameAndFieldIndex(base_name, field_index) {
    var id = getIdentifierFromBaseNameAndFieldIndex(base_name, field_index);
    return getIdSelectorFromId(id);
}

function getIdentifierFromBaseNameAndFieldIndex(base_name, field_index) {
    var full_template_name = getTemplateFromBaseIdentifier(base_name);
    return getNewIdentifierFromTemplateAndIndex(full_template_name, field_index);
}

function getIdSelectorFromId(id_str) {
    return "#" + id_str;
}

function getNewIdentifierFromTemplateAndIndex(full_template_name, field_index) {
    return full_template_name.replace(TEMPLATE_SUFFIX, field_index.toString());
}

function getCurrNumFields() {
    return $('.field').length;
}

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
    $('#addRow').click(function () {
        $('<div/>', {
            'class' : 'field', html: generateFieldHtml()
        }).hide().appendTo('#container').slideDown('slow');

        // once the new elements exist, set up events/etc
        decorateNewElements();
    });
});
