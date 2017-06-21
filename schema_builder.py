from enum import Enum

import metadata_package_schema_builder


class InputNames(Enum):
    study_name = "study_name"
    field_name = "field_name"
    field_type = "field_type"
    allowed_missing_vals = "allowed_missing_vals[]"
    default_value = "default_value"
    allowed_missing_default_select = "allowed_missing_default_select"
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


class FieldTypes(Enum):
    boolean = "boolean"
    text = "str"
    categorical = "categorical"
    continuous = "continuous"


class DefaultTypes(Enum):
    no_default = "no_default"
    boolean_default = "boolean_default"
    allowed_missing_default = "allowed_missing_default"
    categorical_default = "categorical_default"
    continuous_default = "continuous_default"


class ComparisonTypes(Enum):
    greater_than = "greater_than"
    greater_than_or_equal_to = "greater_than_or_equal_to"
    less_than = "less_than"
    less_than_or_equal_to = "less_than_or_equal_to"


def _get_field_type_to_schema_generator():
    return {
        FieldTypes.text.value: _generate_text_schema,
        FieldTypes.boolean.value: _generate_boolean_schema,
        FieldTypes.categorical.value: _generate_categorical_schema,
        FieldTypes.continuous.value: _generate_continuous_schema
    }


def _get_default_types_to_input_fields():
    return {
        DefaultTypes.no_default.value: None,
        DefaultTypes.boolean_default.value: InputNames.boolean_default_select.value,
        DefaultTypes.allowed_missing_default.value: InputNames.allowed_missing_default_select.value,
        DefaultTypes.categorical_default.value: InputNames.categorical_default_select.value,
        DefaultTypes.continuous_default.value: InputNames.continuous_default.value
    }


def _get_comparison_type_to_validation_comparison_key():
    return {
        ComparisonTypes.greater_than.value: metadata_package_schema_builder.ValidationKeys.max_exclusive.value,
        ComparisonTypes.greater_than_or_equal_to.value: metadata_package_schema_builder.ValidationKeys.max_inclusive.value,
        ComparisonTypes.less_than.value: metadata_package_schema_builder.ValidationKeys.min_exclusive.value,
        ComparisonTypes.less_than_or_equal_to.value: metadata_package_schema_builder.ValidationKeys.min_exclusive.value
    }


def get_validation_schema(curr_field_from_form):
    field_name = curr_field_from_form[InputNames.field_name.value]
    validation_schema = _build_single_validation_schema_dict(curr_field_from_form)

    if InputNames.allowed_missing_vals.value in curr_field_from_form:
        allowed_missing_vals = curr_field_from_form[InputNames.allowed_missing_vals.value]
        curr_schema = {}
        missings_schema = {
            metadata_package_schema_builder.ValidationKeys.type.value: metadata_package_schema_builder.CerberusDataTypes.string.value,
            metadata_package_schema_builder.ValidationKeys.allowed.value: allowed_missing_vals,
            metadata_package_schema_builder.ValidationKeys.empty.value: False,
            metadata_package_schema_builder.ValidationKeys.required.value: True
        }

        missings_schema = _set_default_keyval_if_any(curr_field_from_form, missings_schema)
        curr_schema[metadata_package_schema_builder.ValidationKeys.anyof.value] = [missings_schema, validation_schema]
    else:
        curr_schema = validation_schema
        curr_schema = _set_default_keyval_if_any(curr_field_from_form, curr_schema)
    # end if any allowed missing vals

    return field_name, curr_schema


def _build_single_validation_schema_dict(curr_field_from_form):
    generator_funcs_by_type = _get_field_type_to_schema_generator()
    field_type = curr_field_from_form[InputNames.field_type.value]
    schema_generator_func = generator_funcs_by_type[field_type]
    result = schema_generator_func(curr_field_from_form)
    return result


def _generate_text_schema(curr_field_from_form):
    return {
        metadata_package_schema_builder.ValidationKeys.type.value: metadata_package_schema_builder.CerberusDataTypes.string.value,
        metadata_package_schema_builder.ValidationKeys.required.value: True
    }


def _generate_boolean_schema(curr_field_from_form):
    bool_true = curr_field_from_form[InputNames.true_value.value]
    bool_false = curr_field_from_form[InputNames.false_value.value]

    curr_schema = {
        metadata_package_schema_builder.ValidationKeys.type.value: metadata_package_schema_builder.CerberusDataTypes.string.value,
        metadata_package_schema_builder.ValidationKeys.required.value: True,
        metadata_package_schema_builder.ValidationKeys.allowed.value: [bool_true, bool_false],
        metadata_package_schema_builder.ValidationKeys.empty.value: False,
    }
    return curr_schema


def _generate_categorical_schema(curr_field_from_form):
        data_type = curr_field_from_form[InputNames.data_type.value]
        validation_data_type = data_type
        if data_type == "float": validation_data_type = "number"
        func_by_type_str = {"str": str,
                            "float": float,
                            "integer": int}
        curr_schema = {
            metadata_package_schema_builder.ValidationKeys.type.value: validation_data_type,
            metadata_package_schema_builder.ValidationKeys.required.value: True
        }

        categorical_vals_str = curr_field_from_form[InputNames.categorical_values.value]
        split_categorical_vals = categorical_vals_str.split("\r\n")
        split_categorical_vals = [x.strip() for x in split_categorical_vals]

        typed_categorical_vals = [func_by_type_str[data_type](x) for x in split_categorical_vals]

        curr_schema.update({
            metadata_package_schema_builder.ValidationKeys.allowed.value: typed_categorical_vals,
            metadata_package_schema_builder.ValidationKeys.empty.value: False,
        })
        return curr_schema


def _generate_continuous_schema(curr_field_from_form):
    data_type = curr_field_from_form[InputNames.data_type.value]
    validation_data_type = data_type
    if data_type == "float": validation_data_type = "number"
    func_by_type_str = {"str": str,
                        "float": float,
                        "integer": int}
    curr_schema = {
        metadata_package_schema_builder.ValidationKeys.type.value: validation_data_type,
        metadata_package_schema_builder.ValidationKeys.required.value: True
    }

    curr_schema = _set_comparison_keyval_if_any(curr_field_from_form,
                                                InputNames.minimum_value.value,
                                                InputNames.minimum_comparison.value, curr_schema)

    curr_schema = _set_comparison_keyval_if_any(curr_field_from_form,
                                                InputNames.maximum_value.value,
                                                InputNames.maximum_comparison.value, curr_schema)

    return curr_schema


def _set_default_keyval_if_any(curr_field_from_form, curr_schema):
    default_types_to_default_fields = _get_default_types_to_input_fields()
    default_type_value = curr_field_from_form[InputNames.default_value.value]
    default_value_input_name = default_types_to_default_fields[default_type_value]
    if default_value_input_name is not None:
        curr_schema[metadata_package_schema_builder.ValidationKeys.default.value] = curr_field_from_form[default_value_input_name]
    return curr_schema


def _set_comparison_keyval_if_any(curr_field_from_form, threshold_val_name, comparison_val_name, curr_schema):
    comparison_types_to_keys = _get_comparison_type_to_validation_comparison_key()
    if threshold_val_name in curr_field_from_form:
        comparison_value = curr_field_from_form[threshold_val_name]
        comparison_type = curr_field_from_form[comparison_val_name]
        comparison_key = comparison_types_to_keys[comparison_type]
        curr_schema.update({
            comparison_key: comparison_value
        })
    # end if there's a threshold value
    return curr_schema

