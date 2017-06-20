from enum import Enum

import package_schemas

class RecognizedKeys(Enum):
    study_name = "study_name"
    field_name = "field_name"
    field_type = "field_type"
    allowed_missing_vals = "allowed_missing_vals[]"
    default_value = "default_value"
    allowed_missing_default = "allowed_missing_default"
    categorical_default_select = "categorical_default_select"
    continuous_default = "continuous_default"
    boolean_default_select = "boolean_default_select"
    true_value = "true_value"
    false_value = "false_value"
    data_type = "data_type"
    categorical_values = "categorical_values"
    minimum_comparison = "minimum_comparison"
    minimum_value = "minimum_value"
    maximum_comparison = "maximum_comparison"
    maximum_value = "maximum_value"
    units = "units"


def get_validation_schema(curr_field_from_form):
    field_name = curr_field_from_form[RecognizedKeys.field_name.name]
    validation_schema = build_single_validation_schema_dict(curr_field_from_form)

    # TODO: fix hard-code
    if "allowed_missing_vals[]" in curr_field_from_form:
        allowed_missing_vals = curr_field_from_form["allowed_missing_vals[]"]
        curr_schema = {}
        missings_schema = {
            package_schemas.atype: package_schemas.astring,
            package_schemas.allowed: allowed_missing_vals,
            package_schemas.empty: False,
            package_schemas.required: True
        }

        default_val = curr_field_from_form[RecognizedKeys.default_value.name]
        if default_val == "allowed_missing_default":  # TODO: pull out string into symbolic constant
            missings_schema[package_schemas.default] = curr_field_from_form[RecognizedKeys.allowed_missing_default.name]
            # end if allowed missing default

        curr_schema[package_schemas.anyof] = [missings_schema, validation_schema]
    else:
        curr_schema = validation_schema
    # end if any allowed missing vals

    return field_name, curr_schema


def build_single_validation_schema_dict(curr_field_from_form):
    curr_schema = None

    # get the field type
    field_type = curr_field_from_form[RecognizedKeys.field_type.name]
    if field_type == "boolean":
        bool_true = curr_field_from_form[RecognizedKeys.true_value.name]
        bool_false = curr_field_from_form[RecognizedKeys.false_value.name]

        curr_schema =  {
            package_schemas.atype: package_schemas.astring,
            package_schemas.allowed: [bool_true, bool_false],
            package_schemas.empty: False,
            package_schemas.required: True
        }

        default_val = curr_field_from_form[RecognizedKeys.default_value.name]
        if default_val == "boolean_default_value":
            curr_schema[package_schemas.default] = curr_field_from_form[RecognizedKeys.boolean_default_select.name]
        # end if boolean default
    elif field_type == "text":
        curr_schema = {
            package_schemas.atype: package_schemas.astring,
            package_schemas.required: True
        }

        # TODO: currently no default option for free form text
    elif field_type == "categorical":
        categorical_vals_str = curr_field_from_form[RecognizedKeys.categorical_values.name]
        split_categorical_vals = categorical_vals_str.split("\r\n")
        split_categorical_vals = [x.strip() for x in split_categorical_vals]

        data_type = curr_field_from_form[RecognizedKeys.data_type.name]
        validation_data_type = data_type
        if data_type == "float": validation_data_type = "number"

        # TODO: clean up cast to data type
        func_by_type_str = {"str": str,
                            "float": float,
                            "integer": int}
        typed_categorical_vals = [func_by_type_str[data_type](x) for x in split_categorical_vals]

        curr_schema = {
            package_schemas.atype: validation_data_type,
            package_schemas.allowed: typed_categorical_vals,
            package_schemas.empty: False,
            package_schemas.required: True
        }

        default_val = curr_field_from_form[RecognizedKeys.default_value.name]
        if default_val == "categorical_default":
            curr_schema[package_schemas.default] = curr_field_from_form[RecognizedKeys.categorical_default_select.name]
        # end if categorical default
    # elif continuous
        # get data_type
        # add to current schema {
            # atype: data_type,
            # required: True
        # }

        # if default_value = "continuous_default"
            # add "default: " +  continuous_default
        # end if boolean default

        # if minimum_value:
            # add "min": + minimum_value
        # end if minimum_value

        # TODO: figure out min comparison in Cerberus

        # if maximum_value:
            # add "max": + maximum_value
        # end if maximum_value

        # TODO: figure out max comparison in Cerberus
    # else:
        # throw valueerror for unrecognized type
    # end if

    # TODO: Ask Gail/Austin: how to handle units, if at all?

    return curr_schema
