from enum import Enum
import glob
import os
import yaml

import openpyxl

# NOTE: The xlsx_validation_builder.py module's handling of allowed values requires that the
# data type of a schema NOT be defined outside of an anyof, EVEN IF the type of all of the anyof options are the same.

# Also note, from the Cerberus documentation: "String fields with empty values will still be validated [i.e., treated
# as valid], even when required is set to True. If you don’t want to accept empty values, see the empty rule [i.e.,
# add an "empty": False rule to the schema]." (http://docs.python-cerberus.org/en/stable/validation-rules.html#required)

SAMPLE_NAME_HEADER = "sample_name"
NAME_KEY = "name"
DISPLAY_NAME_KEY = "display_name"
HOST_ASSOCIATED_KEY = "host_associated"
NON_WIZARD_XLSX_ERROR_PREFIX = "Spreadsheet does not appear to have been produced by the metadata wizard: "
# TODO: someday: this duplicates a definition in xlsx_builder, which would be a circular reference here; refactor!
METADATA_SCHEMA_SHEET_NAME = "metadata_schema"
_REQUIRED_EXTENSION = ".xlsx"
_BASE_PACKAGE_NAME = "base"
_CROSS_SYMBOL = "+"
_BASE_HOST_NAME = "other"
_HOST_PREFIX = "host_"
_SAMPLETYPE_PREFIX = "sampletype_"
_CROSS_PREFIX = "cross" + _CROSS_SYMBOL
_HAS_HOST_SUFFIX = "_hashost"


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


class SampleTypes(Enum):
    mucus = 'mucus'
    stool = 'stool'


class UnitTypes(Enum):
    kilograms = "kg"
    grams = "g"


class Location(object):
    geo_loc_name = None
    elevation = None
    latitude = None
    longitude = None


class SanDiego(Location):
    geo_loc_name = "USA:CA:San Diego"
    elevation = 193
    latitude = 32.842
    longitude = -117.258


class PerSamplePackage(object):
    # All field names should be lowercase and contain only alphanumeric and underscores.
    # No field name can start with a number
    FIELD_NAME_REGEX = "^[a-z][a-z0-9_]*$"

    SAMPLE_NAME_REGEX = "^[a-zA-Z0-9\.]+$"  # alphanumeric and period only,

    @staticmethod
    def get_base_schema():
        return {
            SAMPLE_NAME_HEADER: {  # note that sample name should be unique within a study
                ValidationKeys.type.value: CerberusDataTypes.Text.value,
                ValidationKeys.regex.value: PerSamplePackage.SAMPLE_NAME_REGEX,
                ValidationKeys.empty.value: False,
                ValidationKeys.required.value: True,
                ValidationKeys.unique.value: True,
                # TODO: someday: This is_phi value shouldn't be hardcoded here.  Then again, my understanding is that eventually
                # this entire per-sample package will no longer be hardcoded here but will be in yaml, so not bothering
                # to refactor unless that understanding changes.
                "is_phi": False
            }
        }


def load_yaml_from_fp(filepath):
    with open(filepath, 'r') as stream:
        result = yaml.load(stream)
    return result


def load_yaml_from_wizard_xlsx(filepath, yaml_sheetname):
    assumed_cell = "A1"
    wb = openpyxl.load_workbook(filename=filepath)
    sheet_names = wb.get_sheet_names()
    if yaml_sheetname not in sheet_names:
        error_msg = "{0}'{1}' .".format(NON_WIZARD_XLSX_ERROR_PREFIX, filepath)
        raise ValueError(error_msg)

    yaml_sheet = wb[yaml_sheetname]
    yaml_string = yaml_sheet[assumed_cell].value
    yaml_dict = yaml.load(yaml_string)
    return yaml_dict


