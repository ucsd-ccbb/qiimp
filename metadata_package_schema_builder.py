from enum import Enum


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


class CerberusDataTypes(Enum):
    string = "string"
    integer = "integer"
    number = "number"


class SampleTypes(Enum):
    mucus = 'mucus',
    stool = 'stool'


# TODO: packages should have versions!
class PerSamplePackage:
    scientific_name = "Scientific_name"
    taxon_id = "TAXON_ID"
    env_biome = 'ENV_BIOME'
    env_feature = 'ENV_FEATURE'
    env_material = 'ENV_MATERIAL'
    env_package = "ENV_package"

    ebi_not_applicable = "Not applicable"
    ebi_not_collected = "Missing: Not collected"
    ebi_not_provided = "Missing: Not provided"
    ebi_restricted = "Missing: Restricted access"

    ebi_nulls = [ebi_not_applicable, ebi_not_collected, ebi_not_provided, ebi_restricted]

    generic_required_string_schema = {
        ValidationKeys.type.value: CerberusDataTypes.string.value,
        ValidationKeys.empty.value: False,
        ValidationKeys.required.value: True
    }

    generic_required_nonneg_int_schema = {
        ValidationKeys.type.value: CerberusDataTypes.integer.value,
        ValidationKeys.min_inclusive.value: 0,  # is Cerberus min exclusive or inclusive??
        ValidationKeys.empty.value: False,
        ValidationKeys.required.value: True
    }

    generic_required_nonneg_num_schema = {
        ValidationKeys.type.value: CerberusDataTypes.number.value,
        ValidationKeys.min_inclusive.value: 0,  # is Cerberus min exclusive or inclusive??
        ValidationKeys.empty.value: False,
        ValidationKeys.required.value: True
    }

    generic_ebi_nulls_schema = {
        ValidationKeys.type.value: CerberusDataTypes.string.value,
        ValidationKeys.allowed.value: ebi_nulls,
        ValidationKeys.required.value: True
    }

    generic_non_na_ebi_nulls_schema = {
        ValidationKeys.type.value: CerberusDataTypes.string.value,
        ValidationKeys.allowed.value: [ebi_not_provided, ebi_not_collected, ebi_restricted],
        ValidationKeys.required.value: True
    }

    generic_not_provided_null_schema = {
        ValidationKeys.type.value: CerberusDataTypes.string.value,
        ValidationKeys.allowed.value: [ebi_not_provided],
        ValidationKeys.required.value: True
    }

    required_nonneg_num_or_not_provided_schema = {
        ValidationKeys.required.value: True,
        ValidationKeys.anyof.value: [
            generic_required_nonneg_num_schema,
            generic_not_provided_null_schema
        ]
    }

    required_nonempty_string_or_not_provided_schema = {
        ValidationKeys.empty.value: False,
        ValidationKeys.required.value: True,
        ValidationKeys.anyof.value: [
            {
                ValidationKeys.type.value: CerberusDataTypes.string.value,
                ValidationKeys.forbidden.value: [ebi_not_applicable, ebi_not_collected, ebi_restricted],
                ValidationKeys.empty.value: False,
                ValidationKeys.required.value: True
            },
            generic_not_provided_null_schema
        ]
    }

    def __init__(self):
        self.schema = {
            'sample_name': {  # note that sample name should be unique within a study
                ValidationKeys.type.value: CerberusDataTypes.string.value,
                ValidationKeys.regex.value: '^[a-zA-Z0-9\.]+$',  # alphanumeric and period only,
                ValidationKeys.empty.value: False,
                ValidationKeys.required.value: True
            },
            'TITLE': {
            # note that title is required for each sample, but should be identical across all samples in study
                ValidationKeys.type.value: CerberusDataTypes.string.value,
                ValidationKeys.required.value: True  # is this correct?
            },
            'ANONYMIZED_NAME': {
                ValidationKeys.type.value: CerberusDataTypes.string.value,
                ValidationKeys.required.value: True  # is it correct that this should be here even if it is empty?
            },
            self.scientific_name: self.generic_required_string_schema,  # EXPECT to be overwritten by more specific one later
            self.taxon_id: self.generic_required_nonneg_int_schema,  # EXPECT to be overwritten by more specific one later
            "DESCRIPTION": {  # not adding a default here.  Need Qiita preprocesess to handle all-empty columns
                ValidationKeys.type.value: CerberusDataTypes.string.value,
                ValidationKeys.required.value: True
            },
            "sample_type": {  # this is NOT the complete list, just a placeholder.  Where does complete list come from?
                ValidationKeys.type.value: CerberusDataTypes.string.value,
                ValidationKeys.allowed.value: [SampleTypes.stool.value, SampleTypes.mucus.value],
                ValidationKeys.required.value: True
            },
            "geo_loc_name": {
                ValidationKeys.type.value: CerberusDataTypes.string.value,
                # I think this will need a regex to determine if format is valid; may also need additional validation to
                # ensure the validly-formatted string is actually a real place?
                ValidationKeys.empty.value: False,
                ValidationKeys.required.value: True
            },
            "ELEVATION": {
                ValidationKeys.type.value: CerberusDataTypes.number.value,
                # Could this be negative--say, at Dead Sea?  Is there a range constraint we should apply?
                ValidationKeys.empty.value: False,
                ValidationKeys.required.value: True
            },
            self.env_biome: self.generic_required_string_schema,  # EXPECT to be overwritten by more specific one later
            self.env_feature: self.generic_required_string_schema,  # EXPECT to be overwritten by more specific one later
            "LATITUDE": {
                ValidationKeys.type.value: CerberusDataTypes.string.value,
                # I think this will need a regex to determine if format is valid; may also need additional validation to
                # ensure the validly-formatted string is actually ... a possible place?
                ValidationKeys.empty.value: False,
                ValidationKeys.required.value: True
            },
            "LONGITUDE": {
                ValidationKeys.type.value: CerberusDataTypes.string.value,
                # I think this will need a regex to determine if format is valid; may also need additional validation to
                # ensure the validly-formatted string is actually ... a possible place?
                ValidationKeys.empty.value: False,
                ValidationKeys.required.value: True
            }
        }


