import os
import string

import tornado.ioloop
import tornado.web
import xlsxwriter
import yaml

import constraint_builder


def write_workbook(yaml_string):
    workbook = xlsxwriter.Workbook('demo.xlsx', {'strings_to_numbers':  False,
                               'strings_to_formulas': True,
                               'strings_to_urls':     True})
    schema_dict = yaml.load(yaml_string)
    write_metadata_sheet(workbook, schema_dict)
    write_schema_worksheet(workbook, yaml_string)
    workbook.close()


def write_schema_worksheet(workbook, yaml_string):
    schema_worksheet = workbook.add_worksheet("metadata_schema")
    schema_worksheet.protect()
    schema_worksheet.write_string("A1", yaml_string)


# TODO: Create validation worksheet that tells them which entries in metadata sheet are wrong
def write_validation_sheet(workbook):
    schema_worksheet = workbook.add_worksheet("validation")
    schema_worksheet.protect()


def write_metadata_sheet(workbook, schema_dict):
    locked_and_bold = workbook.add_format({'locked': 1, 'bold': True})
    unlocked_format = workbook.add_format({'locked': 0})

    worksheet = workbook.add_worksheet("metadata")
    worksheet.protect()
    worksheet.set_column('A:XFD', None, unlocked_format)
    worksheet.freeze_panes(1, 0)

    curr_col_index = 0
    name_row_index = 1
    data_row_index = name_row_index + 1

    # TODO: decide what to do re order
    sorted_keys = sorted(schema_dict.keys())
    for field_name in sorted_keys:
        field_specs_dict = schema_dict[field_name]
        col_letter = _get_col_letters(curr_col_index)
        worksheet.write("{0}{1}".format(col_letter, name_row_index), field_name, locked_and_bold)

        starting_cell_name = "{0}{1}".format(col_letter, data_row_index)
        whole_col_range = "{0}2:{0}1048576".format(col_letter)

        validation_dict = constraint_builder.get_validation_dict(field_name, field_specs_dict)
        value_key = "value"
        if validation_dict is not None:
            if value_key in validation_dict:
                temp = validation_dict[value_key]
                temp2 = temp.format(cell=starting_cell_name)
                validation_dict[value_key] = temp2

            worksheet.data_validation(whole_col_range, validation_dict)

        _add_default_if_any(workbook, worksheet, col_letter, field_specs_dict)
        curr_col_index += 1


def get_letter(zero_based_letter_index):
    return (string.ascii_lowercase[zero_based_letter_index]).upper()


def _get_col_letters(curr_col_index):
    len_alphabet = len(string.ascii_lowercase)
    num_complete_alphabets = curr_col_index // len_alphabet
    if num_complete_alphabets >= len_alphabet:
        max_num_columns = len_alphabet * len_alphabet
        raise ValueError("Having greater than or equal to {0} columns is not supported".format(max_num_columns))

    prefix_letter = "" if num_complete_alphabets == 0 else get_letter(num_complete_alphabets-1)
    index_within_curr_alphabet = curr_col_index % len_alphabet
    current_letter = get_letter(index_within_curr_alphabet)
    result = "{0}{1}".format(prefix_letter, current_letter)
    return result


def _add_default_if_any(workbook, worksheet, col_letter, field_specs_dict):
    default_formula = constraint_builder.get_default_formula(field_specs_dict)
    if default_formula is not None:
        hidden_unlocked = workbook.add_format({'locked': 0, 'hidden': 1})
        for i in range(2,250):  # TODO: extend to whole column
            curr_cell = "{0}{1}".format(col_letter, i)
            completed_default_formula = default_formula.format(curr_row_num=i)
            # A should always be sample_name
            worksheet.write_formula(curr_cell, completed_default_formula, hidden_unlocked)


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("metadata_wizard_template.html")

    def post(self):
        # noun1 = self.get_argument('metadata_form')
        details = ""
        for f in self.request.arguments.values():
            details += "<hr/>" + ", ".join(f)
        self.write(details)

        #write_workbook(noun1)
        # TODO: figure out how to write back download link for newly-generated spreadsheet
        #self.write(noun1)


if __name__ == "__main__":
    # hs_vaginal_fixed_schema_yaml = package_schemas.ridiculously_large_temporary_function()
    # write_workbook(hs_vaginal_fixed_schema_yaml)

    settings = {
        "static_path": os.path.dirname(__file__)
    }
    application = tornado.web.Application([
        (r"/", MainHandler),
        (r"/(apple-touch-icon\.png)", tornado.web.StaticFileHandler,
         dict(path=settings['static_path'])),
    ], **settings)

    application.listen(8898)
    tornado.ioloop.IOLoop.instance().start()