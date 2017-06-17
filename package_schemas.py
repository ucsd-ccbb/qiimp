import yaml

# obviously must be refactored
atype = "type"
astring = "string"
aninteger = "integer"
anumber = "number"
required = "required"
allowed = "allowed"
default = "default"
empty = "empty"
anyof = "anyof"
amin = "min"
amax = "max"
forbidden = "forbidden"
regex = "regex"


def ridiculously_large_temporary_function():
    scientific_name = "Scientific_name"
    taxon_id = "TAXON_ID"
    env_biome = 'ENV_BIOME'
    env_feature = 'ENV_FEATURE'
    env_material = 'ENV_MATERIAL'
    env_package = "ENV_package"
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
    human_vag_metagenome_sci_name = "human vaginal metagenome"
    human_vag_metagenome_tax_id = 1632839
    mucus = 'mucus'
    hs_vag_env_pkg = 'human-vaginal'
    uberon_repro_sys = "UBERON:reproductive system"
    uberon_vagina = "UBERON:vagina"
    uberon_mucus = "UBERON:mucus"

    ebi_not_applicable = "Not applicable"
    ebi_not_collected = "Missing: Not collected"
    ebi_not_provided = "Missing: Not provided"
    ebi_restricted = "Missing: Restricted access"

    ebi_nulls = [ebi_not_applicable, ebi_not_collected, ebi_not_provided, ebi_restricted]

    generic_required_string_schema = {
        atype: astring,
        empty: False,
        required: True
    }

    generic_required_nonneg_int_schema = {
        atype: aninteger,
        amin: 0,  # is Cerberus min exclusive or inclusive??
        empty: False,
        required: True
    }

    generic_required_nonneg_num_schema = {
        atype: anumber,
        amin: 0,  # is Cerberus min exclusive or inclusive??
        empty: False,
        required: True
    }

    generic_ebi_nulls_schema = {
        atype: astring,
        allowed: ebi_nulls,
        required: True
    }

    generic_non_na_ebi_nulls_schema = {
        atype: astring,
        allowed: [ebi_not_provided, ebi_not_collected, ebi_restricted],
        required: True
    }

    generic_not_provided_null_schema = {
        atype: astring,
        allowed: [ebi_not_provided],
        required: True
    }

    required_nonneg_num_or_not_provided_schema = {
        required: True,
        anyof: [
            generic_required_nonneg_num_schema,
            generic_not_provided_null_schema
        ]
    }

    required_nonempty_string_or_not_provided_schema = {
        empty: False,
        required: True,
        anyof: [
            {
                atype: astring,
                forbidden: [ebi_not_applicable, ebi_not_collected, ebi_restricted],
                empty: False,
                required: True
            },
            generic_not_provided_null_schema
        ]
    }

    per_sample_general_schema = {
        'sample_name': {  # note that sample name should be unique within a study
            atype: astring,
            regex: '^[a-zA-Z0-9\.]+$',  # alphanumeric and period only,
            empty: False,
            required: True
        },
        'TITLE': {  # note that title is required for each sample, but should be identical across all samples in study
            atype: astring,
            required: True  # is this correct?
        },
        'ANONYMIZED_NAME': {
            atype: astring,
            required: True  # is it correct that this should be here even if it is empty?
        },
        scientific_name: generic_required_string_schema,  # EXPECT to be overwritten by more specific one later
        taxon_id: generic_required_nonneg_int_schema,  # EXPECT to be overwritten by more specific one later
        "DESCRIPTION": {  # not adding a default here.  Need Qiita preprocesess to handle all-empty columns
            atype: astring,
            required: True
        },
        "sample_type": {  # this is NOT the complete list, just a placeholder.  Where does complete list come from?
            atype: astring,
            allowed: ['stool', mucus],
            required: True
        },
        "geo_loc_name": {
            atype: astring,
            # I think this will need a regex to determine if format is valid; may also need additional validation to
            # ensure the validly-formatted string is actually a real place?
            empty: False,
            required: True
        },
        "ELEVATION": {
            atype: anumber,
            # Could this be negative--say, at Dead Sea?  Is there a range constraint we should apply?
            empty: False,
            required: True
        },
        env_biome: generic_required_string_schema,  # EXPECT to be overwritten by more specific one later
        env_feature: generic_required_string_schema,  # EXPECT to be overwritten by more specific one later
        "LATITUDE": {
            atype: astring,
            # I think this will need a regex to determine if format is valid; may also need additional validation to
            # ensure the validly-formatted string is actually ... a possible place?
            empty: False,
            required: True
        },
        "LONGITUDE": {
            atype: astring,
            # I think this will need a regex to determine if format is valid; may also need additional validation to
            # ensure the validly-formatted string is actually ... a possible place?
            empty: False,
            required: True
        }
    }

    human_schema = per_sample_general_schema.copy()
    human_schema.update({
        env_biome: {
            atype: astring,
            allowed: [urban_biome],
            default: urban_biome,
            required: True
        },
        env_feature: {
            atype: astring,
            allowed: [human_associated_habitat],
            default: human_associated_habitat,
            required: True
        },
        age: required_nonneg_num_or_not_provided_schema,
        age_units: required_nonempty_string_or_not_provided_schema,
        host_taxon_id: {
            atype: aninteger,
            allowed: [human_taxon_id],
            default: human_taxon_id,
            required: True
        },
        host_scientific_name: {
            atype: astring,
            allowed: [human_scientific_name],
            default: human_scientific_name,
            required: True
        },
        host_common_name: {
            atype: astring,
            allowed: [human_common_name],
            default: human_common_name,
            required: True
        },
        life_stage: {
            atype: astring,
            required: True,
            anyof: [
                {allowed: ['adult', 'juvenile', 'infant']},
                generic_non_na_ebi_nulls_schema
            ]
        },
        sex: {
            atype: astring,
            required: True,
            anyof: [
                {allowed: ['female', 'male']},
                generic_non_na_ebi_nulls_schema
            ]
        },
        height: required_nonneg_num_or_not_provided_schema,
        height_units: required_nonempty_string_or_not_provided_schema,
        weight: required_nonneg_num_or_not_provided_schema,
        weight_units: required_nonempty_string_or_not_provided_schema,
        bmi: {
            required: True,
            anyof: [
                generic_required_nonneg_num_schema,
                generic_ebi_nulls_schema
            ]
        },
        body_habitat: generic_required_string_schema,  # EXPECT to be overwritten by more specific one later
        body_site: generic_required_string_schema,  # EXPECT to be overwritten by more specific one later
        body_product:generic_required_string_schema  # EXPECT to be overwritten by more specific one later
    })

    human_vaginal_schema = human_schema.copy()
    human_vaginal_schema.update(
        {
            scientific_name: {
                atype: astring,
                allowed: [human_vag_metagenome_sci_name],
                default: human_vag_metagenome_sci_name,
                required: True
            },
            taxon_id: {
                atype: aninteger,
                allowed: [human_vag_metagenome_tax_id],
                default: human_vag_metagenome_tax_id,
                required: True
            },
            env_material: {
                atype: astring,
                allowed: [mucus],
                default: mucus,
                required: True
            },
            env_package: {
                atype: astring,
                allowed: [hs_vag_env_pkg],
                default: hs_vag_env_pkg,
                required: True
            },
            body_habitat: {
                atype: astring,
                allowed: [uberon_repro_sys],
                default: uberon_repro_sys,
                required: True
            },
            body_site: {
                atype: astring,
                allowed: [uberon_vagina],
                default: uberon_vagina,
                required: True
            },
            body_product: {
                atype: astring,
                allowed: [uberon_mucus],
                default: uberon_mucus,
                required: True
            }
        }
    )

    return yaml.dump(human_vaginal_schema)

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
#         atype: astring,
#         allowed: ["human gut metagenome"],
#         required: True
#     },
#     taxon_id: {
#         atype: aninteger,
#         allowed: [408170],
#         required: True
#     }
# }
#
# human_vagina_metagenome_taxonomy_schema = {
#     scientific_name: {
#         atype: astring,
#         allowed: ["human vaginal metagenome"],
#         required: True
#     },
#     taxon_id: {
#         atype: aninteger,
#         allowed: [1632839],
#         required: True
#     }
# }
