import re

import unicodedata
import xlsxwriter
import yaml

import xlsx_basics
import xlsx_metadata_grid_builder
import xlsx_static_grid_builder
import xlsx_dynamic_grid_builder


def write_workbook(study_name, schema_dict):
    num_samples = 250  # TODO: add real code to get in from interface
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
    hs_vaginal_fixed_schema_yaml = """ANONYMIZED_NAME: {required: true, type: string}
BMI:
  anyof:
  - &id001 {empty: false, min: 0, required: true, type: number}
  - allowed: [Not applicable, 'Missing: Not collected', 'Missing: Not provided', 'Missing:
        Restricted access']
    required: true
    type: string
  required: true
DESCRIPTION: {required: true, type: string}
ELEVATION: {empty: false, required: true, type: number}
ENV_BIOME:
  allowed: [urban biome]
  default: urban biome
  required: true
  type: string
ENV_FEATURE:
  allowed: [human-associated habitat]
  default: human-associated habitat
  required: true
  type: string
ENV_MATERIAL:
  allowed: [mucus]
  default: mucus
  required: true
  type: string
ENV_package:
  allowed: [human-vaginal]
  default: human-vaginal
  required: true
  type: string
LATITUDE: {empty: false, required: true, type: string}
LONGITUDE: {empty: false, required: true, type: string}
Scientific_name:
  allowed: [human vaginal metagenome]
  default: human vaginal metagenome
  required: true
  type: string
TAXON_ID:
  allowed: [1632839]
  default: 1632839
  required: true
  type: integer
TITLE: {required: true, type: string}
age: &id003
  anyof:
  - *id001
  - &id002
    allowed: ['Missing: Not provided']
    required: true
    type: string
  required: true
age_units: &id004
  anyof:
  - empty: false
    forbidden: [Not applicable, 'Missing: Not collected', 'Missing: Restricted access']
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
  - allowed: [Not applicable, 'Missing: Not provided']
    default: 'Missing: Not provided'
    empty: false
    required: true
    type: string
  - allowed: [mild, severe]
    empty: false
    required: true
    type: string
dosage:
  anyof:
  - allowed: [Not applicable, 'Missing: Not collected']
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
    allowed: ['Missing: Not provided', 'Missing: Not collected', 'Missing: Restricted
        access']
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
