from enum import Enum

# NOTE: The xlsx_validation_builder.py module's handling of allowed values requires that the
# data type of a schema NOT be defined outside of an anyof, EVEN IF the type of all of the anyof options are the same.

# Also note, from the Cerberus documentation: "String fields with empty values will still be validated [i.e., treated
# as valid], even when required is set to True. If you don’t want to accept empty values, see the empty rule [i.e.,
# add an "empty": False rule to the schema]." (http://docs.python-cerberus.org/en/stable/validation-rules.html#required)


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
    scientific_name = "scientific_name"
    taxon_id = "taxon_id"
    env_biome = 'env_biome'
    env_feature = 'env_feature'
    env_material = 'env_material'
    env_package = "env_package"

    # values from https://www.ebi.ac.uk/ena/about/missing-values-reporting
    ebi_not_applicable = "not applicable"
    ebi_not_collected = "missing: not collected"
    ebi_not_provided = "missing: not provided"
    ebi_restricted = "missing: restricted access"

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
        ValidationKeys.empty.value: False,
        ValidationKeys.required.value: True
    }

    generic_non_na_ebi_nulls_schema = {
        ValidationKeys.type.value: CerberusDataTypes.string.value,
        ValidationKeys.allowed.value: [ebi_not_provided, ebi_not_collected, ebi_restricted],
        ValidationKeys.empty.value: False,
        ValidationKeys.required.value: True
    }

    generic_not_provided_null_schema = {
        ValidationKeys.type.value: CerberusDataTypes.string.value,
        ValidationKeys.allowed.value: [ebi_not_provided],
        ValidationKeys.empty.value: False,
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
        self._default_location = SanDiego()

        self.schema = {
            'sample_name': {  # note that sample name should be unique within a study
                ValidationKeys.type.value: CerberusDataTypes.string.value,
                ValidationKeys.regex.value: '^[a-zA-Z0-9\.]+$',  # alphanumeric and period only,
                ValidationKeys.empty.value: False,
                ValidationKeys.required.value: True
            },
            'title': {
            # note that title is required for each sample, but should be identical across all samples in study
                ValidationKeys.type.value: CerberusDataTypes.string.value,
                ValidationKeys.empty.value: False,
                ValidationKeys.required.value: True  # is this correct?
            },
            'anonymized_name': {
                ValidationKeys.type.value: CerberusDataTypes.string.value,
                ValidationKeys.empty.value: False,
                ValidationKeys.required.value: True  # is it correct that this should be here even if it is empty?
            },
            self.scientific_name: self.generic_required_string_schema,  # EXPECT to be overwritten by more specific one later
            self.taxon_id: self.generic_required_nonneg_int_schema,  # EXPECT to be overwritten by more specific one later
            "description": {  # not adding a default here.  Need Qiita preprocesess to handle all-empty columns
                ValidationKeys.type.value: CerberusDataTypes.string.value,
                ValidationKeys.empty.value: False,
                ValidationKeys.required.value: True
            },
            "sample_type": {  # this is NOT the complete list, just a placeholder.  Where does complete list come from?
                ValidationKeys.type.value: CerberusDataTypes.string.value,
                ValidationKeys.allowed.value: [SampleTypes.stool.value, SampleTypes.mucus.value],
                ValidationKeys.empty.value: False,
                ValidationKeys.required.value: True
            },
            "geo_loc_name": {
                ValidationKeys.type.value: CerberusDataTypes.string.value,
                # I think this will need a regex to determine if format is valid; may also need additional validation to
                # ensure the validly-formatted string is actually a real place?
                ValidationKeys.default.value: self._default_location.geo_loc_name,
                ValidationKeys.empty.value: False,
                ValidationKeys.required.value: True
            },
            "elevation": {
                ValidationKeys.type.value: CerberusDataTypes.number.value,
                # Could this be negative--say, at Dead Sea?  Is there a range constraint we should apply?
                ValidationKeys.default.value: self._default_location.elevation,
                ValidationKeys.empty.value: False,
                ValidationKeys.required.value: True
            },
            self.env_biome: self.generic_required_string_schema,  # EXPECT to be overwritten by more specific one later
            self.env_feature: self.generic_required_string_schema,  # EXPECT to be overwritten by more specific one later
            "latitude": {
                ValidationKeys.type.value: CerberusDataTypes.number.value,
                # I think this will need a regex to determine if format is valid; may also need additional validation to
                # ensure the validly-formatted string is actually ... a possible place?
                ValidationKeys.default.value: self._default_location.latitude,
                ValidationKeys.empty.value: False,
                ValidationKeys.required.value: True
            },
            "longitude": {
                ValidationKeys.type.value: CerberusDataTypes.number.value,
                # I think this will need a regex to determine if format is valid; may also need additional validation to
                # ensure the validly-formatted string is actually ... a possible place?
                ValidationKeys.default.value: self._default_location.longitude,
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
    bmi = 'bmi'
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
            ValidationKeys.empty.value: False,
            ValidationKeys.required.value: True
        },
        self.env_feature: {
            ValidationKeys.type.value: CerberusDataTypes.string.value,
            ValidationKeys.allowed.value: [self.human_associated_habitat],
            ValidationKeys.default.value: self.human_associated_habitat,
            ValidationKeys.empty.value: False,
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
            ValidationKeys.empty.value: False,
            ValidationKeys.required.value: True
        },
        self.host_common_name: {
            ValidationKeys.type.value: CerberusDataTypes.string.value,
            ValidationKeys.allowed.value: [self.human_common_name],
            ValidationKeys.default.value: self.human_common_name,
            ValidationKeys.empty.value: False,
            ValidationKeys.required.value: True
        },
        self.life_stage: {
            ValidationKeys.required.value: True,
            ValidationKeys.anyof.value: [
                {
                    ValidationKeys.type.value: CerberusDataTypes.string.value,
                    ValidationKeys.allowed.value: ['adult', 'juvenile', 'infant'],
                    ValidationKeys.empty.value: False
                },
                self.generic_non_na_ebi_nulls_schema
            ]
        },
        self.sex: {
            ValidationKeys.required.value: True,
            ValidationKeys.anyof.value: [
                {
                    ValidationKeys.type.value: CerberusDataTypes.string.value,
                    ValidationKeys.allowed.value: ['female', 'male'],
                    ValidationKeys.empty.value: False
                },
                self.generic_non_na_ebi_nulls_schema
            ]
        },
        self.height: self.required_nonneg_num_or_not_provided_schema,
        self.height_units: self.required_nonempty_string_or_not_provided_schema,
        self.weight: self.required_nonneg_num_or_not_provided_schema,
        self.weight_units: {
            ValidationKeys.type.value: CerberusDataTypes.string.value,
            ValidationKeys.allowed.value: [ValidationKeys.UnitTypes.kilograms.value],
            ValidationKeys.default.value: ValidationKeys.UnitTypes.kilograms.value,
            ValidationKeys.empty.value: False,
            ValidationKeys.required.value: True
        },
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
                ValidationKeys.empty.value: False,
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
                ValidationKeys.empty.value: False,
                ValidationKeys.required.value: True
            },
            self.env_package: {
                ValidationKeys.type.value: CerberusDataTypes.string.value,
                ValidationKeys.allowed.value: [self.hs_vag_env_pkg],
                ValidationKeys.default.value: self.hs_vag_env_pkg,
                ValidationKeys.empty.value: False,
                ValidationKeys.required.value: True
            },
            self.body_habitat: {
                ValidationKeys.type.value: CerberusDataTypes.string.value,
                ValidationKeys.allowed.value: [self.uberon_repro_sys],
                ValidationKeys.default.value: self.uberon_repro_sys,
                ValidationKeys.empty.value: False,
                ValidationKeys.required.value: True
            },
            self.body_site: {
                ValidationKeys.type.value: CerberusDataTypes.string.value,
                ValidationKeys.allowed.value: [self.uberon_vagina],
                ValidationKeys.default.value: self.uberon_vagina,
                ValidationKeys.empty.value: False,
                ValidationKeys.required.value: True
            },
            self.body_product: {
                ValidationKeys.type.value: CerberusDataTypes.string.value,
                ValidationKeys.allowed.value: [self.uberon_mucus],
                ValidationKeys.default.value: self.uberon_mucus,
                ValidationKeys.empty.value: False,
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