def load_schemas_for_package_key(packages_dir_path, package_key):
    cross_schema = {}  # by default, assume there will not be a cross-schema
    result = PerSamplePackage.get_base_schema()

    if package_key != _BASE_PACKAGE_NAME:
        cross_pieces = package_key.split(_CROSS_SYMBOL)
        if len(cross_pieces) > 2:
            raise ValueError("package_key '{0}' split into more than two values on '{1}'".format(
                package_key, _CROSS_SYMBOL))

        sampletype_basename = _SAMPLETYPE_PREFIX + cross_pieces[0]
        if len(cross_pieces) == 2:
            # if it has a second piece, it must be host-associated, so load basic host info
            _, base_host_fp = _make_host_filename_and_path(packages_dir_path, _BASE_HOST_NAME)
            base_host_schema = load_yaml_from_wizard_xlsx(base_host_fp, METADATA_SCHEMA_SHEET_NAME)
            result.update(base_host_schema)

            # now load the specifics for this particular host, if different from base host
            specific_host_name = cross_pieces[1]
            if specific_host_name != _BASE_HOST_NAME:
                specific_host_filename, specific_host_fp = _make_host_filename_and_path(packages_dir_path,
                                                                                        specific_host_name)
                specific_host_schema = load_yaml_from_wizard_xlsx(specific_host_fp, METADATA_SCHEMA_SHEET_NAME)
                result.update(specific_host_schema)

                # generate the cross file path, so can check if one exists
                cross_filename = _CROSS_PREFIX + sampletype_basename + _CROSS_SYMBOL + specific_host_filename
                cross_fp = os.path.join(packages_dir_path, cross_filename)
                # IF there is a cross, load that into a schema to be used *later*
                try:
                    cross_schema = load_yaml_from_wizard_xlsx(cross_fp, METADATA_SCHEMA_SHEET_NAME)
                except:
                    pass
            # end if there is a specific host or just the basic one

            sampletype_basename = sampletype_basename + _HAS_HOST_SUFFIX
        # end if this package is host-associated

        # everything should have a sampletype, so get that now
        _, sampletype_fp = _make_filename_and_path_from_base(packages_dir_path, sampletype_basename)
        sampletype_schema = load_yaml_from_wizard_xlsx(sampletype_fp, METADATA_SCHEMA_SHEET_NAME)
        result.update(sampletype_schema)
        result.update(cross_schema)
    # end if the package is something other than just the generic base

    return result


def get_package_info(packages_dir_path):
    sampletype_dicts_list = _get_sampletypes(packages_dir_path)
    host_dicts_list = _get_hosts(packages_dir_path)
    combination_dicts_list = _get_all_valid_package_combinations(sampletype_dicts_list, host_dicts_list)
    return sampletype_dicts_list, host_dicts_list, combination_dicts_list


def _get_sampletypes(packages_dir_path):
    result = []
    basename_generator = _get_trimmed_file_basenames_by_pattern(packages_dir_path, _SAMPLETYPE_PREFIX, _REQUIRED_EXTENSION)

    for curr_basename in basename_generator:
        curr_sampletype_name = curr_basename.replace(_HAS_HOST_SUFFIX, "")
        curr_sampletype_dict = _make_name_and_display_name_dict(curr_sampletype_name,
                                                                 curr_sampletype_name.replace("-", " "))
        curr_sampletype_dict[HOST_ASSOCIATED_KEY] = curr_basename.endswith(_HAS_HOST_SUFFIX)
        result.append(curr_sampletype_dict)

    return result


def _get_hosts(packages_dir_path):
    result = []
    basename_generator = _get_trimmed_file_basenames_by_pattern(packages_dir_path, _HOST_PREFIX, _REQUIRED_EXTENSION)
    for curr_host_name in basename_generator:
        result.append(_make_name_and_display_name_dict(curr_host_name, curr_host_name))

    return result


def _get_all_valid_package_combinations(sampletypes_dicts_list, host_dicts_list):
    result = []
    for curr_sampletype_dict in sampletypes_dicts_list:
        curr_sampletype_name, curr_sampletype_display_name =_get_name_and_display_name(curr_sampletype_dict)
        if curr_sampletype_dict[HOST_ASSOCIATED_KEY]:
            for curr_host_dict in host_dicts_list:
                curr_host_name, curr_host_display_name = _get_name_and_display_name(curr_host_dict)
                combination_dict = _make_name_and_display_name_dict(
                    "{0}{1}{2}".format(curr_sampletype_name, _CROSS_SYMBOL, curr_host_name),
                    "{0} {1}".format(curr_sampletype_display_name, curr_host_display_name)
                )
                result.append(combination_dict)
        else:
            result.append(curr_sampletype_dict)

    # add the base package
    result.append(_make_name_and_display_name_dict(_BASE_PACKAGE_NAME, "generic"))
    return result


def _get_trimmed_file_basenames_by_pattern(dir_path, prefix, extension):
    # get a list of the files in the dirpath that start with prefix and end with extension
    wildcard_pattern = os.path.join(dir_path, prefix + '*' + extension)
    matching_fps = glob.glob(wildcard_pattern)

    for curr_fp in matching_fps:
        curr_file_basename = os.path.splitext(os.path.basename(curr_fp))[0]
        curr_trimmed_basename = curr_file_basename.replace(prefix, "")
        yield curr_trimmed_basename


def _make_name_and_display_name_dict(name, display_name):
    return {NAME_KEY: name, DISPLAY_NAME_KEY: display_name}


def _get_name_and_display_name(names_dict):
    return names_dict[NAME_KEY], names_dict[DISPLAY_NAME_KEY]


def _make_host_filename_and_path(dir_path, host_name):
    host_basename = _HOST_PREFIX + host_name
    return _make_filename_and_path_from_base(dir_path, host_basename)


def _make_filename_and_path_from_base(dir_path, basename):
    filename = basename + _REQUIRED_EXTENSION
    fp = os.path.join(dir_path, filename)
    return filename, fp