import datetime
import json
import os
import string

import tornado.ioloop
import tornado.web
import xlsxwriter




def parse_json(json_string):
    temp = json.loads(json_string)
    return temp


def write_schema_worksheet(workbook, json_string):
    schema_worksheet = workbook.add_worksheet("metadata_schema")
    schema_worksheet.protect()
    schema_worksheet.write_string("A1", json_string)


def write_validation_sheet(workbook):
    schema_worksheet = workbook.add_worksheet("validation")
    schema_worksheet.protect()


def _generate_validation_formula(field_to_validate, starting_cell_name):

    """

    :type field_to_validate: generic_field
    """

    # work out "and" phrase
    if field_to_validate.data_type is int:
        type_phrase = "INT"
        type_name = "integer"
    elif field_to_validate.data_type is float:
        type_phrase = "VALUE"
        type_name = "decimal"
    else:
        raise ValueError("unrecognized num_type: {0}".format(field_to_validate.data_type))

    message_num_type = "a number of the type {0}".format(type_name)
    type_phrase = "{0}({1})={1}".format(type_phrase, starting_cell_name, starting_cell_name)

    min_phrase = None if min_val is None else "{0}<={1}".format(min_val, starting_cell_name)
    min_msg = None if min_val is None else "greater than or equal to {0}".format(min_val)

    max_phrase = None if max_val is None else "{0}<={1}".format(starting_cell_name, max_val)
    max_msg = None if max_val is None else "less than or equal to {0}".format(max_val)

    and_pieces = [x for x in [min_phrase, max_phrase, type_phrase] if x is not None]
    if len(and_pieces) > 0:
        and_clause = "AND({0})".format(", ".join(and_pieces))
        and_msg = " and ".join([message_num_type, min_msg, max_msg])
    else:
        and_clause = "TRUE"
        and_msg = None

    or_clause, or_msg = _generate_allowed_values_clause(field_to_validate, starting_cell_name)

    # construct formula
    validation_formula = "=IF(ISNUMBER({0}),{1},{2})".format(starting_cell_name, and_clause, or_clause)
    validation_msg = '{0} must be {1}, or {2}'.format(field_to_validate.field_name, and_msg, or_msg)


def _generate_allowed_values_clause(field_to_validate, starting_cell_name):
    # allowed values are handled by an OR clause in the validation formula
    if len(field_to_validate.allowed_values) > 0:
        str_comparisons = ['{0} = "{1}"'.format(starting_cell_name, x) for x in field_to_validate.allowed_values]
        or_clause = "OR({0})".format(", ".join(str_comparisons))
        or_msg = '{0} must be one of these allowed values: {1}'.format(
            field_to_validate.field_name, ", ".join(field_to_validate.allowed_values))
    else:
        or_clause = "FALSE"
        or_msg = None

    return or_clause, or_msg

def write_metadata_sheet(workbook, json_dict_list):
    worksheet = workbook.add_worksheet("metadata")
    worksheet.protect()
    locked_and_bold = workbook.add_format({'locked': 1, 'bold': True})
    unlocked_format = workbook.add_format({'locked': 0})
    worksheet.set_column('A:XFD', None, unlocked_format)

    # Write some simple text.
    worksheet.write('A1', 'sample_name', locked_and_bold)
    # construct formula
    validation_formula = "=NOT(OR(LEN(A2)<0, LEN(A2)>250, 1<COUNTIF(A:A, A2)))"
    worksheet.data_validation("A2:A1048576", {'validate': 'custom', 'value': validation_formula,
                                              'input_title': 'Enter a sample_name:',
                                              'input_message': 'sample_name must be a unique string between 1 and 250 characters long'})

    worksheet.freeze_panes(1, 0)

    curr_col_index = 1  # not a mistake: although we write to A1 above, excel is 1-based but ascii indexes are zero-based :)
    name_row_index = 1

    for curr_json_dict in json_dict_list:
        curr_field = GenericField()

        for key, val in curr_json_dict.items():
            if key == "field_name":
                field_name = val
                col_letter = (string.ascii_lowercase[curr_col_index]).upper()
                worksheet.write("{0}{1}".format(col_letter, name_row_index), field_name, locked_and_bold)
                curr_col_index += 1
            else:
                curr_field = process_potential_object_entry(key, val, curr_field)
            # end if
        # end this key

        data_row_index = name_row_index + 1
        starting_cell_name = "{0}{1}".format(col_letter, data_row_index)
        whole_col_range = "{0}2:{0}1048576".format(col_letter)

        if num_type is str and len(unique_allowed_list) > 0:
            worksheet.data_validation(whole_col_range, {'validate': 'list', 'source': unique_allowed_list,
                                      'input_title': 'Enter {0}:'.format(field_name),
                                      'input_message': '{0} must be one of these allowed values: {1}'.format(
                                          field_name, ", ".join(unique_allowed_list)
                                      )})
        else:
            validation_msg = _generate_validation_formula(curr_field, starting_cell_name)
            worksheet.data_validation(whole_col_range, {'validate': 'custom', 'value': validation_formula,
                                                        'input_title': 'Enter {0}:'.format(
                                                            curr_field.field_name),
                                                        'input_message': validation_msg})

        if default_val is not None:
            hidden_unlocked = workbook.add_format({'locked': 0, 'hidden': 1})
            for i in range(2,250):  # TODO: extend to whole column
                curr_cell = "{0}{1}".format(col_letter, i)
                formula_str = '=IF(A{0}="", "", "{1}")'.format(i, default_val)
                # A should always be sample_name
                worksheet.write_formula(curr_cell, formula_str, hidden_unlocked)
    # end this field

    workbook.define_name('ValidationRange', '=metadata!$A$2:${0}$1048576'.format(col_letter))


