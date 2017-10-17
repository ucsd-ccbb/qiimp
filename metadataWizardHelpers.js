function addUniqueNameRule(field_index){
    var name_id_selector = getIdSelectorFromBaseNameAndFieldIndex(SpecialInputs.FIELD_NAME, field_index);
    $(name_id_selector).rules("add", {
       nameIsUnique: true
    });
}

function addNameIsNotReservedRule(field_index){
    var name_id_selector = getIdSelectorFromBaseNameAndFieldIndex(SpecialInputs.FIELD_NAME, field_index);
    $(name_id_selector).rules("add", {
       nameIsNotReserved: true
    });
}

function addOnChangeEvent(field_index, base_name, onChangeFunc){
    addEventHandler("change", field_index, base_name, onChangeFunc);
}

function addOnClickEvent(field_index, base_name, onChangeFunc){
    addEventHandler("click", field_index, base_name, onChangeFunc);
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
                                       list_has_dual_values){
    function build_option_str(new_val, new_text, is_selected) {
        var selected_str = "";
        if (is_selected) {selected_str = "selected"}
        return '<option value="' + new_val + '" ' + selected_str + '>' + new_text + '</option>'
    }

    // remove existing options
    $(select_id_selector).empty();

    // add new options
    var new_options = [];
    if (add_placeholder === null) {add_placeholder = true;}
    if (add_placeholder) {
        new_options.push(build_option_str("", "--Select One--", false))
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

function getCurrNumFields() {
    return $('.field').length;
}
