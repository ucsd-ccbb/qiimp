function getFieldNameValueByIndex(field_index) {
    var field_name_input_id_selector = getIdSelectorFromBaseNameAndFieldIndex(SpecialInputs.FIELD_NAME, field_index);
    var field_name_input = $(field_name_input_id_selector)[0];
    return field_name_input.value;
}

function validatePutativeFieldName(putative_field_name){
    var error_msgs = [];
    error_msgs.push(validateNameIsNotReserved(putative_field_name));
    error_msgs.push(validateNameMatchesPattern(putative_field_name));
    error_msgs.push(validateNameIsUnique(putative_field_name));
    // (filter - JS 1.6 and above)
    error_msgs = error_msgs.filter(function(x){ return x !== null });
    return error_msgs;
}

function validateNameIsNotReserved(putative_field_name) {
    var result = null;
    // if the value in the name element appears in the list of reserved words, then it is invalid
    if (g_reserved_words.indexOf(putative_field_name) > -1) {
        result = "'" + putative_field_name + "' is not an allowed field name because it is a reserved word.";
    }
    return result;
}

function validateNameMatchesPattern(putative_field_name) {
    var result = null;
    if (!field_name_regex.test(putative_field_name)) {
        result = "Only lower-case letters, numbers, and underscores are permitted, and must not start with a number.";
    }
    return result;
}

function validateNameIsUnique(putative_field_name) {
    var result = null; // default: assume unique
    if (existing_field_names[putative_field_name]){
        result = "Field name must be unique."
    }
    return result;
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

function addDateTimeValidationRule(field_index, required_base_name){
    var id_selector = getIdSelectorFromBaseNameAndFieldIndex(required_base_name, field_index);
    $(id_selector).rules("add", {
        isValidDateTime: true
    });
}

function addOnChangeEvent(field_index, base_name, onChangeFunc){
    addEventHandler("change", field_index, base_name, onChangeFunc);
}

function addEventHandler(event_name, field_index, base_name, onEventFunc){
    var id_selector = getIdSelectorFromBaseNameAndFieldIndex(base_name, field_index);
    $(id_selector).on( event_name, {field_index:field_index}, onEventFunc)
}

function doesElementHaveValue(base_name, field_index) {
    var result = true; //default
    var element_id = getIdSelectorFromBaseNameAndFieldIndex(base_name, field_index);
    var element_val = $(element_id)[0].value;
    if (!($.trim(element_val)).length) {result = false;} // see https://stackoverflow.com/a/1854584
    return result;
}

function enableOrDisableByValue(base_name, field_index, curr_val, enable_value) {
    var element_id_selector = getIdSelectorFromBaseNameAndFieldIndex(base_name, field_index);
    enableOrDisableBySelectorAndValue(element_id_selector, curr_val, enable_value);
}

function enableOrDisableBySelectorAndValue(element_selector, curr_val, enable_value){
    if (curr_val === enable_value) {
        $(element_selector).removeAttr("disabled");
    } else {
        $(element_selector).prop('disabled', 'disabled');
    }
}

function showEnableOrHideDisable(curr_selector, do_show){
    // update the element's display state (either way)
    if (!do_show)  {
        $(curr_selector).addClass('hidden');
        $(curr_selector + ' :input').attr('disabled', true);
    } else {
        $(curr_selector).removeClass('hidden');
        // Note this enables everything.  If you need to have somethings still disabled,
        // go back afterwards and (re-)disable them
        $(curr_selector + ' :input').removeAttr('disabled');
        $(curr_selector).slideDown();
    }
}

function resetSelectedOptionIfDisabled(select_id_selector){
    var selected_option = $(select_id_selector).find('option:selected');
    var disabled_val = selected_option.attr('disabled');
    var enabled = (disabled_val === false) || (disabled_val === undefined);

    // if the currently selected option is now disabled, reset which option is selected to be the
    // placeholder option
    if (!enabled) {$(select_id_selector).val("");}
}

function updateSelectWithNewCategories(select_id_selector, values_list, selected_value, add_placeholder,
                                       list_has_dual_values, retain_existing, fixed_size){
    function build_option_str(new_val, new_text, is_selected) {
        var selected_str = "";
        if (is_selected) {selected_str = "selected"}
        return '<option value="' + new_val + '" ' + selected_str + '>' + new_text + '</option>'
    }

    // add new options
    var new_options = [];
    if (add_placeholder === null) {add_placeholder = true;}
    if (add_placeholder) {
        new_options.push(build_option_str("", "--Select One--", false))
    }

    if (retain_existing) {
        // first add the existing options to the "new options" list
        new_options.push($(select_id_selector).html());
    }

    for (var i = 0; i < values_list.length; i++) {
        var new_val = values_list[i];
        var new_text = new_val;
        if (list_has_dual_values) {
            new_val = values_list[i][0];
            new_text = values_list[i][1];
        }

        var is_selected = (new_val === selected_value);
        new_options.push(build_option_str(new_val, new_text, is_selected));
    }

    $(select_id_selector).html(new_options.join(''));
    var num_options = values_list.length;
    if (fixed_size){
        num_options = null;
    }
    setSelectSize(select_id_selector, num_options);
}

// num_options is optional.  If you want the select box to be the minimum of the number of options or the max size,
// include this argument.  If you want the select box to always be the max size, just pass null for this argument.
function setSelectSize(select_id_selector, num_options){
    var size = max_selectbox_size;
    if (num_options !== null) {
        // set the size of the select box to be the number of categories or the max
        size = Math.min(num_options, max_selectbox_size)
    }
    $(select_id_selector).attr('size', size)
}

function getTemplateFromBaseIdentifier(base_name){
    return base_name + TEMPLATE_SUFFIX;
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
    return full_template_name.replace(TEMPLATE_SUFFIX, SEPARATOR + field_index.toString());
}