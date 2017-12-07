// TODO: Refactor to pull from back-end
var HOST_ASSOCIATED_SAMPLE_TYPES = [
    "stool",
    "mucus"
];

function onModeChange(element){
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

function onSampleTypeChange(element){
    var div_to_display = "environmental_div";
    var div_to_hide = "host_associated_div";
    var selected_sample_type = element.value;
    if(jQuery.inArray(selected_sample_type, HOST_ASSOCIATED_SAMPLE_TYPES) !== -1){
        var temp = div_to_display;
        div_to_display = div_to_hide;
        div_to_hide = temp;
    }

    var hide_div_id_selector = getIdSelectorFromId(div_to_hide);
    showEnableOrHideDisable(hide_div_id_selector, false);
    var display_div_id_selector = getIdSelectorFromId(div_to_display);
    showEnableOrHideDisable(display_div_id_selector, true);

    checkSampleTypePlusHostImplications(element);
}

function checkSampleTypePlusHostImplications(element){
    // TODO: Refactor to pull from back-end
    var host_sites_by_host_and_sample_type = {
        "mucus+human": new HostSites("mucus", "human", [["human_vaginal","Human Vagina"], ["human_nasal","Human Nose"]], true, true, ""),
        "stool+human": new HostSites("stool", "human", [["human_fecal","Human Feces"]], false, false, "human_fecal"),
        "mucus+mouse": new HostSites("mucus", "mouse", [["mouse_vaginal","Mouse Vagina"], ["mouse_nasal","Mouse Snout"]], true, true, "")
    };

    // get value of sample type
    var sample_type_select_id_selector = getIdSelectorFromId("sample_type_select");
    var sample_type_val = $(sample_type_select_id_selector).val();

    // get value of host, munge to sample type for potential key
    var host_select_id_selector = getIdSelectorFromId("host_select");
    var host_value = $(host_select_id_selector).val();
    var potential_key = sample_type_val + "+" + host_value;

    var host_site_select_id_selector = getIdSelectorFromId("host_sample_site_select");
    var show_host_site_select = false;
    if (potential_key in host_sites_by_host_and_sample_type) {
        show_host_site_select = true;
        var curr_hostsite = host_sites_by_host_and_sample_type[potential_key];
        updateSelectWithNewCategories(host_site_select_id_selector, curr_hostsite.getSitesList(),
            curr_hostsite.selected_item, curr_hostsite.has_placeholder, true, false, true);
    }

    showEnableOrHideDisable(getIdSelectorFromId("host_specific_sample_type_div"), show_host_site_select);
    enableOrDisableBySelectorAndValue(host_site_select_id_selector, show_host_site_select, true)
}

function HostSites(sample_type, host, sites_list, has_placeholder, has_other, selected_item){
    this.sample_type = sample_type;
    this.host = host;
    this.raw_sites_list= sites_list;
    this.has_placeholder = has_placeholder;
    this.has_other = has_other;
    this.selected_item = selected_item;

    this.getSitesList = function(){
        var sitesList = [];
        for (var i = 0, len = this.raw_sites_list.length; i < len; i++){
            var curr_item = this.raw_sites_list[i];
            var new_item = curr_item;
            if (!(curr_item instanceof Array)){
                new_item = [curr_item, curr_item];
            }
            sitesList.push(new_item)
        }
        if (this.has_other){
            sitesList.push(["other","Other"]);
        }
        return sitesList;
    }
}

function getPackage(){
    // TODO: Would be nice to do nothing if they are "changing" the package to what it already is ...
    // If any custom fields have been added, warn the user they will be cleared by replacing the package
    if (next_field_num > 0) {
        var confirm_msg = "Changing the package selection will remove all custom fields.  Clear existing custom fields and change package?";
        if (!confirm(confirm_msg)) {
            return; //do nothing if they fail to confirm
        }
    }

    // hide field_details_div, custom_fields_div, show no_package_warning_div
    $(getIdSelectorFromId(SpecialInputs.EXISTING_FIELDS_DIV)).addClass('hidden');
    $(getIdSelectorFromId(SpecialInputs.CUSTOM_FIELDS_DIV)).addClass('hidden');
    $(getIdSelectorFromId(SpecialInputs.NO_PACKAGE_WARNING_DIV)).removeClass('hidden');

    // clear field_names_sel, field_details_div, which contains the custom fields, and package_details_div
    $(getIdSelectorFromId(SpecialInputs.FIELD_NAMES_SELECT)).empty();
    $(getIdSelectorFromId(SpecialInputs.FIELD_DETAILS_DIV)).empty();
    $(getIdSelectorFromId(SpecialInputs.PACKAGE_DETAILS_DIV)).empty();

    // TODO: Also need to clear out the list of uploaded files

    // Reset variables tracking package and custom fields
    package_fields = {};
    existing_field_names = {};
    next_field_num = 0;

    var package_key = null;
    // get the "power user" value--the precise, organism-specific package to use
    var package_select_id_selector = getIdSelectorFromId("package_select");

    // get the precise, organism-specific package to use specified through the wizard
    var host_sample_site_select_id_selector = getIdSelectorFromId("host_sample_site_select");

    if (!$(package_select_id_selector).is(':disabled')) {
        // if the power user value is not disabled, use it
        package_key = $(package_select_id_selector).val();
    } else if (!$(host_sample_site_select_id_selector).is(':disabled')) {
        // if the precise, organism-specific package to use specified through the wizard is not disabled, use it
        package_key = $(host_sample_site_select_id_selector).val();
    } else {
        // get the host type and the sample type and paste them together to get the package name to look for
        var host = $(getIdSelectorFromId("host_select")).val();
        var sample_type = $(getIdSelectorFromId("sample_type_select")).val();
        package_key = host + "_" + sample_type;
    }

    var r = {
        url : '/package',
        type : 'POST',
        data : package_key,
        dataType: 'text',
        success : ajax_ok,
        error: ajax_err
    };
    $.ajax(r);
}

function ajax_err(request, error) {
    console.log(request);
    console.log(error);
}
function ajax_ok(data) {
    var fields_message = "<br />The following fields will be added to your metadata template: " +  data +
        ".<br /><strong>Note that none of these names will be available for custom fields.</strong><br /><br />";
    $(getIdSelectorFromId("package_details_div")).html(fields_message);

    var fields_list = data.split(", ");
    var temp_package_fields = {};
    for (var i = 0, len = fields_list.length; i < len; i++) {
        temp_package_fields[fields_list[i]] = true;
    }

    package_fields = $.extend({}, temp_package_fields);
    existing_field_names = $.extend({}, package_fields);

    $(getIdSelectorFromId(SpecialInputs.NO_PACKAGE_WARNING_DIV)).addClass('hidden');
    $(getIdSelectorFromId(SpecialInputs.CUSTOM_FIELDS_DIV)).removeClass('hidden');
}