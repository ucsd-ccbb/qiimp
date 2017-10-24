import argparse
from collections import defaultdict
import configparser
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
import regex_handler

# TODO: Refactor to dynamically pull from files
# TODO: Refactor to share definition of "other" key between back and front ends
_packages_by_keys = {
    "other": metadata_package_schema_builder.PerSamplePackage
}

_package_class = None
_full_websocket_url = None
_regex_handler = None

_allowed_min_browser_versions = {
    'chrome': 49,
    'firefox': 48,
}


def _parse_cmd_line_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--deployed", help="run with non-local settings from config", action="store_true")

    args = parser.parse_args()
    return args.deployed


def _get_config_values(is_deployed):
    local_dir = os.path.dirname(__file__)
    section_name = "DEPLOYED" if is_deployed else "LOCAL"

    config_parser = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
    config_parser.read_file(open(os.path.join(local_dir, 'config.txt')))

    static_path = os.path.expanduser(config_parser.get(section_name, "static_path"))
    listen_port = os.path.expanduser(config_parser.get(section_name, "listen_port"))
    websocket_url = os.path.expanduser(config_parser.get(section_name, "websocket_url"))

    return static_path, websocket_url, listen_port


def _set_package_class(new_class):
    global _package_class
    _package_class = new_class


def _get_package_class():
    global _package_class
    return _package_class


def _parse_form_value(curr_value, retain_list=False):
    revised_values = [x.decode('ascii') for x in curr_value]  # everything comes through as a list of binary string
    if not retain_list:
        if len(revised_values) == 1:
            revised_values = revised_values[0]
        elif len(revised_values) == 0:
            revised_values = None

    return revised_values


class PackageHandler(tornado.websocket.WebSocketHandler):
    def data_received(self, chunk):
        pass

    def open(self):
        pass

    def on_message(self, message):
        global _packages_by_keys

        # default package, if all else fails, is "other"
        package_key = "other"

        if message in _packages_by_keys:
            # if there is an exact match to the package the user is trying to find in the package_keys, use that!
            package_key = message
        else:
            # if there is no exact match to the package the user is looking for, split it on its separator; assume it
            # will have at least one piece.
            message_split = message.split("_")
            message_start = message_split[0]
            if message_start in _packages_by_keys:
                # if the first piece of the package name is in the package_keys, use that
                package_key = message_start
            else:
                # NB: Right now assuming the package can only have two parts--host organism and sample type.
                # This is generated in packageWizard.js getPackage() .
                if len(message_split) == 2:
                    message_end = message_split[1]
                    if message_end in _packages_by_keys:
                        # if the package name has two pieces, and the second piece is in the package_keys even though
                        # the first piece isn't, use the second piece
                        package_key = message_end
                    # end if
                # end if
            # end if
        # end if

        selected_package = _packages_by_keys[package_key]
        package_class = selected_package()

        # TODO: get all the required keys, return them as here, but ALSO
        # get all the not-required keys and their messages, return them separately; then change interface
        # to display them as checkboxes.  If they are checked, include them in schema AS REQUIRED
        return_delimited_str = ", ".join(sorted(package_class.schema.keys()))
        _set_package_class(package_key)
        self.write_message(return_delimited_str)

    def on_close(self):
        pass


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        global _full_websocket_url
        self.render("metadata_wizard_template.html", websocket_url=_full_websocket_url,
                    allowed_min_browser_versions=_allowed_min_browser_versions)

    def post(self):
        global _regex_handler
        try:
            study_name = None
            dict_of_field_schemas_by_index = defaultdict(dict)
            for curr_key, curr_value in self.request.arguments.items():
                # per issue #53, all user-provided fields must be lower-cased
                curr_key = curr_key.lower()

                # ignore the "*_template" keys
                if not curr_key.endswith(schema_builder.TEMPLATE_SUFFIX):
                    if curr_key == schema_builder.InputNames.study_name.value:
                        study_name = _parse_form_value(curr_value)
                    elif curr_key == "study_location_select":
                        # TODO: Add handling for study_location_select
                        pass
                    else:
                        retain_list = False
                        # slice off the field index at the end.
                        # NB: it is OK if the field indices do not start at zero and/or are not contiguous
                        split_val = curr_key.split(schema_builder.SEPARATOR)
                        index_str = split_val[-1]

                        try:
                            index = int(index_str)  # index will be last separated value in key name
                            curr_schema = dict_of_field_schemas_by_index[index]
                            base_key = curr_key.replace(schema_builder.SEPARATOR + index_str, "")
                            if "[]" in base_key:
                                retain_list = True
                            base_key = base_key.replace("[]", "")

                            revised_values = _parse_form_value(curr_value, retain_list)
                            if revised_values:  # "truish"--not empty string, whitespace, etc
                                curr_schema[base_key] = revised_values
                        except ValueError:
                            pass  # ignore fields that don't end with a field index number
                        # end if this key really has a value
                    # end if this key isn't for study_name
                # end if this is a real key and not a template key
            # next form field

            dict_of_validation_schema_by_index = {}
            for curr_key in dict_of_field_schemas_by_index:
                curr_schema = dict_of_field_schemas_by_index[curr_key]
                field_name, curr_validation_schema = schema_builder.get_validation_schema(curr_schema, _regex_handler)
                dict_of_validation_schema_by_index[field_name] = curr_validation_schema

            package_key = _get_package_class()
            selected_package = _packages_by_keys[package_key]
            package_class = selected_package()

            # TODO: so, right now I just grab the whole schema.  Need to handle this differently: get everything
            # required from this schema.  Then, get back selected optionals from interface (currently not done)
            # and get those from schema--and change them to required.
            dict_of_validation_schema_by_index.update(package_class.schema)
            file_name = xlsx_builder.write_workbook(study_name, dict_of_validation_schema_by_index, _regex_handler)

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
    is_deployed = _parse_cmd_line_args()
    local_dir = os.path.dirname(__file__)

    static_path, websocket_url, listen_port = _get_config_values(is_deployed)
    if static_path == "": static_path = local_dir
    _full_websocket_url = "ws://{0}:{1}/websocket".format(websocket_url, listen_port)

    _regex_handler = regex_handler.RegexHandler(os.path.join(local_dir, 'regex_definitions.yaml'))

    settings = {
        "static_path": static_path
    }
    application = tornado.web.Application([
        (r"/", MainHandler),
        (r"/websocket", PackageHandler)
    ], **settings)

    application.listen(listen_port)
    tornado.ioloop.IOLoop.instance().start()

