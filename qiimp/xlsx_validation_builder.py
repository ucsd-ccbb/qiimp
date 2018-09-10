import datetime

import qiimp.metadata_wizard_settings as mws

text_placeholder = "value"
cell_placeholder = "{cell}"
col_range_placeholder = "{col_range}"
# NB: these formats are ALSO defined (in the format syntax of moment.js,
# which is different than the format syntax of python) in metadataWizard.js .
# If changed/added to in one place, the analogous action must be taken in the
# other place as well.
# Also note that some formats require special handling in _make_date_constraint
# so if adding formats here, be sure to see if they need to be added there too.
datetime_formats = ["%Y", "%Y-%m", "%Y-%m-%d", "%Y-%m-%d %H",
                    "%Y-%m-%d %H:%M", "%Y-%m-%d %H:%M:%S", "%H:%M", "%H:%M:%S"]


def roll_up_allowed_onlies(field_schema_dict, a_regex_handler):
    all_allowed_vals = []
    if mws.ValidationKeys.anyof.value in field_schema_dict:
        anyof_subschemas = field_schema_dict[mws.ValidationKeys.anyof.value]
        for curr_anyof_subschema in anyof_subschemas:
            subschema_allowed_vals = roll_up_allowed_onlies(curr_anyof_subschema, a_regex_handler)
            if subschema_allowed_vals is None:
                return None
            else:
                all_allowed_vals.extend(subschema_allowed_vals)
            # end check of constraints in this subschema
        # next subschema
    # end if there are subschemas

    if mws.ValidationKeys.allowed.value in field_schema_dict:
        curr_allowed_vals = field_schema_dict[mws.ValidationKeys.allowed.value]
        all_allowed_vals.extend(curr_allowed_vals)
    else:
        curr_formula_constraint = _get_single_level_formula_constraint(field_schema_dict, a_regex_handler)
        if curr_formula_constraint is not None:
            return None

    return all_allowed_vals


def get_formula_constraint(field_schema_dict, a_regex_handler, field_data_type=None, make_text=False):
    and_constraints = []

    # get the sub-constraints (anyof)
    curr_level_type = _get_field_data_type(field_schema_dict)
    if curr_level_type is not None: field_data_type = curr_level_type
    or_sub_constraints = _make_anyof_constraint(field_schema_dict, a_regex_handler, field_data_type,
                                                make_text=make_text)
    if or_sub_constraints is not None: and_constraints.append(or_sub_constraints)

    # get the constraints from this level
    level_constraints = _get_single_level_formula_constraint(field_schema_dict, a_regex_handler, field_data_type,
                                                             make_text=make_text)
    if level_constraints is not None: and_constraints.append(level_constraints)

    # make an 'and' clause for the constraints
    and_constraint_clause = _make_logical_constraint(and_constraints, True, make_text=make_text)
    return and_constraint_clause


def get_default_formula(field_schema_dict, trigger_col_letter, make_text=False):
    result = None

    # default is only filled in if user has put something into a trigger column, to avoid confusing them by having
    # entries in rows that they haven't even thought about yet.
    if mws.ValidationKeys.default.value in field_schema_dict:
        default_val = field_schema_dict[mws.ValidationKeys.default.value]
        if make_text:
            result = "The default value is {0}".format(default_val)
        else:
            # at this point I don't need the field type of the field but rather the data type of the *default* value:
            # for example, a field with the data type integer could nonetheless have a *string* default of
            # not provided, and that value would need to be written in as a string with quotes around it.

            data_type_of_default = None
            # NB: Per check in _get_data_types_and_allowed_vals, there may not be more than 2 options in this list.
            # Also, code currently just takes LAST data type option in list unless the default value happens to
            # correspond to a specific allowed value associated with one of the data types.
            data_type_and_allowed_vals_tuples_list = _get_data_types_and_allowed_vals(field_schema_dict)
            for curr_tuple in data_type_and_allowed_vals_tuples_list:
                data_type_of_default = curr_tuple[0]
                curr_allowed_vals = curr_tuple[1]
                if curr_allowed_vals is not None:
                    if default_val in curr_allowed_vals:
                        break

            if (data_type_of_default == mws.CerberusDataTypes.Text.value or
                data_type_of_default == mws.CerberusDataTypes.DateTime.value or
                data_type_of_default == mws.CerberusDataTypes.Time.value):
                    default_val = '"{0}"'.format(default_val)

            result = '=IF({trigger_col_letter}{{curr_row_index}}="", "", {default_val})'.format(
                trigger_col_letter=trigger_col_letter, default_val=default_val)
    elif mws.ValidationKeys.anyof.value in field_schema_dict:
        for curr_subschema_dict in field_schema_dict[mws.ValidationKeys.anyof.value]:
            result = get_default_formula(curr_subschema_dict, trigger_col_letter, make_text)
            if result is not None:
                break
            # end if found default
        # next subschema
    # end if

    return result


