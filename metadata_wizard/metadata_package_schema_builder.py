import os
import warnings

import metadata_wizard.metadata_wizard_settings as mws

# NOTE: The xlsx_validation_builder.py module's handling of allowed values requires that the
# data type of a schema NOT be defined outside of an anyof, EVEN IF the type of all of the anyof options are the same.

# Also note, from the Cerberus documentation: "String fields with empty values will still be validated [i.e., treated
# as valid], even when required is set to True. If you don’t want to accept empty values, see the empty rule [i.e.,
# add an "empty": False rule to the schema]." (http://docs.python-cerberus.org/en/stable/validation-rules.html#required)

_FILE_NAME_KEY = "filename"
_PARENT_KEY = "parent"
_FILENAME_BY_SAMPLETYPES_LIST_KEY = "filename_by_sampletypes_list"
_ENV_SCHEMA_KEY = "env_schema"
_SAMPLE_TYPES_KEY = "sampletypes"
_REQUIRED_EXTENSION = ".xlsx"


def update_schema(base_schema, fields_to_modify_schemas, add_silently=False):
    for curr_field_name, curr_schema_modifications in fields_to_modify_schemas.items():
        if curr_field_name in base_schema:
            base_schema[curr_field_name].update(curr_schema_modifications)
        else:
            if add_silently:
                base_schema[curr_field_name] = curr_schema_modifications
            else:
                warnings.warn("Field '{0}' could not be modified as it does not exist in the base schema '{1}'.".format(
                    curr_field_name, base_schema
                ))

    return base_schema


def load_schemas_for_package_key(env_key, sampletype_key, parent_stack_by_env_name, env_schemas):
    result = {}

    env_parent_stack = parent_stack_by_env_name[env_key]
    for curr_parent_env_name in env_parent_stack:
        curr_parent_env_schemas = env_schemas[curr_parent_env_name]

        # First, add any environment-specific info to the result schema
        env_level_schema_changes = curr_parent_env_schemas[_ENV_SCHEMA_KEY]
        update_schema(result, env_level_schema_changes, add_silently=True)

        # Then check if this env has any schema updates for the chosen sample type
        env_sampletype_schemas = curr_parent_env_schemas[_SAMPLE_TYPES_KEY]
        if sampletype_key in env_sampletype_schemas:
            env_sampletype_schema = env_sampletype_schemas[sampletype_key]
            update_schema(result, env_sampletype_schema, add_silently=True)

    return result


