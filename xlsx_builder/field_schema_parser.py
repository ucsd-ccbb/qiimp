import datetime
import json

import generic_field


def _get_string_delimiter():
    return ","


def _parse_delimited_string(a_value, field_to_fill):
    indiv_vals = a_value.split(_get_string_delimiter())
    result = _parse_list(indiv_vals, field_to_fill)
    return result


def _parse_single_string(a_value, field_to_fill):
    # TODO: add handling for if string is not None but is empty?
    result = _parse_list([a_value], field_to_fill)
    return result


def _parse_list(list_of_strings, field_to_fill):
    stripped_vals = [x.strip() for x in list_of_strings]
    # throwing text values of "true", "false", "True", "False", "TRUE", "FALSE", etc into Excel
    # unprotected gets them summarily converted to TRUE and FALSE (booleans), so have to prefix them
    # with a ' to ensure they are correctly treated as text
    munged_split_vals = ["'{0}".format(x) if x.lower() in ["true", "false"] else x for x in stripped_vals]
    field_to_fill.add_allowed_values(munged_split_vals)
    return field_to_fill


def _parse_default_value(a_value, field_to_fill):
    prepped_value = a_value
    if field_to_fill.data_type is not None:
        try:
            prepped_value = field_to_fill.data_type(a_value)
        except ValueError:
            # try to convert the default value to the type requested for the field if possible (e.g., for decimal
            # field, default value entered as "0.5" should be treated as 0.5) but don't raise error if conversion
            # isn't possible: in example above, field with decimal values could reasonably have default of
            # "Not Provided", etc.
            pass

    if field_to_fill.data_type is str:
        prepped_value = _parse_single_string(prepped_value, field_to_fill)

    field_to_fill.default_value = prepped_value
    return field_to_fill


def _parse_data_type_and_limit(the_type, is_maximum, a_value, field_to_fill):
    field_to_fill.data_type = the_type
    if is_maximum:
        field_to_fill.maximum = a_value
    else:
        field_to_fill.minimum = a_value
    return field_to_fill


def process_non_object_entry(a_key, a_value, current_field):
    if a_key.startswith("integer"):
        current_field.data_type = int
    elif a_key.startswith("decimal"):
        current_field.data_type = float
    elif a_key.startswith("datetime"):
        current_field.data_type = datetime.datetime
    elif a_key.startswith("text"):
        current_field.data_type = str

    if a_key.endswith("_maximum"):
        current_field.maximum = a_value
    elif a_key.endswith("_minimum"):
        current_field.minimum = a_value

    return current_field


class FieldSchemaParser:
    _PARSER_FUNCS_BY_KEY = {"text_minimum": lambda x,y: _parse_data_type_and_limit(str, False, x, y),
                            "text_maximum": lambda x,y: _parse_data_type_and_limit(str, True, x, y),
                            "integer_minimum": lambda x,y: _parse_data_type_and_limit(int, False, x, y),
                            "integer_maximum": lambda x,y: _parse_data_type_and_limit(int, True, x, y),
                            "decimal_minimum": lambda x,y: _parse_data_type_and_limit(float, False, x, y),
                            "decimal_maximum": lambda x,y: _parse_data_type_and_limit(float, True, x, y),
                            "datetime_minimum": lambda x,y: _parse_data_type_and_limit(datetime.datetime, False, x, y),
                            "datetime_maximum": lambda x,y: _parse_data_type_and_limit(datetime.datetime, True, x, y),
                            "unit": _parse_single_string,
                            "boolean_true": _parse_single_string,
                            "boolean_false": _parse_single_string,
                            "categorical_values": _parse_delimited_string,
                            "default_value": _parse_default_value,
                            "allowed_missing_vals": _parse_delimited_string
                            }

    @classmethod
    def parse(cls, fields_schema_json_str):
        result = []
        fields_schema_dict = json.loads(fields_schema_json_str)

        for curr_schema_dict in fields_schema_dict:
            curr_field = generic_field.GenericField()
            for a_key, a_value in curr_schema_dict.items():
                curr_field = cls._process_potential_object_entry(a_key, a_value, curr_field)
            result.append(curr_field)

        return result

    @classmethod
    def _process_potential_object_entry(cls, a_key, potentially_iterable_val, current_field):
        result = current_field  # default

        items_method = getattr(potentially_iterable_val, "items", None)
        if callable(items_method):
            for sub_key, sub_value in potentially_iterable_val.items():
                result = cls._process_potential_object_entry(sub_key, sub_value, current_field)
        else:
            if potentially_iterable_val is not None:
                parse_func = cls._PARSER_FUNCS_BY_KEY[a_key]
                result = parse_func(potentially_iterable_val, current_field)

        return result
