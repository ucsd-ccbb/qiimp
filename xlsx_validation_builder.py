import datetime

import metadata_package_schema_builder
import schema_builder

text_placeholder = "value"
cell_placeholder = "{cell}"


def roll_up_allowed_onlies(field_schema_dict):
    all_allowed_vals = []
    if metadata_package_schema_builder.ValidationKeys.anyof.value in field_schema_dict:
        anyof_subschemas = field_schema_dict[metadata_package_schema_builder.ValidationKeys.anyof.value]
        for curr_anyof_subschema in anyof_subschemas:
            subschema_allowed_vals = roll_up_allowed_onlies(curr_anyof_subschema)
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
        curr_formula_constraint = _get_single_level_formula_constraint(field_schema_dict)
        if curr_formula_constraint is not None:
            return None

    return all_allowed_vals


def get_formula_constraint(field_schema_dict, field_data_type=None, make_text=False):
    and_constraints = []

    # get the sub-constraints (anyof)
    curr_level_type = _get_field_data_type(field_schema_dict)
    if curr_level_type is not None: field_data_type = curr_level_type
    or_sub_constraints = _make_anyof_constraint(field_schema_dict, field_data_type, make_text=make_text)
    if or_sub_constraints is not None: and_constraints.append(or_sub_constraints)

    # get the constraints from this level
    level_constraints = _get_single_level_formula_constraint(field_schema_dict, field_data_type, make_text=make_text)
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
            if field_data_type is str:
                default_val = '"{0}"'.format(default_val)
            elif field_data_type is datetime.datetime:
                default_val = 'DATEVALUE("{0}")'.format(default_val)
            # end if

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


def get_field_constraint_description(field_schema_dict):
    text_pieces = []

    # get the description
    if schema_builder.InputNames.field_desc.value in field_schema_dict:
        field_desc = field_schema_dict[schema_builder.InputNames.field_desc.value]
        if field_desc: text_pieces.append(field_desc + ".")

    # append the generated description of the constraint
    constraint_desc = get_formula_constraint(field_schema_dict, make_text=True)
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
    _, result = _parse_field_type(field_schema_dict, make_text)
    return result


def _get_field_data_type(field_schema_dict):
    result, _ = _parse_field_type(field_schema_dict, make_text=False)
    return result


def _parse_field_type(field_schema_dict, make_text):
    constraint = None
    python_type = None
    anyof = metadata_package_schema_builder.ValidationKeys.anyof.value
    if metadata_package_schema_builder.ValidationKeys.type.value in field_schema_dict:
        the_type = field_schema_dict[metadata_package_schema_builder.ValidationKeys.type.value]
        if make_text:
            constraint = "the value must be a {0}".format(the_type)
        else:
            if the_type == metadata_package_schema_builder.CerberusDataTypes.Integer.value:
                # Note that INT(cell) throws a value error (rather than returning anything) if a non-castable string is
                # entered, which is why the iserror call is necessary.  INT also throws an error if there is no value in the
                # cell, so the handling for blanks at the end of this function is important
                # if anyof not in field_schema_dict: constraint = 'IF(ISERROR(INT({cell})),FALSE,INT({cell})={cell})'
                if anyof not in field_schema_dict: constraint = 'IF(ISERROR(INT({cell})),0,INT({cell})={cell})'
                python_type = int
            elif the_type == metadata_package_schema_builder.CerberusDataTypes.Decimal.value:
                # have to use VALUE() here because Excel feels the "real" content of a cell that has a formula is the
                # formula, not whatever the formula evaluates to.  HOWEVER, VALUE() of an empty cell evaluates to ZERO,
                # which doesn't make sense for our usage, so again the handling for blanks at the end of this function is
                # important
                # if anyof not in field_schema_dict: constraint = "ISNUMBER(VALUE({cell}))"
                if anyof not in field_schema_dict: constraint = "INT(ISNUMBER(VALUE({cell})))"
                python_type = float
            elif the_type == metadata_package_schema_builder.CerberusDataTypes.Text.value:
                # I think that "free form text" INCLUDES things that are numbers ... they'd be forced to text in db, right?
                if anyof not in field_schema_dict: constraint = 1  # "TRUE"  # "ISTEXT({cell})"
                python_type = str
            elif the_type == metadata_package_schema_builder.CerberusDataTypes.DateTime.value:
                if anyof not in field_schema_dict: constraint = 'INT(NOT(ISERR(DATEVALUE(TEXT({cell}, "YYYY-MM-DD")))))'
                python_type = datetime.datetime
            else:
                raise ValueError("Unrecognized data type: {0}".format(the_type))

            # Note the check for blank cell value first (can't use ISBLANK because that returns false if there is a
            # formula in the cell even if that formula doesn't yield an actual value).
            if metadata_package_schema_builder.ValidationKeys.required.value in field_schema_dict:
                blank_is_valid = 0  # "FALSE"
            else:
                blank_is_valid = 1  # "TRUE"
            constraint = 'IF({cell}="",' + "{0},{1})".format(blank_is_valid, constraint)

    return python_type, constraint