def load_environment_and_sampletype_info(envs_definitions, displayname_by_sampletypes_list, package_dir_path):
    # TODO: someday: this giant function would be much clearer if broken up some!
    sampletypes_display_dicts_list = _make_sampletypes_display_dicts_list(displayname_by_sampletypes_list)

    all_env_names_list = []
    display_envs_dicts_list = []
    parent_env_name_by_env_name = {}
    env_schemas = {}

    for curr_env in envs_definitions:
        curr_env_name, curr_env_dict = mws.get_single_key_and_subdict(curr_env)
        all_env_names_list.append(curr_env_name)
        curr_env_display_name = curr_env_dict[mws.DISPLAY_NAME_KEY]
        if curr_env_display_name is not None:
            display_envs_dicts_list.append(_make_name_and_display_name_dict(curr_env_name, curr_env_display_name))

        curr_env_parent_name = curr_env_dict[_PARENT_KEY]
        if curr_env_parent_name is not None:
            parent_env_name_by_env_name[curr_env_name] = curr_env_parent_name

        curr_env_schemas = {_ENV_SCHEMA_KEY: _load_schema_from_filename_val(package_dir_path, curr_env_dict)}

        curr_env_sampletype_schemas_by_name = {}
        curr_env_sampletype_dicts_list = curr_env_dict[_FILENAME_BY_SAMPLETYPES_LIST_KEY]
        for curr_env_sampletype in curr_env_sampletype_dicts_list:
            curr_env_sampletype_name, curr_env_sampletype_filename = mws.get_single_key_and_subdict(curr_env_sampletype)

            curr_env_sampletype_schema = _load_schema_from_filename_val(package_dir_path, curr_env_sampletype_filename)
            curr_env_sampletype_schemas_by_name[curr_env_sampletype_name] = curr_env_sampletype_schema

        curr_env_schemas[_SAMPLE_TYPES_KEY] = curr_env_sampletype_schemas_by_name
        env_schemas[curr_env_name] = curr_env_schemas

    parent_stack_by_env_name = {}
    for curr_env_name in all_env_names_list:
        parent_stack_by_env_name = _make_parent_stack_by_env_name(curr_env_name, parent_env_name_by_env_name, parent_stack_by_env_name)

    combinations_display_dicts_list = []
    sampletype_display_info_by_env = {}
    display_name_by_env_name = {x[mws.NAME_KEY]: x[mws.DISPLAY_NAME_KEY] for x in display_envs_dicts_list if mws.DISPLAY_NAME_KEY in x}
    # NB: loop over all envs, not just the displayable ones, because the power users get to see everything
    for curr_env_name in all_env_names_list:
        curr_env_sampletype_names = set()
        curr_parent_stack = parent_stack_by_env_name[curr_env_name]
        for curr_stack_env_name in curr_parent_stack:
            curr_stack_env_schemas = env_schemas[curr_stack_env_name]
            curr_env_sampletype_names.update(curr_stack_env_schemas[_SAMPLE_TYPES_KEY].keys())

        curr_env_sampletype_display_info_list = []
        curr_env_display_name = display_name_by_env_name[curr_env_name] if curr_env_name in display_name_by_env_name else None
        for curr_sampletype_dict in sampletypes_display_dicts_list:
            curr_sampletype_name, curr_sampletype_display_name = _get_name_and_display_name(curr_sampletype_dict)
            if curr_sampletype_name in curr_env_sampletype_names:
                if curr_env_display_name is not None:
                    curr_sampletype_display_info_list = [curr_sampletype_name, curr_sampletype_display_name]
                    curr_env_sampletype_display_info_list.append(curr_sampletype_display_info_list)

                new_combination_name = curr_env_name + " " + curr_sampletype_name
                new_combination = _make_name_and_display_name_dict(new_combination_name, new_combination_name)
                combinations_display_dicts_list.append(new_combination)

        sampletype_display_info_by_env[curr_env_name] = curr_env_sampletype_display_info_list

    return combinations_display_dicts_list, display_envs_dicts_list, sampletype_display_info_by_env, \
           parent_stack_by_env_name, env_schemas


def _load_schema_from_filename_val(base_dir, a_dict):
    a_schema = {}
    a_filename = a_dict
    try:
        a_filename = a_dict[_FILE_NAME_KEY]
    except:
        pass

    if a_filename is None:
        warnings.warn("No filename specified for '{0}'.".format(a_dict))
    else:
        a_filepath = os.path.join(base_dir, a_filename)
        a_schema = mws.load_yaml_from_wizard_xlsx(a_filepath, mws.METADATA_SCHEMA_SHEET_NAME)
    return a_schema


# TODO: someday: rename as the product isn't really stack-like: it starts with most general, not least general
def _make_parent_stack_by_env_name(env_name, parent_env_name_by_env_name, parent_stack_by_env_name):
    if env_name not in parent_stack_by_env_name:
        curr_stack = []
        if env_name in parent_env_name_by_env_name:
            parent_env_name = parent_env_name_by_env_name[env_name]
            parent_stack_by_env_name = _make_parent_stack_by_env_name(parent_env_name, parent_env_name_by_env_name, parent_stack_by_env_name)
            curr_stack = list(parent_stack_by_env_name[parent_env_name])

        curr_stack.append(env_name)
        parent_stack_by_env_name[env_name] = curr_stack

    return parent_stack_by_env_name


def _make_sampletypes_display_dicts_list(displayname_by_sampletypes_list):
    result = []
    for curr_sampletype in displayname_by_sampletypes_list:
        curr_sampletype_name, curr_sampletype_display_name = mws.get_single_key_and_subdict(curr_sampletype)
        result.append(_make_name_and_display_name_dict(curr_sampletype_name, curr_sampletype_display_name))
    return result


def _make_name_and_display_name_dict(name, display_name):
    return {mws.NAME_KEY: name, mws.DISPLAY_NAME_KEY: display_name}


def _get_name_and_display_name(names_dict):
    return names_dict[mws.NAME_KEY], names_dict[mws.DISPLAY_NAME_KEY]
