import metadata_wizard.metadata_wizard_settings as mws


def _get_field_type_to_schema_generator():
    return {
        mws.FieldTypes.Text.value: _generate_text_schema,
        mws.FieldTypes.Boolean.value: _generate_boolean_schema,
        mws.FieldTypes.Categorical.value: _generate_categorical_schema,
        mws.FieldTypes.Continuous.value: _generate_continuous_schema
    }


def _get_default_types_to_input_fields():
    return {
        mws.DefaultTypes.no_default.value: None,
        mws.DefaultTypes.boolean_default.value: mws.InputNames.boolean_default_select.value,
        mws.DefaultTypes.allowed_missing_default.value: mws.InputNames.allowed_missing_default_select.value,
        mws.DefaultTypes.categorical_default.value: mws.InputNames.categorical_default_select.value,
        mws.DefaultTypes.continuous_default.value: mws.InputNames.continuous_default.value,
        mws.DefaultTypes.text_default.value: mws.InputNames.text_default.value,
    }


def _get_special_handling_fields():
    return [mws.InputNames.field_name.value, mws.InputNames.field_type.value, mws.InputNames.allowed_missing_vals.value,
            mws.InputNames.default_value.value, mws.InputNames.allowed_missing_default_select.value,
            mws.InputNames.categorical_default_select.value, mws.InputNames.continuous_default.value,
            mws.InputNames.boolean_default_select.value, mws.InputNames.text_default.value,
            mws.InputNames.datetime_default.value, mws.InputNames.true_value.value, mws.InputNames.false_value.value,
            mws.InputNames.data_type.value, mws.InputNames.categorical_values.value, mws.InputNames.minimum_comparison.value,
            mws.InputNames.minimum_value.value, mws.InputNames.maximum_comparison.value, mws.InputNames.maximum_value.value,
            mws.InputNames.is_phi.value]

# def _get_cast_func_by_data_type():
#     return {mws.CerberusDataTypes.Text.value: str,
#             mws.CerberusDataTypes.Decimal.value: float,
#             mws.CerberusDataTypes.Integer.value: int,
#             mws.CerberusDataTypes.DateTime.value: _cast_date_time
#             }


def get_validation_schemas(curr_field_from_form, a_regex_handler):
    field_name_and_schema_tuples_list = []
    field_name, field_schema = _get_field_validation_schema(curr_field_from_form, a_regex_handler)

    mock_unit_field_form_dict = _mock_a_units_field_if_relevant(curr_field_from_form)
    if mock_unit_field_form_dict is not None:
        mock_unit_field_name, mock_unit_field_schema = _get_field_validation_schema(mock_unit_field_form_dict,
                                                                                    a_regex_handler)
        field_name_and_schema_tuples_list.append((mock_unit_field_name, mock_unit_field_schema))
        field_schema[mws.InputNames.units.value] = mock_unit_field_name

    field_name_and_schema_tuples_list.append((field_name, field_schema))
    return field_name_and_schema_tuples_list


def _get_field_validation_schema(curr_field_from_form, a_regex_handler):
    field_name = curr_field_from_form[mws.InputNames.field_name.value]
    top_level_schema = _build_top_level_schema_dict(curr_field_from_form)
    validation_schema = _build_single_validation_schema_dict(curr_field_from_form, a_regex_handler)

    allowed_missing_val_key = mws.InputNames.allowed_missing_vals.value
    if allowed_missing_val_key in curr_field_from_form:
        # NB: allowed_missing_vals is a fieldset of checkboxes, so it is indicated by its name plus a set of brackets
        allowed_missing_vals_from_form = curr_field_from_form[allowed_missing_val_key]
        # NB: allowed_missing_vals from form are the *names* of the ebi missing values (like "ebi_not_collected"
        # instead of "missing: not collected" because the punctuation/etc in the actual values causes some problems with
        # my jquery selectors.  Thus, it is necessary to convert them from name to value before use in validation schema
        allowed_missing_vals = [_convert_ebi_missing_name_to_ebi_missing_value(x) for x in
                                allowed_missing_vals_from_form]
        missings_schema = _generate_text_schema(None, a_regex_handler)
        missings_schema.update({
            mws.ValidationKeys.allowed.value: allowed_missing_vals
        })

        top_level_schema[mws.ValidationKeys.anyof.value] = \
            [missings_schema, validation_schema]
    else:
        top_level_schema.update(validation_schema)
    # end if any allowed missing vals

    top_level_schema = _set_default_keyval_if_any(curr_field_from_form, top_level_schema)
    return field_name, top_level_schema


def _mock_a_units_field_if_relevant(curr_field_from_form):
    result = None
    if mws.InputNames.units.value in curr_field_from_form:
        base_field_name = curr_field_from_form[mws.InputNames.field_name.value]
        units_string = curr_field_from_form[mws.InputNames.units.value]
        mock_field_name = base_field_name + mws.UNITS_SUFFIX

        result = {
            mws.InputNames.categorical_default_select.value: units_string,
            mws.InputNames.categorical_values.value: units_string,
            mws.InputNames.default_value.value: mws.DefaultTypes.categorical_default.value,
            mws.InputNames.field_name.value: mock_field_name,
            mws.InputNames.field_type.value: mws.FieldTypes.Categorical.value
        }

    return result


