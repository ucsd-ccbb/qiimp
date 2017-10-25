import datetime
import re

import metadata_package_schema_builder
import schema_builder
import regex_handler
    
text_placeholder = "value"
cell_placeholder = "{cell}"
    

def roll_up_allowed_onlies(field_schema_dict, a_regex_handler):
    all_allowed_vals = []
    if metadata_package_schema_builder.ValidationKeys.anyof.value in field_schema_dict:
        anyof_subschemas = field_schema_dict[metadata_package_schema_builder.ValidationKeys.anyof.value]
        for curr_anyof_subschema in anyof_subschemas:
            subschema_allowed_vals = roll_up_allowed_onlies(curr_anyof_subschema, a_regex_handler)
            if subschema_allowed_vals is None:
                return None
            else:
                all_allowed_vals.extend(subschema_allowed_vals)
            # end check of constraints in this subschema
        # next subschema
    # end if there are subschemas

    if metadata_package_schema_builder.ValidationKeys.allowed.value in field_schema_dict:
        curr_allowed_vals = field_schema_dict[metadata_package_schema_builder.ValidationKeys.allowed.value]
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


def get_default_formula(field_schema_dict, trigger_col_letter, field_data_type=None, make_text=False):
    result = None
    curr_level_type = _get_field_data_type(field_schema_dict)
    if curr_level_type is not None: field_data_type = curr_level_type

    # default is only filled in if user has put something into a trigger column, to avoid confusing them by having
    # entries in rows that they haven't even thought about yet.
    if metadata_package_schema_builder.ValidationKeys.default.value in field_schema_dict:
        default_val = field_schema_dict[metadata_package_schema_builder.ValidationKeys.default.value]
        if make_text:
            result = "The default value is {0}".format(default_val)
        else:
            if field_data_type is str or field_data_type is datetime.datetime:
                default_val = '"{0}"'.format(default_val)

            result = '=IF({trigger_col_letter}{{curr_row_index}}="", "", {default_val})'.format(
                trigger_col_letter=trigger_col_letter, default_val=default_val)
    elif metadata_package_schema_builder.ValidationKeys.anyof.value in field_schema_dict:
        for curr_subschema_dict in field_schema_dict[metadata_package_schema_builder.ValidationKeys.anyof.value]:
            result = get_default_formula(curr_subschema_dict, trigger_col_letter, field_data_type, make_text)
            if result is not None:
                break
            # end if found default
        # next subschema
    # end if

    return result


def get_field_constraint_description(field_schema_dict, a_regex_handler):
    text_pieces = []

    # get the description
    if schema_builder.InputNames.field_desc.value in field_schema_dict:
        field_desc = field_schema_dict[schema_builder.InputNames.field_desc.value]
        if field_desc: text_pieces.append(field_desc + ".")

    # append the generated description of the constraint
    constraint_desc = get_formula_constraint(field_schema_dict, a_regex_handler, make_text=True)
    if constraint_desc: text_pieces.append(constraint_desc + ".")

    # append the description of the default, if any
    default_desc = get_default_formula(field_schema_dict, None, make_text=True)
    if default_desc: text_pieces.append(default_desc + ".")

    result = "\n".join(text_pieces)
    # This capitalizes the first letter.  Not using capitalize() or title() because those capitalize the first letter
    # *and* lower-case all the other letters, but I want to touch nothing except the first letter.
    result = result[0].upper() + result[1:]
    return result


def _make_type_constraint(field_schema_dict, make_text):
    result = None
    anyof = metadata_package_schema_builder.ValidationKeys.anyof.value
    if anyof not in field_schema_dict:
        _, _, result = _parse_field_type(field_schema_dict, make_text)

        if not make_text:
            # Note the check for blank cell value first (can't use ISBLANK because that returns false if there is a
            # formula in the cell even if that formula doesn't yield an actual value).
            blank_is_valid = False
            if metadata_package_schema_builder.ValidationKeys.empty.value in field_schema_dict:
                blank_is_valid = field_schema_dict[metadata_package_schema_builder.ValidationKeys.empty.value]

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
    if metadata_package_schema_builder.ValidationKeys.type.value in field_schema_dict:
        the_type = field_schema_dict[metadata_package_schema_builder.ValidationKeys.type.value]

        if make_text:
            type_constraint = "the value must be a {0}".format(the_type)
        else:
            if the_type == metadata_package_schema_builder.CerberusDataTypes.Integer.value:
                # Note that INT(cell) throws a value error (rather than returning anything) if a non-castable string is
                # entered, which is why the iserror call is necessary.  INT also throws an error if there is no value in the
                # cell, so the handling for blanks at the end of this function is important
                type_constraint = 'IF(ISERROR(INT({cell})),FALSE,INT({cell})={cell})'

                # integer-based version for use with array formulas
                # type_constraint = 'IF(ISERROR(INT({cell})),0,INT({cell})={cell})'
                python_type = int
            elif the_type == metadata_package_schema_builder.CerberusDataTypes.Decimal.value:
                # have to use VALUE() here because Excel feels the "real" content of a cell that has a formula is the
                # formula, not whatever the formula evaluates to.  HOWEVER, VALUE() of an empty cell evaluates to ZERO,
                # which doesn't make sense for our usage, so again the handling for blanks at the end of this function is
                # important
                type_constraint = "ISNUMBER(VALUE({cell}))"
                # integer-based version for use with array formulas
                # type_constraint = "INT(ISNUMBER(VALUE({cell})))"
                python_type = float
            elif the_type == metadata_package_schema_builder.CerberusDataTypes.Text.value:
                # text can be anything
                type_constraint = "TRUE"  # "ISTEXT({cell})"
                # integer-based version for use with array formulas
                # type_constraint = 1
                python_type = str
            elif the_type == metadata_package_schema_builder.CerberusDataTypes.DateTime.value:
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
    if metadata_package_schema_builder.ValidationKeys.anyof.value in field_schema_dict:
        anyof_subschemas = field_schema_dict[metadata_package_schema_builder.ValidationKeys.anyof.value]
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

    regex_constraint = _make_regex_constraint(field_schema_dict, make_text, a_regex_handler)
    if regex_constraint is not None: and_constraints.append(regex_constraint)

    # make an 'and' clause for the constraints
    and_constraint_clause = _make_logical_constraint(and_constraints, True, make_text=make_text)
    return and_constraint_clause