def get_field_constraint_description(field_schema_dict, a_regex_handler):
    text_pieces = []

    # append the generated description of the constraint
    constraint_desc = get_formula_constraint(field_schema_dict, a_regex_handler, make_text=True)
    if constraint_desc: text_pieces.append(constraint_desc + ".")

    # append the description of the default, if any
    default_desc = get_default_formula(field_schema_dict, None, make_text=True)
    if default_desc: text_pieces.append(default_desc + ".")

    result = " ".join(text_pieces)
    result = _uppercase_first_letter(result)

    # prepend the description, if one exists
    if mws.InputNames.field_desc.value in field_schema_dict:
        field_desc = field_schema_dict[mws.InputNames.field_desc.value]
        if field_desc:
            if not field_desc.endswith("."):
                field_desc += "."
            field_desc = _uppercase_first_letter(field_desc)
            result = field_desc + " " + result

    return result


def _get_data_types_and_allowed_vals(field_schema_dict):
    result = []
    if mws.ValidationKeys.anyof.value in field_schema_dict:
        anyof_subschemas = field_schema_dict[mws.ValidationKeys.anyof.value]
        if len(anyof_subschemas) > 2:
            raise ValueError("Current schema includes more than two anyof options, "
                             "which is not supported: '{0}'".format(field_schema_dict))

        for curr_anyof_subschema in anyof_subschemas:
            # NB: NOT recursive: goes down ONLY ONE LEVEL
            result.append(_get_single_level_data_type_and_allowed_vals(curr_anyof_subschema))
        # next subschema
    else:
        result.append(_get_single_level_data_type_and_allowed_vals(field_schema_dict))
    # end if there are subschemas

    data_types_detected = [x[0] for x in result]
    if len(data_types_detected) > 1:
        if mws.CerberusDataTypes.Text.value not in data_types_detected:
            raise ValueError("Two data types for a field are supported "
                             "only if one of them is text; instead, found {0}'.".format(data_types_detected))

    return result


def _get_single_level_data_type_and_allowed_vals(field_schema_dict):
    curr_allowed_vals = None
    if mws.ValidationKeys.allowed.value in field_schema_dict:
        curr_allowed_vals = field_schema_dict[mws.ValidationKeys.allowed.value]
    curr_data_type = field_schema_dict[mws.ValidationKeys.type.value]

    return curr_data_type, curr_allowed_vals


def _uppercase_first_letter(a_string):
    # This capitalizes the first letter.  Not using capitalize() or title() because those capitalize the first letter
    # *and* lower-case all the other letters, but I want to touch nothing except the first letter.
    return a_string[0].upper() + a_string[1:]


def _make_type_constraint(field_schema_dict, make_text):
    result = None
    anyof = mws.ValidationKeys.anyof.value
    if anyof not in field_schema_dict:
        _, _, result = _parse_field_type(field_schema_dict, make_text)

        if not make_text:
            # Note the check for blank cell value first (can't use ISBLANK because that returns false if there is a
            # formula in the cell even if that formula doesn't yield an actual value).
            blank_is_valid = False
            if mws.ValidationKeys.empty.value in field_schema_dict:
                blank_is_valid = field_schema_dict[mws.ValidationKeys.empty.value]

            blank_is_valid_str = "TRUE" if blank_is_valid else "FALSE"
            result = 'IF({cell}="",' + "{0},{1})".format(blank_is_valid_str, result)

    return result


