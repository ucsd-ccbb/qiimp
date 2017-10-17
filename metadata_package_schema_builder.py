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
    Text = "string"
    Integer = "integer"
    Decimal = "number"


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
    def __init__(self):
        self.schema = {}
