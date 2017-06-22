// Reset displayed interface elements and data type options when field type is changed
function resetFieldDetails(event) {
    // find out what field type was selected
    var selected_field_type = $(event.target).val();
    var field_index = event.data.field_index;

    displayFieldDetails(selected_field_type, field_index);
    enableDisableTextDataType(selected_field_type, field_index);
}

// Enable/disable the "text" option in data type when the field type is changed
function enableDisableTextDataType(selected_field_type, field_index){
    var data_type_id_selector = getIdSelectorFromBaseNameAndFieldIndex(SpecialInputs.DATA_TYPE, field_index);

    // if the field type is categorical, the data type may be text.  If field type is anything else, text is disabled.
    var select_option_for_field_type_selector = data_type_id_selector + " option[value='str']";
    enableOrDisableBySelectorAndValue(select_option_for_field_type_selector, selected_field_type, "categorical");
        resetSelectedOptionIfDisabled(data_type_id_selector);
}

// Show/hide appropriate interface elements when field type is changed
function displayFieldDetails(selected_field_type, field_index) {
    var fields_to_show_by_field_type = {
        "":[],
        "str":[],
        "boolean": ["field_details_div","boolean_true_div", "boolean_false_div", "boolean_default_div"],
        "continuous": ["field_details_div","data_type_div", "minimum_div", "maximum_div", "units_div",
            "continuous_default_div"],
        "categorical": ["field_details_div","data_type_div", "categorical_div", "units_div", "categorical_default_div"]
    };
    var elements_to_show = fields_to_show_by_field_type[selected_field_type];

    // find all elements for the current field that were initially hidden
    var conditional_settings = $('[id$=_' + field_index + '].initially_hidden');
    for (var i = 0, len = conditional_settings.length; i < len; i++){
        // by default, assume all elements will be hidden
        var do_show = false;
        var curr_setting_id = conditional_settings[i].id;
        var curr_setting_selector = "#" + curr_setting_id;

        // if the current element IS in the list of those that should be shown for the currently selected
        // field type, then mark it so show
        for (var j = 0, len2 = elements_to_show.length; j < len2; j++) {
            var potential_element_to_show = elements_to_show[j];
            if (curr_setting_id.startsWith(potential_element_to_show)){
                do_show = true;
                break;
            }
        }
        // Note two-step approach when showing: first enable everything.
        // Then, outside loop, go back and (re-)disable default
        // selects that go with default choices that aren't actually chosen
        showEnableOrHideDisable(curr_setting_selector, do_show);
    }

    enableDisableDefaultSelectsOnFieldTypeChange(field_index);
}

function enableDisableDefaultSelectsOnFieldTypeChange(field_index){
    // get the selected value for the default radio button set for this index
    var default_radio_name = getIdentifierFromBaseNameAndFieldIndex(SpecialInputs.DEFAULT_OPTION, field_index);
    var curr_val = $("input[name='"+ default_radio_name + "']:checked").val();
    // disable/enable the default select boxes based on the current value
    enableDisableDefaultSelects(field_index, curr_val);
}


// Enable/disable appropriate subordinate input elements when type of default setting is changed
function enableDisableDefaultSelectsOnDefaultChange(event) {
    var field_index = event.data.field_index;
    var curr_val = this.value;
    enableDisableDefaultSelects(field_index, curr_val)
}


// Enable/disable select box options for allowed missing default when allowed missing checkbox(es) are changed
function updateDefaultsWithMissings(event){
    var the_target = $(event.target);
    var field_index = event.data.field_index;
    var checkbox_value = the_target.val();
    var checkbox_ischecked = the_target.is(":checked");

    var default_missings_id_selector = getIdSelectorFromBaseNameAndFieldIndex(SpecialInputs.DEFAULT_MISSINGS,
        field_index);
    var select_option_for_checked_val_selector = default_missings_id_selector +
        " option[value='" + checkbox_value + "']";
    enableOrDisableBySelectorAndValue(select_option_for_checked_val_selector, checkbox_ischecked, true);
    resetSelectedOptionIfDisabled(default_missings_id_selector);
}

// Refresh select box options for categorical default when category items text area is changed
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

// Refresh select box options for boolean default when boolean true_value or false_value text is changed
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

// Reset type validation on minimum, maximum, and continuous default when data type select is changed
function updateTypeValidations(event){
    // find out what data type was selected
    var field_index = event.data.field_index;
    var data_type_value = $(event.target).val();

    updateTypeValidation(SpecialInputs.MINIMUM, field_index, data_type_value);
    updateTypeValidation(SpecialInputs.MAXIMUM, field_index, data_type_value);
    updateTypeValidation(SpecialInputs.DEFAULT_CONTINUOUS, field_index, data_type_value);
}
