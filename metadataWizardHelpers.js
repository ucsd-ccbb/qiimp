function temp_parse_form_round_trip(){
    // TODO: currently not handling non-field values (default locale, study name, etc) ... should I?



    // NB: I do NOT care (or require) that the fields go in with the same field indexes they did in the original
    // form that we are recreating.  The only thing I care about is that they go in in the same ORDER.
    var text = "0:\n" +
        "  allowed_missing_default_select: ebi_not_provided\n" +
        "  allowed_missing_vals[]:\n" +
        "  - ebi_not_collected\n" +
        "  - ebi_not_provided\n" +
        "  categorical_values: \"kiw\\r\\nned\\r\\ngugg\"\n" +
        "  default_value: allowed_missing_default\n" +
        "  field_name: phenotype\n" +
        "  field_type: categorical\n" +
        "1:\n" +
        "  default_value: text_default\n" +
        "  field_desc: a lot of fun\n" +
        "  field_name: is_patient\n" +
        "  field_type: string\n" +
        "  text_default: green";
    var round_trip_form_vals_dict = jsyaml.load(text);
    addFields(round_trip_form_vals_dict);
}

function addFields(input_field_names_or_dicts){
    var new_field_nums_and_names = [];
    var is_dicts = !Array.isArray(input_field_names_or_dicts);

    for (var curr_item in input_field_names_or_dicts) {
        var curr_field_dict = null;
        var curr_field_name = input_field_names_or_dicts[curr_item];
        if (is_dicts) {
            curr_field_dict = curr_field_name;
            curr_field_name = curr_field_dict[SpecialInputs.FIELD_NAME];
        }

        if ((curr_field_name !== "") && (!existing_field_names[curr_field_name])) {
            existing_field_names[curr_field_name] = true;

            var new_html = generateFieldHtml(curr_field_name);
            $('<div/>', {html: new_html}).appendTo('#field_details_div');

            // once the new elements exist, set up events/etc
            decorateNewElements(next_field_num);

            if (curr_field_dict !== null){
                for (var curr_field_key in curr_field_dict) {
                    var input_value = curr_field_dict[curr_field_key];
                    var input_name= getIdentifierFromBaseNameAndFieldIndex(curr_field_key, next_field_num);

                    // TODO: refactor hard-coded square brackets
                    if (curr_field_key.endsWith("[]")) {
                        // TODO: must find better way to place brackets ... also icky in template.html
                        input_name = input_name.replace("[]", "");
                        input_name = input_name + "[]";
                        // assume we're dealing with values from a checkbox fieldset
                        for (var curr_checkbox_val_index in input_value){
                            // only trigger onchange event after setting last value in field;
                            // otherwise, since fields come through dictionary in basically arbitrary order,
                            // effect of partial change of allowed missing checkboxes can wipe out
                            // allowed missing default select, if that happened to come through first,
                            // because of allowed missing fieldset's onchange's call to resetSelectedOptionIfDisabled.
                            var trigger_onchange = curr_checkbox_val_index === input_value.length-1;
                            setFormValue(input_name, input_value[curr_checkbox_val_index], trigger_onchange);
                        }
                    } else {
                        setFormValue(input_name, input_value, true);
                    }
                }
            }

            new_field_nums_and_names.push([next_field_num, curr_field_name]);
            next_field_num++;
        }
    }

    // add new values to the select list for field_names_sel
    var field_names_sel_id_selector = getIdSelectorFromId(SpecialInputs.FIELD_NAMES_SELECT);
    updateSelectWithNewCategories(field_names_sel_id_selector, new_field_nums_and_names, null, false,
        true, true, true);

    // show the div with the field names and details
    var existing_fields_id_selector = getIdSelectorFromId("existing_fields");
    $(existing_fields_id_selector).removeClass('hidden');
}

function setFormValue(input_name, input_value, trigger_onchange){
    var input_name_selector = "[name='" + input_name + "']";
    var input_element = $(input_name_selector);
    var input_type = getElementType(input_element);

    // TODO: refactor out option selector generation?
    switch(input_type) {
        case "checkbox":
            $(input_name_selector + "[value='" + input_value + "']").prop("checked", true);
            break;
        case "radio":
            $(input_name_selector + "[value='" + input_value + "']").prop("checked", true);
            break;
        case "select":
            $(input_name_selector + " option[value='" + input_value + "']").prop("selected", true);
            break;
        case "textarea":
            $(input_name_selector).html(input_value);
            break;
        case "hidden":
            // NB: INTENTIONAL FALL-THROUGH to text case!  Do NOT add break here.
        case "text":
            $(input_name_selector).attr("value", input_value);
            break;
        default:
            // TODO: add error handling
    }

    if (trigger_onchange) {
        // Manually trigger onchange event, if any, of changed form element(s)
        $(input_name_selector).change();
    }
}

// From https://stackoverflow.com/a/9116746
function getElementType(element){
    return element[0].tagName == "INPUT" ? element[0].type.toLowerCase() : element[0].tagName.toLowerCase();
}

function findFieldIndexFromNameOrId(field_identifier){
    var result = null;  // default: assume field has no index (like "study_name")
    var id_pieces = field_identifier.split(SEPARATOR);
    var field_num_str = id_pieces[id_pieces.length-1];
    // Check if string contains a valid integer, per https://stackoverflow.com/a/35759874
    if (!isNaN(field_num_str) && !isNaN(parseFloat(field_num_str))){
        result = parseInt(field_num_str);
    }
    return result;
}

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