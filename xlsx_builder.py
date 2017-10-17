import re

import unicodedata
import xlsxwriter
import yaml

import xlsx_basics
import xlsx_metadata_grid_builder
import xlsx_static_grid_builder
import xlsx_dynamic_grid_builder


def write_workbook(study_name, schema_dict):
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
    metadata_worksheet = xlsx_basics.MetadataWorksheet(workbook, num_columns, num_samples)
    xlsx_metadata_grid_builder.write_metadata_grid(metadata_worksheet, schema_dict)

    # write validation worksheet
    validation_worksheet = xlsx_static_grid_builder.ValidationWorksheet(workbook, num_columns, num_samples)
    index_and_range_str_tuple_by_header_dict = xlsx_static_grid_builder.write_static_validation_grid_and_helpers(
        validation_worksheet, schema_dict)
    xlsx_dynamic_grid_builder.write_dynamic_validation_grid(
        validation_worksheet, index_and_range_str_tuple_by_header_dict)

    # write schema worksheet
    schema_worksheet = xlsx_basics.create_worksheet(workbook, "metadata_schema")
    schema_worksheet.write_string("A1", yaml.dump(schema_dict))

    # close workbook
    workbook.close()
    return file_name


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
  - allowed: [not applicable, 'missing: not collected', 'missing: not provided', 'missing: restricted access']
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
    forbidden: [not applicable, 'missing: not collected', 'missing: restricted access']
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
disease state:
  anyof:
  - allowed: [not applicable, 'missing: not provided']
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
  - allowed: [not applicable, 'missing: not collected']
    default: '0.5'
    empty: false
    required: true
    type: string
  - {min: '0.5', required: true, type: number}
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
life_stage:
  anyof:
  - allowed: [adult, juvenile, infant]
    required: true
    type: string  
  - &id005
    allowed: ['missing: not provided', 'missing: not collected', 'missing: restricted access']
    required: true
    type: string
sample_name: {empty: false, regex: '^[a-zA-Z0-9\.]+$', required: true, type: string}
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
    write_workbook("validation_wksht_test", yaml.load(hs_vaginal_fixed_schema_yaml))
