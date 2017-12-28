import collections

import scripts_server.metadata_wizard_settings as mws
import scripts_server.xlsx_basics as xlsxbasics
import scripts_server.xlsx_validation_builder as xvb


def write_metadata_grid(data_worksheet, schema_dict):
    """

    :type data_worksheet: xlsxbasics.MetadataWorksheet
    """

    _write_sample_id_col(data_worksheet)

    unlocked = xlsxbasics.make_format(data_worksheet.workbook, is_locked=False)
    # format as text to prevent autoformatting!
    unlocked_text = xlsxbasics.make_format(data_worksheet.workbook, {'num_format': '@'}, is_locked=False)

    sorted_keys = xlsxbasics.sort_keys(schema_dict)
    for field_index, field_name in enumerate(sorted_keys):
        field_specs_dict = schema_dict[field_name]
        curr_col_index = field_index + 1  # add one bc sample id is in first col

        xlsxbasics.write_header(data_worksheet, field_name, field_index + 1)
        curr_format = unlocked_text if _determine_if_format_should_be_text(field_specs_dict) else unlocked
        data_worksheet.worksheet.set_column(curr_col_index, curr_col_index, None, curr_format)

        col_range = xlsxbasics.format_range(curr_col_index, None)
        starting_cell_name = xlsxbasics.format_range(curr_col_index, data_worksheet.first_data_row_index)
        whole_col_range = xlsxbasics.format_range(curr_col_index, data_worksheet.first_data_row_index,
                                                   last_row_index=data_worksheet.last_allowable_row_for_sample_index)

        validation_dict = _get_validation_dict(field_name, field_specs_dict, data_worksheet.regex_handler)
        value_key = "value"
        if validation_dict is not None:
            if value_key in validation_dict:
                unformatted_validation_formula = validation_dict[value_key]
                formatted_validation_formula = unformatted_validation_formula.format(
                    cell=starting_cell_name, col_range=col_range)
                validation_dict[value_key] = formatted_validation_formula

            validation_return_code = data_worksheet.worksheet.data_validation(whole_col_range, validation_dict)
            # NB: xlsxwriter's data_validation docstring *claims* it returns 0 if it succeeds, but in fact if it
            # succeeds it doesn't return an error code at all, hence the then None check ...
            if validation_return_code is not None and validation_return_code < 0:
                raise ValueError("Worksheet validation failed with return code '{0}'; check user warnings.".format(
                    validation_return_code
                ))

        _add_default_if_any(data_worksheet, field_specs_dict, curr_col_index)

        max_samples_msg = "No more than {0} samples can be entered in this worksheet.  If you need to submit metadata" \
                          " for >{0} samples, please contact CMI directly.".format(data_worksheet.num_allowable_samples)
        xlsxbasics.write_header(data_worksheet, max_samples_msg, data_worksheet.first_data_col_index,
                                 data_worksheet.last_allowable_row_for_sample_index + 1)


def _write_sample_id_col(data_sheet):
    """

    :type data_sheet: xlsxbasics.MetadataWorksheet
    """

    data_sheet.worksheet.set_column(data_sheet.sample_id_col_index, data_sheet.sample_id_col_index, None, None,
                                    data_sheet.hidden_cell_setting)
    xlsxbasics.write_header(data_sheet, "sample_id", data_sheet.sample_id_col_index)

    # +1 bc range is exclusive of last number
    for row_index in range(data_sheet.first_data_row_index, data_sheet.last_allowable_row_for_sample_index + 1):
        curr_cell = xlsxbasics.format_range(data_sheet.sample_id_col_index, row_index)
        id_num = row_index - data_sheet.first_data_row_index + 1
        data_row_range = xlsxbasics.format_single_data_grid_row_range(data_sheet, row_index)

        completed_formula = "=IF(COUNTBLANK({data_row_range})<>COLUMNS({data_row_range}),{id_num},\"\")".format(
            data_row_range=data_row_range, id_num=id_num)
        data_sheet.worksheet.write_formula(curr_cell, completed_formula)


def _get_validation_dict(field_name, field_schema_dict, a_regex_handler):
    result = None
    validation_generators = [
        _make_allowed_only_constraint,
        _make_formula_constraint
    ]

    for curr_generator in validation_generators:
        curr_validation_dict = curr_generator(field_name, field_schema_dict, a_regex_handler)
        if curr_validation_dict is not None:
            result = curr_validation_dict
            break
        # end if validation generated
    # next validation generator

    return result


