function addUniqueNameRule(field_index){
    var name_id_selector = getIdSelectorFromBaseNameAndFieldIndex(SpecialInputs.FIELD_NAME, field_index);
    $(name_id_selector).rules("add", {
       nameIsUnique: true
    });
}

function addOnChangeEvent(field_index, base_name, onChangeFunc){
    var id_selector = getIdSelectorFromBaseNameAndFieldIndex(base_name, field_index);
    $(id_selector).on("change", {field_index:field_index}, onChangeFunc)
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

function enableDisableDefaultSelects(field_index, curr_val){
        // TODO: Determine whether to pull the below text values out into symbolic constants
    enableOrDisableByValue(SpecialInputs.DEFAULT_MISSINGS, field_index, curr_val, "allowed_missing_default");
    enableOrDisableByValue(SpecialInputs.DEFAULT_CATEGORICAL, field_index, curr_val, "categorical_default");
    enableOrDisableByValue(SpecialInputs.DEFAULT_BOOLEAN, field_index, curr_val, "boolean_default");
    enableOrDisableByValue(SpecialInputs.DEFAULT_CONTINUOUS, field_index, curr_val, "continuous_default");
}

function enableOrDisableBySelectorAndValue(element_selector, curr_val, enable_value){
    if (curr_val === enable_value) {
        $(element_selector).removeAttr("disabled");
    } else {
        $(element_selector).prop('disabled', 'disabled');
    }
}

function resetSelectedOptionIfDisabled(select_id_selector){
    var selected_option = $(select_id_selector).find('option:selected');
    var disabled_val = selected_option.attr('disabled');
    var enabled = (disabled_val === false) || (disabled_val === undefined);

    // if the currently selected option is now disbled, reset which option is selected to be the
    // placeholder option
    if (!enabled) {$(select_id_selector).val("");}
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

function updateTypeValidation(base_name, field_index, data_type_value){
    // get the relevant input field and remove any existing validation rules related to data type (only)
    var input_id_selector = getIdSelectorFromBaseNameAndFieldIndex(base_name, field_index);
    $(input_id_selector).rules( "remove", "digits number" );

    // add back any required data type validation rule
    switch (data_type_value) {
        case "integer":
            $(input_id_selector).rules("add", {
               digits: true
            });
            break;
        case "float":
            $(input_id_selector).rules("add", {
               number: true
            });
            break;
        case "str":
            // no known validation required for text; perhaps length?
            break;
        default:
            alert("Unexpected data type value: '" + data_type_value + "'")
    }
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