def _get_field_data_type(field_schema_dict):
    _, result, _ = _parse_field_type(field_schema_dict, make_text=False)
    return result


def _parse_field_type(field_schema_dict, make_text):
    the_type = None
    type_constraint = None
    python_type = None
    if mws.ValidationKeys.type.value in field_schema_dict:
        the_type = field_schema_dict[mws.ValidationKeys.type.value]

        if make_text:
            type_constraint = "the value must be a {0}".format(the_type)
        else:
            if the_type == mws.CerberusDataTypes.Integer.value:
                # Note that INT(cell) throws a value error (rather than returning anything) if a non-castable string is
                # entered, which is why the iserror call is necessary.  INT also throws an error if there is no value in the
                # cell, so the handling for blanks at the end of this function is important
                type_constraint = 'IF(ISERROR(INT({cell})),FALSE,INT({cell})={cell})'

                # integer-based version for use with array formulas
                # type_constraint = 'IF(ISERROR(INT({cell})),0,INT({cell})={cell})'
                python_type = int
            elif the_type == mws.CerberusDataTypes.Decimal.value:
                # have to use VALUE() here because Excel feels the "real" content of a cell that has a formula is the
                # formula, not whatever the formula evaluates to.  HOWEVER, VALUE() of an empty cell evaluates to ZERO,
                # which doesn't make sense for our usage, so again the handling for blanks at the end of this function is
                # important
                type_constraint = "ISNUMBER(VALUE({cell}))"
                # integer-based version for use with array formulas
                # type_constraint = "INT(ISNUMBER(VALUE({cell})))"
                python_type = float
            elif the_type == mws.CerberusDataTypes.Text.value:
                # text can be anything
                type_constraint = "TRUE"  # "ISTEXT({cell})"
                # integer-based version for use with array formulas
                # type_constraint = 1
                python_type = str
            elif the_type == mws.CerberusDataTypes.DateTime.value or \
                    the_type == mws.CerberusDataTypes.Time.value:
                type_constraint = "TRUE"  # constraint for date is handled with regular expression
                # type_constraint = 'NOT(ISERR(DATEVALUE(TEXT({cell}, "YYYY-MM-DD HH:MM:SS"))))'
                # integer-based version for use with array formulas
                # type_constraint = 'INT(NOT(ISERR(DATEVALUE(TEXT({cell}, "YYYY-MM-DD")))))'
                python_type = datetime.datetime
            else:
                raise ValueError("Unrecognized data type: {0}".format(the_type))

    return the_type, python_type, type_constraint


def _make_anyof_constraint(field_schema_dict, a_regex_handler, field_data_type=None, make_text=False):
    constraint = None
    subschema_constraints = []
    if mws.ValidationKeys.anyof.value in field_schema_dict:
        anyof_subschemas = field_schema_dict[mws.ValidationKeys.anyof.value]
        for curr_anyof_subschema in anyof_subschemas:
            curr_subschema_constraint = get_formula_constraint(curr_anyof_subschema, a_regex_handler, field_data_type,
                                                               make_text=make_text)
            if curr_subschema_constraint is not None: subschema_constraints.append(curr_subschema_constraint)
        # next subschema

        constraint = _make_logical_constraint(subschema_constraints, is_and=False, make_text=make_text)
    # end if anyof

    return constraint


