import datetime
import warnings


class GenericField:
    @property
    def field_name(self):
        return self._field_name

    @field_name.setter
    def field_name(self, value):
        self._set_with_overwrite_warning("field_name", value)

    @property
    def data_type(self):
        return self._data_type

    @data_type.setter
    def data_type(self, value):
        if value not in [str, int, float, datetime.datetime, None]:
            raise ValueError("Unrecognized data type: {0}".format(value))
        self._set_with_overwrite_warning("data_type", value)

    @property
    def allowed_values(self):
        return self._allowed_values

    @property
    def default_value(self):
        return self._default_value

    @default_value.setter
    def default_value(self, value):
        self._set_with_overwrite_warning("default_value", value)

    @property
    def maximum(self):
        return self._maximum

    @maximum.setter
    def maximum(self, value):
        self._set_with_overwrite_warning("maximum", value)

    @property
    def minimum(self):
        return self._minimum

    @minimum.setter
    def minimum(self, value):
        self._set_with_overwrite_warning("minimum", value)

    @property
    def unit(self):
        return self._unit

    @unit.setter
    def unit(self, value):
        self._set_with_overwrite_warning("unit", value)

    def __init__(self, field_name=None, data_type=None, allowed_values=None,
                 default_value=None, maximum=None, minimum=None, unit=None):
        self._field_name = field_name
        self._data_type = data_type
        self._allowed_values = [] if allowed_values is None else allowed_values
        self._default_value = default_value
        self._maximum = maximum
        self._minimum = minimum
        self._unit = unit

    def update_definitions(self, other_field):
        if other_field.allowed_values is not None:
            self._allowed_values.extend(other_field.allowed_values)

        attr_names = ["default_value", "maximum", "minimum", "data_type"]
        for curr_attr_name in attr_names:
            other_attr_value = getattr(other_field, curr_attr_name)
            if other_attr_value is not None:
                setattr(self, curr_attr_name, other_attr_value)

    def add_allowed_values(self, additional_values):
        if additional_values is not None:
            self._allowed_values.extend(additional_values)
            # make sure list contains no duplicates
            self._allowed_values = list(set(self._allowed_values))

    def _set_with_overwrite_warning(field_to_fill, attr_name, new_value):
        curr_attr_value = getattr(field_to_fill, attr_name)
        if curr_attr_value is not None:
            if curr_attr_value != new_value:
                warnings.warn("The field with name '{0}' already has a value of {1} set for attribute '{2}';"
                              "this will be overwritten with {3}".format(field_to_fill.field_name, curr_attr_value,
                                                                         attr_name,
                                                                         new_value)
                              )
        setattr(field_to_fill, attr_name, new_value)
