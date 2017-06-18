import package_schemas

cell_placeholder = "{cell}"


def get_validation_dict(field_name, field_schema_dict):
    result = None
    validation_generators = [
        _make_allowed_only_constraint,
        _make_formula_constraint
    ]

    for curr_generator in validation_generators:
        curr_validation_dict = curr_generator(field_name, field_schema_dict)
        if curr_validation_dict is not None:
            result = curr_validation_dict
            break
        # end if validation generated
    # next validation generator

    return result


def _make_allowed_only_constraint(field_name, field_schema_dict):
    result = None
    allowed_onlies = _roll_up_allowed_onlies(field_schema_dict)

    # TODO: add back uniqueness check
    if allowed_onlies is not None and len(allowed_onlies) > 0:
        allowed_onlies_as_strs = [str(x) for x in allowed_onlies]
        result = {'validate': 'list', 'source': allowed_onlies,
                  'input_title': 'Enter {0}:'.format(field_name),
                  'input_message': '{0} must be one of these allowed values: {1}'.format(
                      field_name, ", ".join(allowed_onlies_as_strs))
                  }
    return result


def _make_formula_constraint(field_name, field_schema_dict):
    result = None
    formula_string = get_formula_constraint(field_schema_dict)

    if formula_string is not None:
        formula_string = "="+formula_string
        result = {
            'validate': 'custom', 'value': formula_string,
            'input_title': 'Enter {0}:'.format(field_name),
            'input_message': 'placeholder'
        }
    return result


def _roll_up_allowed_onlies(field_schema_dict):
    all_allowed_vals = []
    if package_schemas.anyof in field_schema_dict:
        anyof_subschemas = field_schema_dict[package_schemas.anyof]
        for curr_anyof_subschema in anyof_subschemas:
            subschema_allowed_vals = _roll_up_allowed_onlies(curr_anyof_subschema)
            if subschema_allowed_vals is None:
                return None
            else:
                all_allowed_vals.extend(subschema_allowed_vals)
            # end check of constraints in this subschema
        # next subschema
    # end if there are subschemas

    if package_schemas.allowed in field_schema_dict:
        curr_allowed_vals = field_schema_dict[package_schemas.allowed]
        all_allowed_vals.extend(curr_allowed_vals)
    else:
        curr_formula_constraint = get_single_level_formula_constraint(field_schema_dict)
        if curr_formula_constraint is not None:
            return None

    return all_allowed_vals


def _make_logical_constraint(constraints, is_and):
    if len(constraints) == 0:
        result = None
    elif len(constraints) == 1:
        result = constraints[0]
    else:
        logical_str = "AND" if is_and else "OR"
        joined_constraints = ",".join(constraints)
        result = "{0}({1})".format(logical_str, joined_constraints)
    return result


def _make_allowed_constraint(field_schema_dict, field_data_type):
    constraint = None
    if package_schemas.allowed in field_schema_dict:
        allowed_vals_list = field_schema_dict[package_schemas.allowed]
        allowed_vals_list = ['"{0}"'.format(x) if field_data_type is str else x for x in allowed_vals_list]
        # TODO: Decide whether to change this to exact(a,b) as a=b is apparently case-insensitive?
        allowed_constraints = ["{0}={1}".format(cell_placeholder, x) for x in allowed_vals_list]
        constraint = _make_logical_constraint(allowed_constraints, False)
    return constraint


# TODO: get rid of copy/paste code
def _make_forbidden_constraint(field_schema_dict, field_data_type):
    constraint = None
    if package_schemas.forbidden in field_schema_dict:
        forbidden_list = field_schema_dict[package_schemas.forbidden]
        forbidden_list = ['"{0}"'.format(x) if field_data_type is str else x for x in forbidden_list]
        forbidden_constraints = ["{0}<>{1}".format(cell_placeholder, x) for x in forbidden_list]
        constraint = _make_logical_constraint(forbidden_constraints, True)

    return constraint


def _make_max_constraint(field_schema_dict):
    constraint = None
    # TODO: add handling for comparison type once I figure out how it is expressed in Cerberus ...
    if package_schemas.amax in field_schema_dict:
        max_val = field_schema_dict[package_schemas.amax]
        constraint = "{0}<{1}".format(cell_placeholder, max_val)
    return constraint


def _make_min_constraint(field_schema_dict):
    constraint = None
    # TODO: add handling for comparison type once I figure out how it is expressed in Cerberus ...
    if package_schemas.amin in field_schema_dict:
        min_val = field_schema_dict[package_schemas.amin]
        constraint = "{0}<{1}".format(min_val, cell_placeholder)
    return constraint