def _get_single_level_formula_constraint(field_schema_dict, a_regex_handler, field_data_type=None, make_text=False):
    and_constraints = []

    if field_data_type is None: field_data_type = _get_field_data_type(field_schema_dict)

    # get the type constraint (type)
    type_constraint = _make_type_constraint(field_schema_dict, make_text=make_text)
    if type_constraint is not None: and_constraints.append(type_constraint)

    # get the unique constraint
    unique_constraint = _make_unique_constraint(field_schema_dict, make_text)
    if unique_constraint is not None: and_constraints.append(unique_constraint)

    # get the min constraint
    min_constraint = _make_gte_min_constraint(field_schema_dict, field_data_type, make_text, a_regex_handler)
    if min_constraint is not None: and_constraints.append(min_constraint)
    min_exclusive_constraint = _make_gt_min_constraint(field_schema_dict, field_data_type, make_text, a_regex_handler)
    if min_exclusive_constraint is not None: and_constraints.append(min_exclusive_constraint)

    # get the max constraint
    max_constraint = _make_lte_max_constraint(field_schema_dict, field_data_type, make_text, a_regex_handler)
    if max_constraint is not None: and_constraints.append(max_constraint)
    max_exclusive_constraint = _make_lt_max_constraint(field_schema_dict, field_data_type, make_text, a_regex_handler)
    if max_exclusive_constraint is not None: and_constraints.append(max_exclusive_constraint)

    # get the forbidden constraint
    forbidden_constraint = _make_forbidden_constraint(field_schema_dict, field_data_type, make_text=make_text)
    if forbidden_constraint is not None: and_constraints.append(forbidden_constraint)

    # get the allowed constraint
    allowed_constraint = _make_allowed_constraint(field_schema_dict, field_data_type, make_text=make_text)
    if allowed_constraint is not None: and_constraints.append(allowed_constraint)

    # get the regex constraint
    regex_constraint = _make_regex_constraint(field_schema_dict, make_text, a_regex_handler)
    if regex_constraint is not None: and_constraints.append(regex_constraint)

    # make an 'and' clause for the constraints
    and_constraint_clause = _make_logical_constraint(and_constraints, True, make_text=make_text)
    return and_constraint_clause


def _make_unique_constraint(field_schema_dict, make_text):
    constraint = None
    unique_key = mws.ValidationKeys.unique.value
    if unique_key in field_schema_dict:
        if make_text:
            constraint = "must be unique"
        else:
            constraint = "COUNTIF({0}, {1}) = 1".format(col_range_placeholder, cell_placeholder)

    return constraint


def _make_regex_constraint(field_schema_dict, make_text, a_regex_handler):
    """

    :type a_regex_handler: regex_handler.RegexHandler
    """
    constraint = None
    regex_key = mws.ValidationKeys.regex.value
    if regex_key in field_schema_dict:
        regex_val = field_schema_dict[regex_key]
        constraint = a_regex_handler.get_formula_or_message_for_regex(regex_val, not make_text)

    return constraint


def _make_logical_constraint(constraints, is_and, make_text):
    if len(constraints) == 0:
        result = None
    elif len(constraints) == 1:
        result = constraints[0]
    else:
        logical_str = "AND" if is_and else "OR"
        if make_text:
            result = (" " + logical_str.lower() + " ").join(constraints)
        else:
            joined_constraints = ",".join(constraints)
            result = "{0}({1})".format(logical_str, joined_constraints)

        # NB: actual logical functions in Excel do NOT play nicely with array formulas, so if necessary can use
        # numerical versions of them as described at
        # http://dailydoseofexcel.com/archives/2004/12/04/logical-operations-in-array-formulas/
        # if is_and:
        #     result = " and ".join(constraints) if make_text else "(" + ")*(".join(constraints) + ")"
        # else:
        #     result = " or ".join(constraints) if make_text else "((" + ")+(".join(constraints) + ")>0)"

    return result


def _make_list_constraint(schema_key, format_str, is_and, field_schema_dict, field_data_type, make_text):
    constraint = None
    if schema_key in field_schema_dict:
        values_list = field_schema_dict[schema_key]
        values_list = ['"{0}"'.format(x) if field_data_type is str else x for x in values_list]

        placeholder = text_placeholder if make_text else cell_placeholder
        constraints_list = [format_str.format(placeholder, x) for x in values_list]
        constraint = _make_logical_constraint(constraints_list, is_and, make_text)
    return constraint


def _make_allowed_constraint(field_schema_dict, field_data_type, make_text):
    format_text = "must equal {1}" if make_text else "exact({0},{1})"
    return _make_list_constraint(mws.ValidationKeys.allowed.value, format_text, False,
                                 field_schema_dict, field_data_type, make_text=make_text)


def _make_forbidden_constraint(field_schema_dict, field_data_type, make_text):
    format_text = "must not equal {1}" if make_text else "{0}<>{1}"
    return _make_list_constraint(mws.ValidationKeys.forbidden.value, format_text, True,
                                 field_schema_dict, field_data_type, make_text=make_text)


