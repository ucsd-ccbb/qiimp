$.validator.setDefaults({
    submitHandler: function() {
        alert("submitted!");
    }
});


var SpecialInputs;
SpecialInputs = {
    FIELD_NAME: "field_name",
    FIELD_TYPE: "field_type",
    TRUE_VALUE: "true_value",
    FALSE_VALUE: "false_value",
    MINIMUM: "minimum_value",
    MIN_COMPARE: "minimum_comparison"

};

function getIdFromBaseNameAndFieldIndex(base_name, field_index) {
    return base_name + "_" + field_index;
}

function getIdSelectorFromId(id_str) {
    return "#" + id_str;
}

function getIdSelectorFromBaseNameAndFieldIndex(base_name, field_index) {
    var id = getIdFromBaseNameAndFieldIndex(base_name, field_index);
    return getIdSelectorFromId(id);
}

function doesElementHaveValue(base_name, field_index) {
    var result = true; //default
    var element_id = getIdSelectorFromBaseNameAndFieldIndex(SpecialInputs.MINIMUM, field_index);
    var element_val = $(element_id)[0].value;
    // see https://stackoverflow.com/a/1854584
    if (!($.trim(element_val)).length) {result = false;}
    return result;
}

function decorateNewElements() {
    var newest_field_index = getCurrNumFields() - 1;

    var required_field_base_names = [SpecialInputs.FIELD_NAME, SpecialInputs.FIELD_TYPE,
        SpecialInputs.TRUE_VALUE, SpecialInputs.FALSE_VALUE];

    for (i=0, len = required_field_base_names.length; i < len; i++) {
        var curr_base_name = required_field_base_names[i];
        var curr_id_selector = getIdSelectorFromBaseNameAndFieldIndex(curr_base_name, newest_field_index);
        $(curr_id_selector).rules("add", {
           required: true
        });
    }

    var fld_type = SpecialInputs.FIELD_TYPE;
    var min_compare = SpecialInputs.MIN_COMPARE;
    var functions_by_element_name = {
         fld_type: function(field_index) {
             var id_selector = getIdSelectorFromBaseNameAndFieldIndex(SpecialInputs.FIELD_TYPE,
                     newest_field_index);
             //$( "form" ).on("change", "#"+revised_id, {field_index:field_index}, displayFieldDetails);
             $(id_selector).on("change", {field_index:field_index}, displayFieldDetails)
         },
        min_compare: function (field_index) {
            var id_selector = getIdSelectorFromBaseNameAndFieldIndex(SpecialInputs.MIN_COMPARE,
                     newest_field_index);
            $(id_selector).rules("add", {
                required: function() {
                    return doesElementHaveValue(SpecialInputs.MINIMUM, newest_field_index);
                }
            });
        }
    };

    for (var curr_key in functions_by_element_name) {
        functions_by_element_name[curr_key](newest_field_index);
    }
}

function GenericField(field_index) {
    this.generateHtml = function ($html) {
        var template_suffix = "_template";
        var template_id_objects = $("[id$="+template_suffix+"]");
        for (var i = 0, len = template_id_objects.length; i < len; i++) {
            var curr_element_name = template_id_objects[i].id.replace(template_suffix, "");
            var curr_new_id = renameTemplateId($html, curr_element_name, field_index);
            if (!curr_element_name.endsWith("_div")) {
                var curr_new_name = getNameFromRootAndIndex(curr_element_name, field_index);
                $html.find("#"+curr_new_id)[0].name = curr_new_name;
            }
        }

        return $html.html();
    }
}

function makeInputRequired($html, base_name, field_index) {
    var new_id = getIdFromTemplateAndIndex(base_name, field_index);
    var curr_element = $html.find("#"+new_id);
    //var new_name = getNameFromRootAndIndex(base_name, field_index);
    //var curr_element = $('input[name="'+ new_name + '"]');
    curr_element.rules("add", {
        required: true
    });
    // return new_name;
}

function getNameFromRootAndIndex(root_name, field_index) {
    //return "field["+ field_index.toString() + "]["+ root_name + "]";
    return root_name + "_" + field_index;
}

function getIdFromTemplateAndIndex(element_name, field_index) {
    var template_suffix = "template";
    var full_template_name = element_name + "_" + template_suffix;
    var new_id = full_template_name.replace(template_suffix, field_index.toString());
    return new_id;
}

function renameTemplateId($html, template_name, field_index) {
    //debugger;
    var template_suffix = "template";
    var full_template_name = template_name + "_" + template_suffix;
    var new_id = getIdFromTemplateAndIndex(template_name, field_index);
    $html.find("#"+full_template_name).prop('id', new_id);
    return new_id;
}

function getCurrNumFields() {
    return $('.field').length;
}

function generateFieldHtml() {
    var len = getCurrNumFields();
    var $html = $('.fieldTemplate').clone();

    var new_field = new GenericField(len);
    var new_html = new_field.generateHtml($html);

    //console.log(new_html);
    return new_html;
}

function displayFieldDetails(event) {
    var fields_to_show_by_field_type = {
        "":[],
        "text":[],
        "boolean": ["field_details_div","boolean_true_div", "boolean_false_div", "boolean_default", "boolean_default_label"],
        "continuous": ["field_details_div","data_type_div", "minimum_div", "maximum_div", "units_div", "continuous_default", "continuous_default_label"],
        "categorical": ["field_details_div","data_type_div", "categorical_div", "units_div", "categorical_default", "categorical_default_label"]
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

        //debugger;
        if (!do_show)  {
            $(curr_setting_selector).addClass('hidden');
        } else {
            $(curr_setting_selector).removeClass('hidden');
            //$(curr_setting_selector).slideDown();
        }
    }
}

// Code to run as soon code as the document is ready to be manipulated
$(document).ready(function () {
    $("#metadata_form").validate({
        rules: {
                study_name: {
                    required: true
                }
            }
        });

    // Get the html from template and add the first item to the container
    //debugger;
    var new_html = $('<div/>', {
        'class' : 'row field', html: generateFieldHtml()
    });
    new_html.appendTo('#container');
    decorateNewElements();

    // When someone clicks to add a row, add new hidden html to
    // the container and then slide down slowly
    $('#addRow').click(function () {
        $('<div/>', {
            'class' : 'field', html: generateFieldHtml()
        }).hide().appendTo('#container').slideDown('slow');

        decorateNewElements();
    });
});