def _make_allowed_only_constraint(field_name, field_schema_dict, a_regex_handler):
    result = None
    allowed_onlies = xvb.roll_up_allowed_onlies(field_schema_dict, a_regex_handler)

    if allowed_onlies is not None and len(allowed_onlies) > 0:
        allowed_onlies_as_strs = [str(x) for x in allowed_onlies]

        # See line 1810 in xlsxwriter's worksheet.py: the comma-delimited list of options for a list validation can
        # be no more than 255 characters long, per an Excel limitation :(  If list is longer than that, have to fall
        # back and use a formula validation.
        joined_allowed_str = ','.join(allowed_onlies_as_strs)
        if len(joined_allowed_str) <= 255:
            message = xvb.get_field_constraint_description(field_schema_dict, a_regex_handler)
            # 'The value must be one of the following: {1}'.format(field_name, ", ".join(allowed_onlies_as_strs))
            result = _make_base_validate_dict(field_name, message)
            result.update({
                'validate': 'list',
                'source': allowed_onlies
            })

    return result


def _make_formula_constraint(field_name, field_schema_dict, a_regex_handler):
    result = None

    formula_string = xvb.get_formula_constraint(field_schema_dict, a_regex_handler)
    message = xvb.get_field_constraint_description(field_schema_dict, a_regex_handler)

    if formula_string is not None:
        formula_string = "=("+formula_string + ")"
        result = _make_base_validate_dict(field_name, message)
        result.update({
            'validate': 'custom',
            'value': formula_string
        })

    return result


def _make_base_validate_dict(field_name, message):
    input_title_prefix = 'Enter '
    error_title_prefix = 'Invalid '

    def munge_title(field_name, prefix):
        title_len_limit = 32
        usable_title_len = title_len_limit - len(prefix)
        usable_name = "value" if len(field_name) > usable_title_len else field_name
        return prefix + usable_name

    def munge_msg(field_name, message, add_error_prefix):
        msg_len_limit = 255
        prefix = "The {0} value entered is not valid. ".format(field_name) if add_error_prefix else ""
        result = prefix + message

        if len(result) > msg_len_limit:
            placeholder_msg = "[text truncated: please refer to field descriptions sheet for full requirements]."
            usable_len = msg_len_limit - len(placeholder_msg)
            result = result[:usable_len] + placeholder_msg

        return result

    return {
              'input_title': munge_title(field_name, input_title_prefix),
              'input_message': munge_msg(field_name, message, add_error_prefix=False),
              'error_title': munge_title(field_name, error_title_prefix),
              'error_message': munge_msg(field_name, message, add_error_prefix=True)
              }


def _add_default_if_any(data_worksheet, field_specs_dict, col_index):
    """

    :type data_worksheet: xlsxbasics.MetadataWorksheet
    """

    # So, you might be thinking: why don't we look at the sample_id column rather than the first visible metadata column
    # to determine if the user has entered anything for this sample?  After all, the sample_id is filled if ANY
    # column has something in it. Yes, but therein lies the problem: the sample_id is filled if there is anything in
    # the first visible metadata column (among others), so it *depends on* every visible metadata column--which means
    # that if the first visible metadata column in turn depends on the sample_id column, then we have a circular
    # reference.  Filling defaults only when the first visible metadata column is filled is not ideal, but should still
    # serve the need since the first visible column is a sensible place for people to start filling things in and
    # b) Austin says that sample_name, which will be always be required for every sample, is supposed to be the
    # first column always.
    trigger_col_letter = xlsxbasics.get_col_letters(data_worksheet.first_data_col_index)

    partial_default_formula = xvb.get_default_formula(field_specs_dict, trigger_col_letter)
    if partial_default_formula is not None:
        xlsxbasics.copy_formula_throughout_range(data_worksheet.worksheet, partial_default_formula, col_index,
                                                  data_worksheet.first_data_row_index,
                                                  last_row_index=data_worksheet.last_allowable_row_for_sample_index,
                                                  cell_format=None)


def _determine_if_format_should_be_text(field_specs_dict):
    result = True  # by default, assume format should be text

    data_type_vals = _apply_func_to_nested_dict_vals(
        field_specs_dict, lambda x: _find_val_for_key(x, mws.ValidationKeys.type.value))
    if mws.CerberusDataTypes.Integer.value in data_type_vals or mws.CerberusDataTypes.Decimal.value in data_type_vals:
        # in these cases, format needs to remain General
        result = False

    return result


def _find_val_for_key(a_dict, a_key):
    result = []
    if a_key in a_dict:
        result.append(a_dict[a_key])
    return result


def _apply_func_to_nested_dict_vals(a_val, func_to_apply):
    result = []

    if hasattr(a_val, 'items'):
        result.extend(func_to_apply(a_val))

        for curr_key, curr_val in a_val.items():
            result.extend(_apply_func_to_nested_dict_vals(curr_val, func_to_apply))
    else:
        # see https://stackoverflow.com/a/6711233 on why this type-checking is kosher.
        # using str instead of basestring because later is not in python 3
        if isinstance(a_val, collections.Iterable) and not isinstance(a_val, str):
            for curr_item in a_val:
                result.extend(_apply_func_to_nested_dict_vals(curr_item, func_to_apply))

    return result