# So ... the schema indicates whether a field is phi, but Qiita can't actually read the schema,
# so the customer requests that if a field is marked as phi, then the suffix "_phi" is appended to
# the end of the field name.  I kind of hate rewriting the customer's inputs this way, so hopefully
# Qiita will be able to read the schema soon.  NB that I COULD change the field names when the schema
# is first generated, but I went with rewriting them afterwards on request so that I can retain a "clean"
# copy of the schema that has the original field names for output on the schema worksheet.
def rewrite_field_names_with_phi_if_relevant(schema_dict):
    result = {}
    for curr_field_name, curr_field_schema in schema_dict.items():
        new_field_name = curr_field_name
        if curr_field_schema[mws.InputNames.is_phi.value]:
            new_field_name = new_field_name + mws.PHI_SUFFIX
        result[new_field_name] = curr_field_schema
    return result


def _build_top_level_schema_dict(curr_field_from_form):
    top_level_schema = {mws.ValidationKeys.empty.value: False,
                        mws.ValidationKeys.required.value: True,
                        mws.InputNames.is_phi.value: mws.InputNames.is_phi.value in curr_field_from_form}

    for curr_key, curr_value in curr_field_from_form.items():
        if curr_key not in _get_special_handling_fields():
            top_level_schema.update({curr_key: curr_value})

    return top_level_schema


def _build_single_validation_schema_dict(curr_field_from_form, a_regex_handler):
    generator_funcs_by_type = _get_field_type_to_schema_generator()
    field_type = curr_field_from_form[mws.InputNames.field_type.value]
    schema_generator_func = generator_funcs_by_type[field_type]
    result = schema_generator_func(curr_field_from_form, a_regex_handler)
    return result


def _generate_text_schema(curr_field_from_form, a_regex_handler):
    return _generate_schema_by_data_type(
        curr_field_from_form, a_regex_handler,
        overriding_datatype=mws.CerberusDataTypes.Text.value)


def _generate_boolean_schema(curr_field_from_form, a_regex_handler):
    bool_true = curr_field_from_form[mws.InputNames.true_value.value]
    bool_false = curr_field_from_form[mws.InputNames.false_value.value]

    curr_schema = _generate_text_schema(curr_field_from_form, a_regex_handler)
    curr_schema.update({
        mws.ValidationKeys.allowed.value: [bool_true, bool_false]
    })
    return curr_schema


def _generate_datetime_schema(curr_field_from_form, a_regex_handler):
    return _generate_schema_by_data_type(
        curr_field_from_form, a_regex_handler,
        overriding_datatype=mws.CerberusDataTypes.DateTime.value)


def _generate_categorical_schema(curr_field_from_form, a_regex_handler):
    curr_schema = _generate_text_schema(curr_field_from_form, a_regex_handler)

    categorical_vals_str = curr_field_from_form[mws.InputNames.categorical_values.value]
    split_categorical_vals = categorical_vals_str.split("\r\n")
    split_categorical_vals = [x.strip() for x in split_categorical_vals]
    non_empty_split_categorical_values = [x for x in split_categorical_vals if x != ""]

    curr_schema.update({
        mws.ValidationKeys.allowed.value: non_empty_split_categorical_values
    })
    return curr_schema


def _generate_continuous_schema(curr_field_from_form, a_regex_handler):
    curr_schema = _generate_schema_by_data_type(curr_field_from_form, a_regex_handler)

    curr_schema = _set_comparison_keyval_if_any(curr_field_from_form,
                                                mws.InputNames.minimum_value.value,
                                                mws.InputNames.minimum_comparison.value, curr_schema)

    curr_schema = _set_comparison_keyval_if_any(curr_field_from_form,
                                                mws.InputNames.maximum_value.value,
                                                mws.InputNames.maximum_comparison.value, curr_schema)

    return curr_schema


def _generate_schema_by_data_type(curr_field_from_form, a_regex_handler, overriding_datatype=None):
    """

    :type a_regex_handler: regex_handler.RegexHandler
    """

    data_type = overriding_datatype if overriding_datatype else curr_field_from_form[mws.InputNames.data_type.value]
    curr_schema = {mws.ValidationKeys.type.value: data_type}

    regex_for_data_type = a_regex_handler.get_regex_val_by_name(data_type)
    if regex_for_data_type:
        curr_schema.update({
            mws.ValidationKeys.regex.value: regex_for_data_type
        })

    return curr_schema


def _set_default_keyval_if_any(curr_field_from_form, curr_schema):
    default_types_to_default_fields = _get_default_types_to_input_fields()
    default_type_value = curr_field_from_form[mws.InputNames.default_value.value]
    default_value_input_name = default_types_to_default_fields[default_type_value]
    if default_value_input_name is not None:
        default_val = curr_field_from_form[default_value_input_name]
        if default_val in [x.name for x in mws.EbiMissingValues]:
            default_val = _convert_ebi_missing_name_to_ebi_missing_value(default_val)
        curr_schema[mws.ValidationKeys.default.value] = default_val
    return curr_schema


def _set_comparison_keyval_if_any(curr_field_from_form, threshold_val_name, comparison_val_name, curr_schema):
    if threshold_val_name in curr_field_from_form:
        comparison_value = curr_field_from_form[threshold_val_name]
        comparison_key = curr_field_from_form[comparison_val_name]
        curr_schema.update({
            comparison_key: comparison_value
        })
    # end if there's a threshold value
    return curr_schema


def _convert_ebi_missing_name_to_ebi_missing_value(ebi_missing_name):
    return mws.EbiMissingValues[ebi_missing_name].value
