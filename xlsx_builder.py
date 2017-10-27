import re
import os

import unicodedata
import xlsxwriter
import yaml

import xlsx_basics
import xlsx_metadata_grid_builder
import xlsx_validation_builder
import xlsx_static_grid_builder
import xlsx_dynamic_grid_builder
import regex_handler


def write_workbook(study_name, schema_dict, a_regex_handler):
    num_allowable_samples = 1000
    # TODO: either expand code to use num_samples and add real code to get in from interface, or take out unused hook
    num_samples = 0
    num_columns = len(schema_dict.keys())

    # create workbook
    file_base_name = slugify(study_name)
    file_name = '{0}.xlsx'.format(file_base_name)
    workbook = xlsxwriter.Workbook(file_name, {'strings_to_numbers': False,
                                               'strings_to_formulas': True,
                                               'strings_to_urls': True})

    # write metadata worksheet
    metadata_worksheet = xlsx_basics.MetadataWorksheet(workbook, num_columns, num_samples, a_regex_handler,
                                                       num_allowable_samples=num_allowable_samples)
    xlsx_metadata_grid_builder.write_metadata_grid(metadata_worksheet, schema_dict)

    # write validation worksheet
    validation_worksheet = xlsx_static_grid_builder.ValidationWorksheet(workbook, num_columns, num_samples,
                                                                        a_regex_handler)
    index_and_range_str_tuple_by_header_dict = xlsx_static_grid_builder.write_static_validation_grid_and_helpers(
        validation_worksheet, schema_dict)
    xlsx_dynamic_grid_builder.write_dynamic_validation_grid(
        validation_worksheet, index_and_range_str_tuple_by_header_dict)

    # write descriptions worksheet
    descriptions_worksheet = DescriptionWorksheet(workbook, num_columns, num_samples, a_regex_handler)
    xlsx_basics.write_header(descriptions_worksheet, "field name", 0)
    xlsx_basics.write_header(descriptions_worksheet, "field description", 1)
    sorted_keys = xlsx_basics.sort_keys(schema_dict)
    for field_index, field_name in enumerate(sorted_keys):
        row_num = field_index + 1 + 1  # plus 1 to move past name row, and plus 1 again because row nums are 1-based
        field_specs_dict = schema_dict[field_name]
        message = xlsx_validation_builder.get_field_constraint_description(field_specs_dict, a_regex_handler)
        descriptions_worksheet.worksheet.write("A{0}".format(row_num), field_name, metadata_worksheet.bold_format)
        descriptions_worksheet.worksheet.write("B{0}".format(row_num), message)

    # write schema worksheet
    schema_worksheet = xlsx_basics.create_worksheet(workbook, "metadata_schema")
    schema_worksheet.write_string("A1", yaml.dump(schema_dict))

    # close workbook
    workbook.close()
    return file_name


class DescriptionWorksheet(xlsx_basics.MetadataWorksheet):
    def __init__(self, workbook, num_attributes, num_samples, a_regex_handler):
        super().__init__(workbook, num_attributes, num_samples, a_regex_handler, make_sheet=False)

        self.worksheet = xlsx_basics.create_worksheet(self.workbook, "field descriptions",
                                                      self._permissive_protect_options)


# very slight modification of django code at https://github.com/django/django/blob/master/django/utils/text.py#L413
def slugify(value, allow_unicode=False):
    """
    Convert to ASCII if 'allow_unicode' is False. Convert spaces to hyphens.
    Remove characters that aren't alphanumerics, underscores, or hyphens.
    Convert to lowercase. Also strip leading and trailing whitespace.
    """
    value = str(value)
    if allow_unicode:
        value = unicodedata.normalize('NFKC', value)
    else:
        value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode('ascii')
    value = re.sub(r'[^\w\s-]', '', value).strip().lower()
    return re.sub(r'[-\s]+', '-', value)


