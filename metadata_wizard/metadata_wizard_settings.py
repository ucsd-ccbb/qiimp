import configparser
import datetime
from enum import Enum
import os

import openpyxl
import yaml

SEPARATOR = "_"
TEMPLATE_SUFFIX = SEPARATOR + "template"
# TODO: someday: move this into the config
UNITS_SUFFIX = SEPARATOR + "units"
PHI_SUFFIX = SEPARATOR + "phi"
# All field names should be lowercase and contain only alphanumeric and underscores.
# No field name can start with a number
FIELD_NAME_REGEX = "^[a-z][a-z0-9_]*$"
NON_WIZARD_XLSX_ERROR_PREFIX = "Spreadsheet does not appear to have been produced by the metadata wizard: "
# TODO: someday: this duplicates a definition in xlsx_builder, which would be a circular reference here; refactor!
METADATA_SCHEMA_SHEET_NAME = "metadata_schema"
SAMPLE_NAME_HEADER = "sample_name"
NAME_KEY = "name"
DISPLAY_NAME_KEY = "display_name"
TUTORIAL_LINK = "Need help? Visit the <a target='_blank' href='http://metadata-wizard-tutorial.readthedocs.io/en/latest/'>tutorial</a>! (Opens in new tab.)"


def get_single_key_and_subdict(a_dict):
    if len(a_dict.keys()) != 1:
        raise ValueError(
            "Dictionary '{0}' is mis-structured; must have only one top-level key.".format(a_dict))

    single_key = list(a_dict.keys())[0]
    return single_key, a_dict[single_key]


def load_yaml_from_wizard_xlsx(filepath, yaml_sheetname):
    assumed_cell = "A1"
    wb = openpyxl.load_workbook(filename=filepath)
    check_is_metadata_wizard_file(wb, yaml_sheetname, filepath)

    yaml_sheet = wb[yaml_sheetname]
    yaml_string = yaml_sheet[assumed_cell].value
    yaml_dict = yaml.load(yaml_string)
    return yaml_dict


# TODO: someday: grrr ... this doesn't really belong here, I feel, but can't move it xlsx_basics because that
# would create a circular reference, so some refactoring is called for ...
def check_is_metadata_wizard_file(openpyxl_workbook, yaml_sheetname, filepath):
    sheet_names = openpyxl_workbook.get_sheet_names()
    if yaml_sheetname not in sheet_names:
        error_msg = "{0}'{1}' .".format(NON_WIZARD_XLSX_ERROR_PREFIX, filepath)
        raise ValueError(error_msg)


def _load_yaml_from_fp(filepath):
    with open(filepath, 'r') as stream:
        result = yaml.load(stream)
    return result


class ValidationKeys(Enum):
    type = "type"
    required = "required"
    allowed = "allowed"
    default = "default"
    empty = "empty"
    anyof = "anyof"
    min_inclusive = "min"
    min_exclusive = "min_exclusive"
    max_inclusive = "max"
    max_exclusive = "max_exclusive"
    forbidden = "forbidden"
    regex = "regex"
    unique = "unique"


class CerberusDataTypes(Enum):
    Text = "string"
    Integer = "integer"
    Decimal = "number"
    DateTime = "datetime"


class EbiMissingValues(Enum):
    # values from https://www.ebi.ac.uk/ena/about/missing-values-reporting
    ebi_not_applicable = "not applicable"
    ebi_not_collected = "missing: not collected"
    ebi_not_provided = "missing: not provided"
    ebi_restricted = "missing: restricted access"


class InputNames(Enum):
    study_name = "study_name"
    field_name = "field_name"
    field_type = "field_type"
    field_desc = "field_desc"
    allowed_missing_vals = "allowed_missing_vals[]"
    default_value = "default_value"
    allowed_missing_default_select = "allowed_missing_default_select"
    categorical_default_select = "categorical_default_select"
    continuous_default = "continuous_default"
    boolean_default_select = "boolean_default_select"
    text_default = "text_default"
    datetime_default = "datetime_default"
    true_value = "true_value"
    false_value = "false_value"
    data_type = "data_type"
    categorical_values = "categorical_values"
    minimum_comparison = "minimum_comparison"
    minimum_value = "minimum_value"
    maximum_comparison = "maximum_comparison"
    maximum_value = "maximum_value"
    units = "units"
    is_phi = "is_phi"
    environment = "env"
    sample_type = "sample_type"


class FieldTypes(Enum):
    Boolean = "boolean"
    Categorical = "categorical"
    Continuous = "continuous"
    Text = CerberusDataTypes.Text.value


def _get_field_type_to_tooltip_dict():
    return {
        FieldTypes.Text.value: "Free Text",
        FieldTypes.Boolean.value: "Boolean (True/False)",
        FieldTypes.Categorical.value: "Categorical (Group A, B, C, etc.)",
        FieldTypes.Continuous.value: "Continous (Numbers, dates, etc.)"
    }

class DefaultTypes(Enum):
    no_default = "no_default"
    boolean_default = "boolean_default"
    allowed_missing_default = "allowed_missing_default"
    categorical_default = "categorical_default"
    continuous_default = "continuous_default"
    text_default = "text_default"


