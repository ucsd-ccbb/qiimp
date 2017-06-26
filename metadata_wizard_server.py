from collections import defaultdict
import os
import sys
import traceback

from urllib.parse import quote

import tornado.ioloop  # Note: Pycharm thinks this import isn't used, but it is
import tornado.web  # Note: Pycharm thinks this import isn't used, but it is
import tornado.websocket


import metadata_package_schema_builder
import schema_builder
import xlsx_builder

_packages_by_keys = {
    "human_vaginal": metadata_package_schema_builder.HumanVaginaPackage,
    "human": metadata_package_schema_builder.HumanPackage,
    "other": metadata_package_schema_builder.PerSamplePackage
}

_package_class = None


def set_package_class(new_class):
    global _package_class
    _package_class = new_class


def get_package_class():
    global _package_class
    return _package_class


def parse_form_value(curr_value, retain_list = False):
    revised_values = [x.decode('ascii') for x in curr_value]  # everything comes through as a list of binary string
    if not retain_list:
        if len(revised_values) == 1:
            revised_values = revised_values[0]
        elif len(revised_values) == 0:
            revised_values = None

    return revised_values


class Hello(tornado.websocket.WebSocketHandler):
    def data_received(self, chunk):
        pass

    def open(self):
        pass

    def on_message(self, message):
        global _packages_by_keys
        package_key = "other"
        if message in _packages_by_keys:
            package_key = message
        else:
            message_split = message.split("_")
            message_start = message_split[0]
            if message_start in _packages_by_keys:
                package_key = message_start
            else:
                if len(message_split)==2:
                    message_end = message_split[1]
                    if message_end in _packages_by_keys:
                        package_key = message_end
                    # end if
                # end if
            # end if
        # end if

        selected_package = _packages_by_keys[package_key]
        package_class = selected_package()
        return_delimited_str = ", ".join(sorted(package_class.schema.keys()))
        set_package_class(package_key)
        self.write_message(return_delimited_str)

    def on_close(self):
        pass


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("metadata_wizard_template.html")

    def post(self):
        try:
            separator = "_"
            study_name = None
            dict_of_field_schemas_by_index = defaultdict(dict)
            for curr_key, curr_value in self.request.arguments.items():
                if not curr_key.endswith("template"):
                    if curr_key == "study_name":
                        study_name = parse_form_value(curr_value)
                    elif curr_key == "study_location_select":
                        pass
                    else:
                        retain_list = False
                        # slice off the field index at the end
                        split_val = curr_key.split(separator)
                        index_str = split_val[-1]
                        if "[]" in index_str:
                            retain_list = True
                        index_str = index_str.replace("[]", "")
                        try:
                            index = int(index_str)  # index will be last separated value in key name
                            curr_schema = dict_of_field_schemas_by_index[index]
                            base_key = curr_key.replace(separator + index_str, "")

                            revised_values = parse_form_value(curr_value, retain_list)
                            if revised_values:  # "truish"--not empty string, whitespace, etc
                                curr_schema[base_key] = revised_values
                        except ValueError:
                            pass  # ignore fields not used here
                        # end if this key really has a value
                    # end if this key isn't for study_name
                # end if this is a real key and not a template key
            # next form field

            dict_of_validation_schema_by_index = {}
            for curr_key in dict_of_field_schemas_by_index:
                curr_schema = dict_of_field_schemas_by_index[curr_key]
                field_name, curr_validation_schema = schema_builder.get_validation_schema(curr_schema)
                dict_of_validation_schema_by_index[field_name] = curr_validation_schema

            package_key = get_package_class()
            selected_package = _packages_by_keys[package_key]
            package_class = selected_package()
            dict_of_validation_schema_by_index.update(package_class.schema)
            file_name = xlsx_builder.write_workbook(study_name, dict_of_validation_schema_by_index)

            self.render("metadata_download_template.html", template_file_name=file_name)
        except Exception as e:
            self.send_error(exc_info=sys.exc_info())

    def write_error(self, status_code, **kwargs):
        error_details_list = []
        exc_info_key = "exc_info"
        if exc_info_key in kwargs:
            exc_info = kwargs.get(exc_info_key)
            exc_type, exc_value, exc_traceback = exc_info
            error_details_list = traceback.format_exception(exc_type, exc_value, exc_traceback)

        if len(error_details_list) == 0:
            error_details_list.append("Error details not found.")
        error_details = "".join(error_details_list)

        email_addr = "abirmingham@ucsd.edu"
        subject = "Metadata Wizard error report"
        mailto_url = "mailto:{0}?subject={1}&body={2}".format(email_addr, quote(subject), quote(error_details))

        self.render("metadata_error_template.html", mailto_url=mailto_url, error_trace=error_details)

    def data_received(self, chunk):
        # PyCharm tells me that this abstract method must be implemented to derive from RequestHandler ...
        pass


if __name__ == "__main__":
    settings = {
        "static_path": os.path.dirname(__file__)
    }
    application = tornado.web.Application([
        (r"/", MainHandler),
        (r"/(apple-touch-icon\.png)", tornado.web.StaticFileHandler, dict(path=settings['static_path'])) ,
        (r"/websocket", Hello)
    ], **settings)

    application.listen(8898)
    tornado.ioloop.IOLoop.instance().start()