# TODO: Remove--only for POC testing
if __name__ == "__main__":
    hs_vaginal_fixed_schema_yaml = """anonymized_name: {required: true, type: string}
bmi:
  anyof:
  - &id001 {empty: false, min: 0, required: true, type: number}
  - allowed: ['not applicable', 'missing: not collected', 'missing: not provided', 'missing: restricted access']
    required: true
    type: string
  required: true
description: {required: true, type: string}
elevation: {empty: false, required: true, type: number}
env_biome:
  allowed: [urban biome]
  default: urban biome
  required: true
  type: string
env_feature:
  allowed: [human-associated habitat]
  default: human-associated habitat
  required: true
  type: string
env_material:
  allowed: [mucus]
  default: mucus
  required: true
  type: string
env_package:
  allowed: [human-vaginal]
  default: human-vaginal
  required: true
  type: string
latitude: {empty: false, required: true, type: string}
longitude: {empty: false, required: true, type: string}
scientific_name:
  allowed: [human vaginal metagenome]
  default: human vaginal metagenome
  required: true
  type: string
taxon_id:
  allowed: [1632839]
  default: 1632839
  required: true
  type: integer
title: {required: true, type: string}
age: &id003
  anyof:
  - *id001
  - &id002
    allowed: ['missing: not provided']
    required: true
    type: string
  required: true
age_units: &id004
  anyof:
  - empty: false
    forbidden: ['not applicable', 'missing: not collected', 'missing: restricted access']
    required: true
    type: string
  - *id002
  empty: false
  required: true
body_habitat:
  allowed: ['UBERON:reproductive system']
  default: UBERON:reproductive system
  required: true
  type: string
body_product:
  allowed: ['UBERON:mucus']
  default: UBERON:mucus
  required: true
  type: string
body_site:
  allowed: ['UBERON:vagina']
  default: UBERON:vagina
  required: true
  type: string
collection_timestamp:
  anyof:
  - allowed: ['missing: not provided']
    default: 'missing: not provided'
    empty: false
    required: true
    type: string
  - regex: '^([0-9]{1,4})(?:-([0-9]{1,2})(?:-([0-9]{1,2})(?: ([0-9]{1,2})(?::([0-9]{1,2})(?::([0-9]{1,2}))?)?)?)?)?$'
    empty: false
    required: true
    type: datetime
other_timestamp:
  anyof:
  - allowed: ['missing: not provided']
    default: 'missing: not provided'
    empty: false
    required: true
    type: string
  - regex: '^([0-9]{1,4})(?:-([0-9]{1,2})(?:-([0-9]{1,2})(?: ([0-9]{1,2})(?::([0-9]{1,2})(?::([0-9]{1,2}))?)?)?)?)?$'
    empty: false
    required: true
    type: datetime
    min: '2011'
    max: '2012-06-30'
disease state:
  anyof:
  - allowed: ['not applicable', 'missing: not provided']
    default: 'missing: not provided'
    empty: false
    required: true
    type: string
  - allowed: [mild, severe]
    empty: false
    required: true
    type: string
dosage:
  anyof:
  - allowed: ['not applicable', 'missing: not collected']
    empty: false
    required: true
    type: string
  - {min: '0.5', required: true, type: number, default: '0.5'}
geo_loc_name: {empty: false, required: true, type: string}
height: *id003
height_units: *id004
host_common_name:
  allowed: [human]
  default: human
  required: true
  type: string
host_scientific_name:
  allowed: [Homo sapiens]
  default: Homo sapiens
  required: true
  type: string
host_taxid:
  allowed: [9606]
  default: 9606
  required: true
  type: integer
is a patient:
  allowed: [Y, N]
  empty: false
  required: true
  type: string
latitude:
  anyof:
  - allowed: ['not applicable', 'missing: not collected']
    empty: false
    required: true
    type: string
  - {min: -90, max: 90, required: true, type: number}
life_stage:
  anyof:
  - allowed: [adult, juvenile, infant]
    required: true
    type: string  
  - &id005
    allowed: ['missing: not provided', 'missing: not collected', 'missing: restricted access']
    required: true
    type: string
latitude:
  anyof:
  - allowed: ['not applicable', 'missing: not collected']
    empty: false
    required: true
    type: string
  - {min: -90, max: 90, required: true, type: number}
sample_name: {empty: false, regex: '^[a-zA-Z0-9\.]+$', required: true, type: string, unique: true}
sample_type:
  allowed: [stool, mucus]
  required: true
  type: string
sex:
  anyof:
  - allowed: [female, male]
    required: true
    type: string  
  - *id005
weight: *id003
weight_units: *id004
"""
    a_regex_handler = regex_handler.RegexHandler(os.path.join(os.path.dirname(__file__), 'regex_definitions.yaml'))
    write_workbook("validation_wksht_test", yaml.load(hs_vaginal_fixed_schema_yaml), a_regex_handler)