class MetadataWizardState(object):
    def __init__(self):
        # I think this should NOT be in the config; new versions SHOULD involve changing code.
        self.VERSION = "v0.3"

        # TODO: someday: these file path definitions should move into the config
        self.RESERVED_WORDS_YAML_PATH = "reserved_words.yaml"
        self.REGEX_YAML_PATH = 'regex_definitions.yaml'
        self.README_TEXT_PATH = "readme_template.txt"
        self.DEFAULT_LOCALES_YAML_PATH = "default_locales.yaml"
        self.ENVIRONMENTS_YAML_PATH = "environments.yaml"
        self.SAMPLETYPES_YAML_PATH = "sampletypes.yaml"
        self.FIELD_TYPE_TOOLTIPS = _get_field_type_to_tooltip_dict()

        self.install_dir = None
        self.static_path = None
        self.packages_dir_path = None
        self.settings_dir_path = None
        self.templates_dir_path = None
        self.client_scripts_dir_path = None

        self.main_url = None
        self.full_upload_url = None
        self.full_merge_url = None
        self.websocket_url = None
        self.listen_port = None

        self.regex_handler = None

        self.default_locales_list = None
        self.reserved_words_list = None
        self.displayname_by_sampletypes_list = None
        self.environment_definitions = None

        self.combinations_display_dicts_list = None
        self.envs_display_dicts_list = None
        self.sampletype_display_dicts_list = None
        self.parent_stack_by_env_name = None
        self.env_schemas = None

        self.merge_info_by_merge_id = {}

    def set_up(self, is_deployed):
        self.install_dir = os.path.dirname(__file__)
        self.settings_dir_path = os.path.join(self.install_dir, "settings")
        self.packages_dir_path = os.path.join(self.settings_dir_path, "packages")
        self.templates_dir_path = os.path.join(self.install_dir, "templates")
        self.client_scripts_dir_path = os.path.join(self.install_dir, "client_scripts")


        self._get_config_values(is_deployed)
        if self.static_path == "": self.static_path = self.install_dir
        self.main_url = "{0}:{1}".format(self.websocket_url, self.listen_port)
        self.full_upload_url = "http://{0}/upload".format(self.main_url)
        self.full_merge_url = "http://{0}/merge".format(self.main_url)

        self.regex_handler = RegexHandler(self._get_settings_item_path(self.REGEX_YAML_PATH))
        self.reserved_words_list = _load_yaml_from_fp(self._get_settings_item_path(self.RESERVED_WORDS_YAML_PATH))
        self.default_locales_list = _load_yaml_from_fp(self._get_settings_item_path(self.DEFAULT_LOCALES_YAML_PATH))
        self.displayname_by_sampletypes_list = _load_yaml_from_fp(self._get_settings_item_path(self.SAMPLETYPES_YAML_PATH))
        self.environment_definitions = _load_yaml_from_fp(self._get_settings_item_path(self.ENVIRONMENTS_YAML_PATH))

    def set_env_and_sampletype_infos(self, env_and_sampletype_infos_tuple):
        # NB: These values come from metadata_package_schema_builder.load_environment_and_sampletype_info; a more
        # explicit output rather than an arbitrarily ordered tuple wouldn't be a bad idea :)
        self.combinations_display_dicts_list = env_and_sampletype_infos_tuple[0]
        self.envs_display_dicts_list = env_and_sampletype_infos_tuple[1]
        self.sampletype_display_dicts_list = env_and_sampletype_infos_tuple[2]
        self.parent_stack_by_env_name = env_and_sampletype_infos_tuple[3]
        self.env_schemas = env_and_sampletype_infos_tuple[4]

    def get_output_path(self, file_name):
        return os.path.join(self.install_dir, self.get_partial_output_path(file_name))

    def get_partial_output_path(self, file_name):
        return os.path.join("output", file_name)

    def make_readme_text(self):
        with open(self._get_settings_item_path(self.README_TEXT_PATH), 'r') as f:
            readme_text = f.read()

        now = datetime.datetime.now()
        readme_text = readme_text.replace("VERSION", self.VERSION)
        readme_text = readme_text.replace("GENERATION_TIMESTAMP", now.strftime("%Y-%m-%d %H:%M:%S"))
        return readme_text

    def _get_config_values(self, is_deployed):
        section_name = "DEPLOYED" if is_deployed else "LOCAL"
        config_parser = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
        config_parser.read_file(open(os.path.join(self.settings_dir_path, 'config.txt')))

        self.static_path = os.path.expanduser(config_parser.get(section_name, "static_path"))
        self.listen_port = os.path.expanduser(config_parser.get(section_name, "listen_port"))
        self.websocket_url = os.path.expanduser(config_parser.get(section_name, "websocket_url"))

    def _get_settings_item_path(self, item_file_name):
        return self._get_item_path(self.settings_dir_path, item_file_name)

    @staticmethod
    def _get_item_path(parent_dir, file_name):
        return os.path.join(parent_dir, file_name)


class RegexHandler(object):
    FORMULA_KEY = "formula"
    REGEX_KEY = "regex"
    MESSAGE_KEY = "message"

    def __init__(self, regex_definitions_yaml_fp):
        with open(regex_definitions_yaml_fp) as f:
            self._dict_of_regex_dicts = yaml.load(f)

        self.datetime_regex = self.get_regex_val_by_name(CerberusDataTypes.DateTime.value)

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