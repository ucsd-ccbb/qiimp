import yaml

import metadata_package_schema_builder


class RegexHandler(object):
    FORMULA_KEY = "formula"
    REGEX_KEY = "regex"
    MESSAGE_KEY = "message"

    def __init__(self, regex_definitions_yaml_fp):
        with open(regex_definitions_yaml_fp) as f:
            self._dict_of_regex_dicts = yaml.load(f)

        self.datetime_regex = self.get_regex_val_by_name(
            metadata_package_schema_builder.CerberusDataTypes.DateTime.value)

    def get_regex_val_by_name(self, regex_name):
        return self._get_relevant_item_dict_if_any(regex_name, self.REGEX_KEY)

    def get_formula_or_message_for_regex(self, regex_value, get_formula=True):
        result = None
        for _, details_dict in self._dict_of_regex_dicts.items():
            curr_regex_value = details_dict[self.REGEX_KEY]
            if curr_regex_value == regex_value:
                result = details_dict[self.FORMULA_KEY] if get_formula else details_dict[self.MESSAGE_KEY]
                break

        if result is None:
            raise ValueError("unrecognized regex {0}".format(regex_value))
        return result

    def _get_relevant_item_dict_if_any(self, section_key, item_key):
        result = None
        if section_key in self._dict_of_regex_dicts:
            section_dict = self._dict_of_regex_dicts[section_key]
            if item_key in section_dict:
                result = section_dict[item_key]

        return result