class HumanPackage(PerSamplePackage):
    age = "age"
    age_units = "age_units"
    host_taxon_id = 'host_taxid'
    host_scientific_name = 'host_scientific_name'
    host_common_name = 'host_common_name'
    life_stage = 'life_stage'
    sex = 'sex'
    height = 'height'
    height_units = 'height_units'
    weight = 'weight'
    weight_units = 'weight_units'
    bmi = 'BMI'
    body_habitat = "body_habitat"
    body_site = "body_site"
    body_product = "body_product"

    urban_biome = 'urban biome'
    human_associated_habitat = 'human-associated habitat'
    human_taxon_id = 9606
    human_scientific_name = 'Homo sapiens'
    human_common_name = 'human'

    def __init__(self):
        super().__init__()
        self.schema.update({
        self.env_biome: {
            ValidationKeys.type.value: CerberusDataTypes.string.value,
            ValidationKeys.allowed.value: [self.urban_biome],
            ValidationKeys.default.value: self.urban_biome,
            ValidationKeys.required.value: True
        },
        self.env_feature: {
            ValidationKeys.type.value: CerberusDataTypes.string.value,
            ValidationKeys.allowed.value: [self.human_associated_habitat],
            ValidationKeys.default.value: self.human_associated_habitat,
            ValidationKeys.required.value: True
        },
        self.age: self.required_nonneg_num_or_not_provided_schema,
        self.age_units: self.required_nonempty_string_or_not_provided_schema,
        self.host_taxon_id: {
            ValidationKeys.type.value: CerberusDataTypes.integer.value,
            ValidationKeys.allowed.value: [self.human_taxon_id],
            ValidationKeys.default.value: self.human_taxon_id,
            ValidationKeys.required.value: True
        },
        self.host_scientific_name: {
            ValidationKeys.type.value: CerberusDataTypes.string.value,
            ValidationKeys.allowed.value: [self.human_scientific_name],
            ValidationKeys.default.value: self.human_scientific_name,
            ValidationKeys.required.value: True
        },
        self.host_common_name: {
            ValidationKeys.type.value: CerberusDataTypes.string.value,
            ValidationKeys.allowed.value: [self.human_common_name],
            ValidationKeys.default.value: self.human_common_name,
            ValidationKeys.required.value: True
        },
        self.life_stage: {
            ValidationKeys.type.value: CerberusDataTypes.string.value,
            ValidationKeys.required.value: True,
            ValidationKeys.anyof.value: [
                {ValidationKeys.allowed.value: ['adult', 'juvenile', 'infant']},
                self.generic_non_na_ebi_nulls_schema
            ]
        },
        self.sex: {
            ValidationKeys.type.value: CerberusDataTypes.string.value,
            ValidationKeys.required.value: True,
            ValidationKeys.anyof.value: [
                {ValidationKeys.allowed.value: ['female', 'male']},
                self.generic_non_na_ebi_nulls_schema
            ]
        },
        self.height: self.required_nonneg_num_or_not_provided_schema,
        self.height_units: self.required_nonempty_string_or_not_provided_schema,
        self.weight: self.required_nonneg_num_or_not_provided_schema,
        self.weight_units: self.required_nonempty_string_or_not_provided_schema,
        self.bmi: {
            ValidationKeys.required.value: True,
            ValidationKeys.anyof.value: [
                self.generic_required_nonneg_num_schema,
                self.generic_ebi_nulls_schema
            ]
        },
        self.body_habitat: self.generic_required_string_schema,  # EXPECT to be overwritten by more specific one later
        self.body_site: self.generic_required_string_schema,  # EXPECT to be overwritten by more specific one later
        self.body_product: self.generic_required_string_schema  # EXPECT to be overwritten by more specific one later
    })