def write_workbook(json_string):
    workbook = xlsxwriter.Workbook('demo.xlsx', {'strings_to_numbers':  False,
                               'strings_to_formulas': True,
                               'strings_to_urls':     True})
    json_dict_list = parse_json(json_string)
    write_metadata_sheet(workbook, json_dict_list)
    write_schema_worksheet(workbook, json_string)
    workbook.close()


class MainHandler(tornado.web.RequestHandler):

    def get(self):
        self.render("test_json_editor_template.html")

    def post(self):
        noun1 = self.get_argument('schema_json')
        write_workbook(noun1)
        self.write(noun1)


if __name__ == "__main__":
    #json_string = '[ { "field_name": "ispatient", "type_specific_contents": { "true_value": "true", "false_value": "false" }, "has_default": { "default_value_inner": "Not Provided" }, "has_missings": {} } ]'
    # json_string = '[ { "field_name": "age", "type_specific_contents": { "measurement": { "minimum_integer": 18, "maximum_integer": 115 }, "unit": "years" }, "default_value": { "default_value_inner": "-1" }, "allowed_missing_vals": {} }, { "field_name": "is_patient", "type_specific_contents": { "true_value": "Yes", "false_value": "No" }, "default_value": {}, "allowed_missing_vals": { "allowed_missing_values_list": "Not Applicable, Not Provided, Restricted" } }, { "field_name": "patient_group", "type_specific_contents": { "allowed_values": "Healthy Control, Mild Disease, Severe Disease" }, "default_value": {}, "allowed_missing_vals": {} } ]'
    json_string = """[{
    "field_name": "age",
    "type_specific_contents": {
      "continuous": {
        "integer_minimum": 18,
        "integer_maximum": 115
      },
      "unit": "years"
    },
    "default_setting": {
      "default_value": "Not Provided"
    },
    "missing_vals_setting": {
      "allowed_missing_vals": "Not Provided, Restricted"
    }
  },
  {
    "field_name": "is_patient",
    "type_specific_contents": {
      "boolean_true": "Yes",
      "boolean_false": "No"
    },
    "default_setting": {
      "default_value": null
    },
    "missing_vals_setting": {
      "allowed_missing_vals": "Not Applicable, Not Provided, Restricted"
    }
  },
  {
    "field_name": "disease_group",
    "type_specific_contents": {
      "categorical_values": "Mild Disease, Severe Disease, Healthy Control"
    },
    "default_setting": {
      "default_value": null
    },
    "missing_vals_setting": {
      "allowed_missing_vals": null
    }
  },
  {
    "field_name": "dosage",
    "type_specific_contents": {
      "continuous": {
        "decimal_minimum": 0.1,
        "decimal_maximum": 1.2
      },
      "unit": "cc"
    },
    "default_setting": {
      "default_value": "0.5"
    },
    "missing_vals_setting": {
      "allowed_missing_vals": "Not Applicable, Not Provided, Restricted"
    }
  }
]"""

    write_workbook(json_string)

    # settings = {
    #     "static_path": os.path.dirname(__file__)
    # }
    # application = tornado.web.Application([
    #     (r"/", MainHandler),
    #     (r"/(apple-touch-icon\.png)", tornado.web.StaticFileHandler,
    #      dict(path=settings['static_path'])),
    # ], **settings)
    #
    # application.listen(8898)
    # tornado.ioloop.IOLoop.instance().start()