def _make_anyof_constraint(field_schema_dict, field_data_type=None, make_text=False):
    constraint = None
    subschema_constraints = []
    if metadata_package_schema_builder.ValidationKeys.anyof.value in field_schema_dict:
        anyof_subschemas = field_schema_dict[metadata_package_schema_builder.ValidationKeys.anyof.value]
        for curr_anyof_subschema in anyof_subschemas:
            curr_subschema_constraint = get_formula_constraint(curr_anyof_subschema, field_data_type, make_text=make_text)
            if curr_subschema_constraint is not None: subschema_constraints.append(curr_subschema_constraint)
        # next subschema

        constraint = _make_logical_constraint(subschema_constraints, is_and=False, make_text=make_text)
    # end if anyof

    return constraint


def _get_single_level_formula_constraint(field_schema_dict, field_data_type=None, make_text=False):
    and_constraints = []

    if field_data_type is None: field_data_type = _get_field_data_type(field_schema_dict)

    # get the type constraint (type)
    type_constraint = _make_type_constraint(field_schema_dict, make_text=make_text)
    if type_constraint is not None: and_constraints.append(type_constraint)

    # get the min constraint
    min_constraint = _make_gte_min_constraint(field_schema_dict, make_text)
    if min_constraint is not None: and_constraints.append(min_constraint)
    min_exclusive_constraint = _make_gt_min_constraint(field_schema_dict, make_text)
    if min_exclusive_constraint is not None: and_constraints.append(min_exclusive_constraint)

    # get the max constraint
    max_constraint = _make_lte_max_constraint(field_schema_dict, make_text)
    if max_constraint is not None: and_constraints.append(max_constraint)
    max_exclusive_constraint = _make_lt_max_constraint(field_schema_dict, make_text)
    if max_exclusive_constraint is not None: and_constraints.append(max_exclusive_constraint)

    # get the forbidden constraint (forbidden)
    forbidden_constraint = _make_forbidden_constraint(field_schema_dict, field_data_type, make_text=make_text)
    if forbidden_constraint is not None: and_constraints.append(forbidden_constraint)

    # get the allowed constraint (allowed)
    allowed_constraint = _make_allowed_constraint(field_schema_dict, field_data_type, make_text=make_text)
    if allowed_constraint is not None: and_constraints.append(allowed_constraint)

    # make an 'and' clause for the constraints
    and_constraint_clause = _make_logical_constraint(and_constraints, True, make_text=make_text)
    return and_constraint_clause


def _make_logical_constraint(constraints, is_and, make_text):
    if len(constraints) == 0:
        result = None
    elif len(constraints) == 1:
        result = constraints[0]
    else:
        # NB: used to use actual logical functions in Excel (below), but they do NOT play nicely with array formulas, so
        # switched over to numeric versions of them as described at
        # http://dailydoseofexcel.com/archives/2004/12/04/logical-operations-in-array-formulas/
        # logical_str = "AND" if is_and else "OR"
        # joined_constraints = ",".join(constraints)
        # result = "{0}({1})".format(logical_str, joined_constraints)

        if is_and:
            result = " and ".join(constraints) if make_text else "(" + ")*(".join(constraints) + ")"
        else:
            result = " or ".join(constraints) if make_text else "((" + ")+(".join(constraints) + ")>0)"

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


def _make_comparison_constraint(schema_key, comparison_str, field_schema_dict, make_text):
    constraint = None
    if schema_key in field_schema_dict:
        threshold_val = field_schema_dict[schema_key]
        if make_text:
            constraint = "{0}{1}".format(comparison_str, threshold_val)
        else:
            constraint = "{0}{1}{2}".format(cell_placeholder, comparison_str, threshold_val)
    return constraint


def _make_lte_max_constraint(field_schema_dict, make_text):
    return _make_comparison_constraint(metadata_package_schema_builder.ValidationKeys.max_inclusive.value,
                                       "<=", field_schema_dict, make_text)


def _make_gte_min_constraint(field_schema_dict, make_text):
    return _make_comparison_constraint(metadata_package_schema_builder.ValidationKeys.min_inclusive.value,
                                       ">=", field_schema_dict, make_text)


def _make_lt_max_constraint(field_schema_dict, make_text):
    return _make_comparison_constraint(metadata_package_schema_builder.ValidationKeys.max_exclusive.value,
                                       "<", field_schema_dict, make_text)


def _make_gt_min_constraint(field_schema_dict, make_text):
    return _make_comparison_constraint(metadata_package_schema_builder.ValidationKeys.min_exclusive.value,
                                       ">", field_schema_dict, make_text)