class HumanVaginaPackage(HumanPackage):
    human_vag_metagenome_sci_name = "human vaginal metagenome"
    human_vag_metagenome_tax_id = 1632839
    hs_vag_env_pkg = 'human-vaginal'
    uberon_repro_sys = "UBERON:reproductive system"
    uberon_vagina = "UBERON:vagina"
    uberon_mucus = "UBERON:mucus"

    def __init__(self):
        super().__init__()

        self.schema.update({
            self.scientific_name: {
                ValidationKeys.type.value: CerberusDataTypes.string.value,
                ValidationKeys.allowed.value: [self.human_vag_metagenome_sci_name],
                ValidationKeys.default.value: self.human_vag_metagenome_sci_name,
                ValidationKeys.required.value: True
            },
            self.taxon_id: {
                ValidationKeys.type.value: CerberusDataTypes.integer.value,
                ValidationKeys.allowed.value: [self.human_vag_metagenome_tax_id],
                ValidationKeys.default.value: self.human_vag_metagenome_tax_id,
                ValidationKeys.required.value: True
            },
            self.env_material: {
                ValidationKeys.type.value: CerberusDataTypes.string.value,
                ValidationKeys.allowed.value: [SampleTypes.mucus.value],
                ValidationKeys.default.value: SampleTypes.mucus.value,
                ValidationKeys.required.value: True
            },
            self.env_package: {
                ValidationKeys.type.value: CerberusDataTypes.string.value,
                ValidationKeys.allowed.value: [self.hs_vag_env_pkg],
                ValidationKeys.default.value: self.hs_vag_env_pkg,
                ValidationKeys.required.value: True
            },
            self.body_habitat: {
                ValidationKeys.type.value: CerberusDataTypes.string.value,
                ValidationKeys.allowed.value: [self.uberon_repro_sys],
                ValidationKeys.default.value: self.uberon_repro_sys,
                ValidationKeys.required.value: True
            },
            self.body_site: {
                ValidationKeys.type.value: CerberusDataTypes.string.value,
                ValidationKeys.allowed.value: [self.uberon_vagina],
                ValidationKeys.default.value: self.uberon_vagina,
                ValidationKeys.required.value: True
            },
            self.body_product: {
                ValidationKeys.type.value: CerberusDataTypes.string.value,
                ValidationKeys.allowed.value: [self.uberon_mucus],
                ValidationKeys.default.value: self.uberon_mucus,
                ValidationKeys.required.value: True
            }
        })

# host_associated_schema = {
#     age: {},
#     age_units: {},
#     host_taxon_id: generic_required_nonneg_int_schema,
#     host_scientific_name: generic_required_string_schema,
#     host_common_name: generic_required_string_schema,
#     life_stage: {},
#     sex: {},
#     height: {},
#     height_units: {},
#     weight: {},
#     weight_units: {},
#     bmi: {},
#     body_habitat: {},
#     body_site: {},
#     body_product: {}
# }
#
# human_gut_metagenome_taxonomy_schema = {
#     scientific_name: {
#         ValidationKeys.type.value: CerberusDataTypes.string.value,
#         ValidationKeys.allowed.value: ["human gut metagenome"],
#         ValidationKeys.required.value: True
#     },
#     taxon_id: {
#         ValidationKeys.type.value: CerberusDataTypes.integer.value,
#         ValidationKeys.allowed.value: [408170],
#         ValidationKeys.required.value: True
#     }
# }
#
# human_vagina_metagenome_taxonomy_schema = {
#     scientific_name: {
#         ValidationKeys.type.value: CerberusDataTypes.string.value,
#         ValidationKeys.allowed.value: ["human vaginal metagenome"],
#         ValidationKeys.required.value: True
#     },
#     taxon_id: {
#         ValidationKeys.type.value: CerberusDataTypes.integer.value,
#         ValidationKeys.allowed.value: [1632839],
#         ValidationKeys.required.value: True
#     }
# }