def _make_regex_constraint(field_schema_dict, make_text, a_regex_handler):
    """

    :type a_regex_handler: regex_handler.RegexHandler
    """
    constraint = None
    regex_key = metadata_package_schema_builder.ValidationKeys.regex.value
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
    return _make_list_constraint(metadata_package_schema_builder.ValidationKeys.allowed.value, format_text, False,
                                 field_schema_dict, field_data_type, make_text=make_text)


def _make_forbidden_constraint(field_schema_dict, field_data_type, make_text):
    format_text = "must not equal {1}" if make_text else "{0}<>{1}"
    return _make_list_constraint(metadata_package_schema_builder.ValidationKeys.forbidden.value, format_text, True,
                                 field_schema_dict, field_data_type, make_text=make_text)


def _make_comparison_constraint(schema_key, comparison_str, field_schema_dict, field_type, make_text, a_regex_handler,
                                is_greater_than):
    constraint = None
    if schema_key in field_schema_dict:
        threshold_val = field_schema_dict[schema_key]
        if make_text:
            constraint = "{0}{1}".format(comparison_str, threshold_val)
        else:
            guaranteed_pass_val = _get_guaranteed_pass_value(threshold_val, is_greater_than)
            if field_type == datetime.datetime:
                constraint = _make_date_constraint(comparison_str, threshold_val, a_regex_handler.datetime_regex,
                                                   guaranteed_pass_val)
            else:
                constraint = "IFERROR(NUMBERVALUE({0}),{1}){2}{3}".format(cell_placeholder, guaranteed_pass_val,
                                                                          comparison_str, threshold_val)
    return constraint


def _make_date_constraint(comparison_str, threshold_val, datetime_regex, guaranteed_pass_val):
    # get all the pieces of the threshold value
    regex = re.compile(datetime_regex)
    regex_matches = regex.match(threshold_val).groups()

    result = None
    last_group_index = len(regex_matches) - 1

    def get_start_position(match_index):
        return 1 if match_index == 0 else (match_index+1) * 3

    # Note: we are going BACKWARDS through the matches, so as to start with seconds and work up to years.
    # Also note that end of range is -1, because we want to see the 0-index group, and range is exclusive of endpoint.
    for i in range(last_group_index, -1, -1):
        curr_match = regex_matches[i]
        if curr_match is not None:
            pieces = []
            curr_threshold_val = int(curr_match)
            startpos = get_start_position(i)
            # all values are two positions long except for year, which is four
            val_length = len(curr_match)
            curr_input_val = "IFERROR(INT(MID({0},{1},{2})), {3})".format(cell_placeholder, startpos, val_length,
                                                                          guaranteed_pass_val)

            curr_level_constraint = curr_input_val + "{0}{1}".format(comparison_str, curr_threshold_val)
            pieces.append(curr_level_constraint)

            if result:
                pieces.append("IF(" + curr_input_val + "={0},{1}, TRUE)".format(curr_threshold_val, result))
            result = _make_logical_constraint(pieces, is_and=True, make_text=False)

    return result


def _get_guaranteed_pass_value(threshold_val, increase):
    offset = 1 if increase else -1
    return float(threshold_val) + offset


def _make_lte_max_constraint(field_schema_dict, field_type, make_text, a_regex_handler):
    return _make_comparison_constraint(metadata_package_schema_builder.ValidationKeys.max_inclusive.value,
                                       "<=", field_schema_dict, field_type, make_text, a_regex_handler, False)


def _make_gte_min_constraint(field_schema_dict, field_type, make_text, a_regex_handler):
    return _make_comparison_constraint(metadata_package_schema_builder.ValidationKeys.min_inclusive.value,
                                       ">=", field_schema_dict, field_type, make_text, a_regex_handler, True)


def _make_lt_max_constraint(field_schema_dict, field_type, make_text, a_regex_handler):
    return _make_comparison_constraint(metadata_package_schema_builder.ValidationKeys.max_exclusive.value,
                                       "<", field_schema_dict, field_type, make_text, a_regex_handler, False)


def _make_gt_min_constraint(field_schema_dict, field_type, make_text, a_regex_handler):
    return _make_comparison_constraint(metadata_package_schema_builder.ValidationKeys.min_exclusive.value,
                                       ">", field_schema_dict, field_type, make_text, a_regex_handler, True)