def _make_comparison_constraint(schema_key, comparison_str, field_schema_dict, field_type, make_text):
    constraint = None
    if schema_key in field_schema_dict:
        threshold_val = field_schema_dict[schema_key]
        if make_text:
            constraint = "{0}{1}".format(comparison_str, threshold_val)
        else:
            if field_type == datetime.datetime:
                constraint = _make_date_constraint(comparison_str, threshold_val)
            else:
                constraint = "{0}{1}{2}".format(cell_placeholder, comparison_str, threshold_val)

    return constraint


def _make_date_constraint(comparison_str, threshold_val):
    # convert the threshold from whatever format it came in as to a datetime
    datetime_threshold_val = _cast_date_time(threshold_val, datetime_formats)
    # TODO: Need to add handling for case where threshold is just a time,
    # not a datetime, bc python sees such times as being on 01-01-1901 but
    # Excel sees them as being in year zero -- ugh.

    datetime_format = '(IFERROR(DATEVALUE({target}),0)+' \
                      'IFERROR(TIMEVALUE({target}),0))'

    # Excel cannot automatically convert YYYY, YYYY-MM, YYYY-MM-DD HH, or HH:MM
    # to dates and/or times, so to make datevalue and timevalue work on these
    # allowed formats, we have to doctor them into the closest of the formats
    # that Excel can convert (e.g., YYYY-MM-DD or YYYY-MM-DD HH:mm).
    # NB that CONCAT (instead of CONCATENATE) *cannot* be used here because
    # it is not fully supported in xlsxwriter (see
    # "Formulas added in Excel 2010 and later" at
    # https://xlsxwriter.readthedocs.io/working_with_formulas.html ).
    format_normalization = 'IF(LEN({cell})=4,CONCATENATE({cell},"-01-01"),' \
                           'IF(LEN({cell})=7,CONCATENATE({cell},"-01"),' \
                           'IF(LEN({cell})=13,CONCATENATE({cell},":00"),' \
                           '{cell})))'.format(cell=cell_placeholder)
    input_val_as_date = datetime_format.format(target=format_normalization)
    threshold_val_as_date = datetime_format.format(
        target='"' + str(datetime_threshold_val) + '"')
    comparison_formula = (input_val_as_date + comparison_str +
                          threshold_val_as_date)
    return comparison_formula


def _cast_date_time(datetime_string, allowed_formats):
    # by default, assume cast fails
    is_valid = False
    result = None

    for curr_format in allowed_formats:
        try:
            # create a python datetime object
            result = datetime.datetime.strptime(datetime_string, curr_format)
            is_valid = True
            break
        except ValueError:
            pass  # if this format gave error, just try next one

    # if none of the formats passed, NOW raise an error
    if not is_valid:
        raise ValueError("{0} cannot be converted to any of these datetime "
                         "formats: {1}".format(
                            datetime_string, " or ".join(allowed_formats)))

    return result


def _get_guaranteed_pass_value(threshold_val, increase):
    offset = 1 if increase else -1
    return float(threshold_val) + offset


def _make_lte_max_constraint(field_schema_dict, field_type, make_text, a_regex_handler):
    return _make_comparison_constraint(mws.ValidationKeys.max_inclusive.value,
                                       "<=", field_schema_dict, field_type, make_text)


def _make_gte_min_constraint(field_schema_dict, field_type, make_text, a_regex_handler):
    return _make_comparison_constraint(mws.ValidationKeys.min_inclusive.value,
                                       ">=", field_schema_dict, field_type, make_text)


def _make_lt_max_constraint(field_schema_dict, field_type, make_text, a_regex_handler):
    return _make_comparison_constraint(mws.ValidationKeys.max_exclusive.value,
                                       "<", field_schema_dict, field_type, make_text)


def _make_gt_min_constraint(field_schema_dict, field_type, make_text, a_regex_handler):
    return _make_comparison_constraint(mws.ValidationKeys.min_exclusive.value,
                                       ">", field_schema_dict, field_type, make_text)
