// TODO: Refactor to pull from back-end
var HOST_ASSOCIATED_SAMPLE_TYPES = [
    "stool",
    "mucus"
];

function onModeChange(element){
    // TODO: someday: remove hardcoding of div names, etc
    var mode_divs = ["power_div", "wizard_div"];
    var selected_mode = element.value;
    var div_to_display_basename = selected_mode.replace("metadata_mode_","");
    var div_to_display = div_to_display_basename + "_div";

    for (var i = 0, len = mode_divs.length; i < len; i++){
        var curr_mode_div = mode_divs[i];
        var curr_mode_div_selector = getIdSelectorFromId(curr_mode_div);
        var do_show = false; // default to false
        if (curr_mode_div === div_to_display){
          do_show = true;
        }
        showEnableOrHideDisable(curr_mode_div_selector, do_show);
    }

    // once user has picked a route, enable the select package button
    enableOrDisableBySelectorAndValue(getIdSelectorFromId("select_package_button"), true, true)
}

function onSelectPackage(){
    var package_key = determinePackageKey();
    if (package_key === null) {
        return false;
    }

    // If the user re-chose the SAME package, do nothing
    if (g_fields_state.package_key === package_key){
        return;
    }

    // If any custom fields have been added, warn the user they will be cleared by replacing the package
    if (g_fields_state.getCurrentNextFieldNum() > 0) {
        var confirm_msg = "Changing the package selection will remove all custom fields.  Clear existing custom fields and change package?";
        if (!confirm(confirm_msg)) {
            return; //do nothing if they fail to confirm
        }
    }

    resetFieldsAndDivs(package_key);

    // Make an ajax call to get the list of field names for this package and the list of reserved words
    $.ajax({
        url : '/package',
        type : 'POST',
        data : package_key,
        dataType: 'json',
        success : ajax_ok,
        error: ajax_err
    });
}

function determinePackageKey(){
    var package_key = null;
    var package_select_id_selector = getIdSelectorFromId("package_select");
    var sampletype_select_id_selector = getIdSelectorFromId("sample_type_select");
    var host_select_id_selector = getIdSelectorFromId("host_select");

    // check the "power user" value--the precise, organism-specific package to use
    if (!$(package_select_id_selector).is(':disabled')) {
        var valid_pkg = $(package_select_id_selector).valid();
        if (valid_pkg) {
            package_key = $(package_select_id_selector).val();
        }
    } else {
        var valid_sampletype = $(sampletype_select_id_selector).valid();
        var valid_host = $(host_select_id_selector).valid();
        if (valid_sampletype && valid_host) {
            // get the host type and the sample type and paste them together to get the package name to look for
            var host = $(host_select_id_selector).val();
            var sample_type = $(sampletype_select_id_selector).val();
            package_key = sample_type + "+" + host;
        }
    }

    return package_key;
}

function resetFieldsAndDivs(package_key){
    // hide field_details_div, custom_fields_div, show no_package_warning_div
    $(getIdSelectorFromId(g_transferred_variables.ELEMENT_IDENTIFIERS.EXISTING_FIELDS_DIV)).addClass('hidden');
    $(getIdSelectorFromId(g_transferred_variables.ELEMENT_IDENTIFIERS.CUSTOM_FIELDS_DIV)).addClass('hidden');
    $(getIdSelectorFromId(g_transferred_variables.ELEMENT_IDENTIFIERS.NO_PACKAGE_WARNING_DIV)).removeClass('hidden');

    // clear field_names_sel, field_details_div, which contains the custom fields, and package_details_div
    $(getIdSelectorFromId(g_transferred_variables.ELEMENT_IDENTIFIERS.FIELD_NAMES_SELECT)).empty();
    $(getIdSelectorFromId(g_transferred_variables.ELEMENT_IDENTIFIERS.FIELD_DETAILS_DIV)).empty();
    $(getIdSelectorFromId(g_transferred_variables.ELEMENT_IDENTIFIERS.PACKAGE_DETAILS_DIV)).empty();
    // TODO: someday: remove hardcoding of div name
    $("#files").empty();

    // Reset variables tracking field information
    g_fields_state = new Fields();
    g_fields_state.package_key = package_key;
}

function ajax_err(request, error) {
    console.log(request);
    console.log(error);
}
function ajax_ok(data) {
    // Set the reserved words
    g_fields_state.setReservedWords(data["reserved_words"]);

    // Set the package field names
    var package_field_names_list = data["field_names"];
    g_fields_state.setPackageFields(package_field_names_list);

    var field_desc_dicts_list = data["field_descriptions"];
    var field_descs_html_pieces = [];
    for (var i = 0; i < field_desc_dicts_list.length; i++) {
        var curr_desc_dict = field_desc_dicts_list[i];
        var curr_desc_html = "<tr><td class='description-cell'>" + curr_desc_dict["name"]+
            "</td><td class='description-cell'>" + curr_desc_dict["description"] + "</td></tr>";
        field_descs_html_pieces.push(curr_desc_html);
    }
    var fields_message = "<br /><p>The following fields will be added to your metadata template:</p><table>" +
        field_descs_html_pieces.join("") +
        "</table><br /><strong>Note that none of these fields' names will be available for custom fields.</strong><br /><br />";
    $(getIdSelectorFromId("package_details_div")).html(fields_message);

    $(getIdSelectorFromId(g_transferred_variables.ELEMENT_IDENTIFIERS.NO_PACKAGE_WARNING_DIV)).addClass('hidden');
    $(getIdSelectorFromId(g_transferred_variables.ELEMENT_IDENTIFIERS.CUSTOM_FIELDS_DIV)).removeClass('hidden');
}