from collections import defaultdict
import os

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


def parse_form_value(curr_value):
    revised_values = [x.decode('ascii') for x in curr_value]  # everything comes through as a list of binary string
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
                    # slice off the field index at the end
                    split_val = curr_key.split(separator)
                    index_str = split_val[-1]
                    index_str = index_str.replace("[]", "")
                    try:
                        index = int(index_str)  # index will be last separated value in key name
                        curr_schema = dict_of_field_schemas_by_index[index]
                        base_key = curr_key.replace(separator + index_str, "")

                        revised_values = parse_form_value(curr_value)
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