def _make_type_constraint(field_schema_dict):
    _, result = _parse_field_type(field_schema_dict)
    return result


def _get_field_data_type(field_schema_dict):
    result, _ = _parse_field_type(field_schema_dict)
    return result


def _parse_field_type(field_schema_dict):
    constraint = None
    python_type = None
    if package_schemas.atype in field_schema_dict:
        the_type = field_schema_dict[package_schemas.atype]
        if the_type == package_schemas.aninteger:
            constraint = "INT({cell})={cell}"
            python_type = int
        elif the_type == package_schemas.anumber:
            constraint = "ISNUMBER({cell})"
            python_type = float
        elif the_type == package_schemas.astring:
            # I think that "free form text" INCLUDES things that are numbers ... they'd be forced to text in db, right?
            constraint = None  # "ISTEXT({cell})"
            python_type = str
        else:
            raise ValueError("Unrecognized data type: {0}".format(the_type))

    return python_type, constraint


def _make_anyof_constraint(field_schema_dict, field_data_type=None):
    constraint = None
    subschema_constraints = []
    if package_schemas.anyof in field_schema_dict:
        anyof_subschemas = field_schema_dict[package_schemas.anyof]
        for curr_anyof_subschema in anyof_subschemas:
            curr_subschema_constraint = get_formula_constraint(curr_anyof_subschema, field_data_type)
            if curr_subschema_constraint is not None: subschema_constraints.append(curr_subschema_constraint)
        # next subschema

        constraint = _make_logical_constraint(subschema_constraints, is_and=False)
    # end if anyof

    return constraint


def get_formula_constraint(field_schema_dict, field_data_type=None):
    # TODO: ensure no unrecognized tags

    and_constraints = []

    # get the sub-constraints (anyof)
    curr_level_type = _get_field_data_type(field_schema_dict)
    if curr_level_type is not None: field_data_type = curr_level_type
    or_sub_constraints = _make_anyof_constraint(field_schema_dict, field_data_type)
    if or_sub_constraints is not None: and_constraints.append(or_sub_constraints)

    # get the constraints from this level
    level_constraints = get_single_level_formula_constraint(field_schema_dict, field_data_type)
    if level_constraints is not None: and_constraints.append(level_constraints)

    # make an 'and' clause for the constraints
    and_constraint_clause = _make_logical_constraint(and_constraints, True)

    # TODO: get the default [NB: not a constraint] (default)
    return and_constraint_clause


def get_single_level_formula_constraint(field_schema_dict, field_data_type=None):
    # TODO: ensure no unrecognized tags

    and_constraints = []

    # TODO: this is copy/paste code; think of way to refactor?
    if field_data_type is None: field_data_type = _get_field_data_type(field_schema_dict)

    # get the type constraint (type)
    type_constraint = _make_type_constraint(field_schema_dict)
    if type_constraint is not None: and_constraints.append(type_constraint)

    # get the min constraint (min and ?min_comparison?)
    min_constraint = _make_min_constraint(field_schema_dict)
    if min_constraint is not None: and_constraints.append(min_constraint)

    # get the max constraint (max and ?max_comparison?)
    max_constraint = _make_max_constraint(field_schema_dict)
    if max_constraint is not None: and_constraints.append(max_constraint)

    # get the forbidden constraint (forbidden)
    forbidden_constraint = _make_forbidden_constraint(field_schema_dict, field_data_type)
    if forbidden_constraint is not None: and_constraints.append(forbidden_constraint)

    # get the allowed constraint (allowed)
    allowed_constraint = _make_allowed_constraint(field_schema_dict, field_data_type)
    if allowed_constraint is not None: and_constraints.append(allowed_constraint)

    # TODO: come back to empty constraint
    # get the empty constraint (empty) -- decide whether to use?

    # make an 'and' clause for the constraints
    and_constraint_clause = _make_logical_constraint(and_constraints, True)

    # TODO: get the default [NB: not a constraint] (default)
    return and_constraint_clause


def get_default_formula(field_schema_dict, field_data_type=None):
    result = None
    curr_level_type = _get_field_data_type(field_schema_dict)
    if curr_level_type is not None: field_data_type = curr_level_type

    if package_schemas.default in field_schema_dict:
        default_val = field_schema_dict[package_schemas.default]
        default_val = "'{0}'".format(default_val) if field_data_type is str else default_val
        result = '=IF(A{0}="", "", "{1}")'.format("{curr_row_num}", default_val)
    elif package_schemas.anyof in field_schema_dict:
        for curr_subschema_dict in field_schema_dict[package_schemas.anyof]:
            result = get_default_formula(curr_subschema_dict, field_data_type)
            if result is not None:
                break
            # end if found default
        # next subschema
    # end if

    return result
