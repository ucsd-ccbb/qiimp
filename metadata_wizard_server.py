import argparse
from collections import defaultdict
import configparser
import copy
import datetime
import json
import os
import sys
import traceback
import tempfile

from urllib.parse import quote

import tornado.ioloop  # Note: Pycharm thinks this import isn't used, but it is
import tornado.web  # Note: Pycharm thinks this import isn't used, but it is
import tornado.websocket

import metadata_package_schema_builder
import regex_handler
import schema_builder
import xlsx_builder
import xlsx_validation_builder

_allowed_min_browser_versions = {
    'chrome': 49,
    'firefox': 48,
}


def _parse_cmd_line_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--deployed", help="run with non-local settings from config", action="store_true")

    args = parser.parse_args()
    return args.deployed


def _parse_form_value(curr_value, retain_list=False):
    revised_values = [x.decode('ascii') for x in curr_value]  # everything comes through as a list of binary string
    if not retain_list:
        if len(revised_values) == 1:
            revised_values = revised_values[0]
        elif len(revised_values) == 0:
            revised_values = None

    return revised_values


def _get_package_schema_by_env_and_sample_type(wiz_state, arguments_obj):
    env_value = _parse_form_value(arguments_obj[schema_builder.InputNames.environment.value])
    sampletype_value = _parse_form_value(arguments_obj[schema_builder.InputNames.sample_type.value])
    result = metadata_package_schema_builder.load_schemas_for_package_key(
        env_value, sampletype_value, wiz_state.parent_stack_by_env_name, wiz_state.env_schemas)
    return result


class MetadataWizardState(object):
    @staticmethod
    def _get_config_values(is_deployed):
        local_dir = os.path.dirname(__file__)
        section_name = "DEPLOYED" if is_deployed else "LOCAL"

        config_parser = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
        config_parser.read_file(open(os.path.join(local_dir, 'config.txt')))

        static_path = os.path.expanduser(config_parser.get(section_name, "static_path"))
        listen_port = os.path.expanduser(config_parser.get(section_name, "listen_port"))
        websocket_url = os.path.expanduser(config_parser.get(section_name, "websocket_url"))

        return static_path, websocket_url, listen_port

    def __init__(self):
        # I think this should NOT be in the config; new versions SHOULD involve changing code.
        self.VERSION = "v0.3"

        # TODO: someday: these file path definitions should move into the config
        self.RESERVED_WORDS_YAML_PATH = "reserved_words.yaml"
        self.REGEX_YAML_PATH = 'regex_definitions.yaml'
        self.README_TEXT_PATH = "readme_template.txt"
        self.DEFAULT_LOCALES_YAML_PATH = "default_locales.yaml"
        self.ENVIRONMENTS_YAML_PATH = "environments.yaml"
        self.SAMPLETYPES_YAML_PATH = "sampletypes.yaml"
        self.local_dir = os.path.dirname(__file__)
        self.static_path = None
        self.packages_dir_path = None
        self.main_url = None
        self.full_upload_url = None
        self.full_merge_url = None
        self.websocket_url = None
        self.listen_port = None
        self.regex_handler = None
        self.parent_stack_by_env_name = None
        self.env_schemas = None
        self.default_locales_list = None
        self.reserved_words_list = None
        self.merge_info_by_merge_id = {}

    def set_up(self, is_deployed):
        self.packages_dir_path = os.path.join(self.local_dir, "packages")

        self.static_path, self.websocket_url, self.listen_port = self._get_config_values(is_deployed)
        if self.static_path == "": self.static_path = self.local_dir
        self.main_url = "{0}:{1}".format(self.websocket_url, self.listen_port)
        self.full_upload_url = "http://{0}/upload".format(self.main_url)
        self.full_merge_url = "http://{0}/merge".format(self.main_url)

        self.regex_handler = regex_handler.RegexHandler(os.path.join(self.local_dir, self.REGEX_YAML_PATH))
        self.reserved_words_list = metadata_package_schema_builder.load_yaml_from_fp(self.RESERVED_WORDS_YAML_PATH)
        self.default_locales_list = metadata_package_schema_builder.load_yaml_from_fp(self.DEFAULT_LOCALES_YAML_PATH)

    def make_readme_text(self):
        with open(self.README_TEXT_PATH, 'r') as f:
            readme_text = f.read()

        now = datetime.datetime.now()
        readme_text = readme_text.replace("VERSION", self.VERSION)
        readme_text = readme_text.replace("GENERATION_TIMESTAMP", now.strftime("%Y-%m-%d %H:%M:%S"))
        return readme_text


class PackageHandler(tornado.web.RequestHandler):
    def get(self, *args, **kwargs):
        raise NotImplementedError("Get not supported for PackageHandler.")

    def post(self, *args):
        wiz_state = self.application.settings["wizard_state"]
        package_schema = _get_package_schema_by_env_and_sample_type(wiz_state, self.request.arguments)

        field_descriptions = []
        for curr_field_name, curr_field_dict in package_schema.items():
            curr_desc = xlsx_validation_builder.get_field_constraint_description(curr_field_dict, wiz_state.regex_handler)
            field_descriptions.append({"name": curr_field_name,
                                       "description": curr_desc})

        self.write(json.dumps(
            {"field_names": sorted(package_schema.keys()),
             "reserved_words": wiz_state.reserved_words_list,
             "field_descriptions": field_descriptions}))
        self.finish()

    def data_received(self, chunk):
        # PyCharm tells me that this abstract method must be implemented to derive from RequestHandler ...
        pass


class UploadHandler(tornado.web.RequestHandler):
    def get(self, *args, **kwargs):
        raise NotImplementedError("Get not supported for UploadHandler.")

    def post(self, *args):
        # TODO: someday: refactor hard-coding of element name
        fileinfo_dict = self.request.files["files[]"][0]
        file_name = fileinfo_dict['filename']
        result_dict = {"files": [{"name": file_name}]}

        # The libraries for reading xlsx files don't accept a stream, only a file name, so I HAVE to write this to a
        # file at least temporarily ...
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
        temp_file.write(fileinfo_dict['body'])
        temp_file.close()  # but DON'T delete yet

        try:
            # TODO: someday: refactor hardcoding of spreadsheet name
            form_dict = metadata_package_schema_builder.load_yaml_from_wizard_xlsx(temp_file.name, "metadata_form")
            result_dict["fields"] = form_dict
        except ValueError as e:
            if str(e).startswith(metadata_package_schema_builder.NON_WIZARD_XLSX_ERROR_PREFIX):
                result_dict["files"][0]["error"] = str(e)
            else:
                raise e

        # send back name of file that was uploaded
        self.write(json.dumps(result_dict))
        self.finish()

    def data_received(self, chunk):
        # PyCharm tells me that this abstract method must be implemented to derive from RequestHandler ...
        pass


class MergeHandler(tornado.web.RequestHandler):
    def get(self, *args, **kwargs):
        wiz_state = self.application.settings["wizard_state"]
        self.render("metadata_merge_template.html", merge_url=wiz_state.full_merge_url)

    def post(self, *args):
        wiz_state = self.application.settings["wizard_state"]

        # TODO: someday: refactor hard-coding of element names
        files_element_name = "files[]"
        merge_id_element_name = "merge_id"
        filename_key = "filename"

        merge_id = _parse_form_value(self.request.arguments[merge_id_element_name])

        # if there is a files element in the submit
        if files_element_name in self.request.files:
            # get the files, save them under the merge_id
            file_names_dict_list = []
            fileinfo_dicts_list = self.request.files[files_element_name]
            for curr_fileinfo_dict in fileinfo_dicts_list:
                # store the uploaded file(s) for use when we know all have been submitted, at which point we will merge
                if not merge_id in wiz_state.merge_info_by_merge_id:
                    wiz_state.merge_info_by_merge_id[merge_id] = []
                wiz_state.merge_info_by_merge_id[merge_id].append(curr_fileinfo_dict)

                # build up a list of the file name(s) uploaded to send back to the front-end
                file_names_dict_list.append({"name": curr_fileinfo_dict[filename_key]})

            # send back name(s) of file(s) uploaded
            self.write(json.dumps({"files": file_names_dict_list}))
            self.finish()
        else:
            # all file uploads are done; do the actual merge and redirect to the download page;

            # start by getting all the files that were uploaded
            file_info_dicts_list = wiz_state.merge_info_by_merge_id[merge_id]

            # TODO: insert Austin's code to merge the files, once provided

            # delete the info/files stored in wiz_state.merge_info_by_merge_id under this merge id, since merge is done
            wiz_state.merge_info_by_merge_id.pop(merge_id)

            pretend_filename = "_".join([x[filename_key] for x in file_info_dicts_list])
            self.redirect("/download/{0}".format(pretend_filename))

    def data_received(self, chunk):
        # PyCharm tells me that this abstract method must be implemented to derive from RequestHandler ...
        pass


class MainHandler(tornado.web.RequestHandler):
    def get(self):
        wiz_state = self.application.settings["wizard_state"]
        global _allowed_min_browser_versions

        # get the package info
        combination_dicts_list, host_dicts_list, sampletype_dicts_list, wiz_state.parent_stack_by_env_name, \
        wiz_state.env_schemas = metadata_package_schema_builder.load_environment_and_sampletype_info(
            wiz_state.ENVIRONMENTS_YAML_PATH, wiz_state.SAMPLETYPES_YAML_PATH, wiz_state.packages_dir_path)

        sampletypes_by_env_json = json.dumps(sampletype_dicts_list)

        self.render("metadata_wizard_template.html", upload_url=wiz_state.full_upload_url,
                    allowed_min_browser_versions=_allowed_min_browser_versions, select_size=10,
                    combinations_list=combination_dicts_list, sampletypes_by_env_json=sampletypes_by_env_json,
                    hosts_list=host_dicts_list)

    def post(self):
        wiz_state = self.application.settings["wizard_state"]

        try:
            # first get the package schema info
            package_schema = _get_package_schema_by_env_and_sample_type(wiz_state, self.request.arguments)

            study_name = None
            study_default_locale = None
            dict_of_field_schemas_by_index = defaultdict(dict)
            for curr_key, curr_value in self.request.arguments.items():
                # per issue #53, all user-provided fields must be lower-cased
                curr_key = curr_key.lower()

                # ignore the "*_template" keys
                if not curr_key.endswith(schema_builder.TEMPLATE_SUFFIX):
                    if curr_key == schema_builder.InputNames.study_name.value:
                        study_name = _parse_form_value(curr_value)
                    # TODO: Get rid of hardcode of field name
                    elif curr_key == "default_study_location_select":
                        study_default_locale = _parse_form_value(curr_value)
                    else:
                        retain_list = False
                        # slice off the field index at the end
                        split_val = curr_key.split(schema_builder.SEPARATOR)
                        index_str = split_val[-1]
                        if "[]" in index_str:
                            retain_list = True
                        index_str = index_str.replace("[]", "")
                        try:
                            index = int(index_str)  # index will be last separated value in key name
                            curr_schema = dict_of_field_schemas_by_index[index]
                            base_key = curr_key.replace(schema_builder.SEPARATOR + index_str, "")

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
                # The only time when multiple fields come back is when the input is a continuous field, in which
                # case the units for that field are split out and put in *another* field that always has the same
                # value (ugh, but this is the customer requirement).
                field_name_and_schema_tuples_list = schema_builder.get_validation_schemas(curr_schema, wiz_state.regex_handler)
                for field_name, curr_validation_schema in field_name_and_schema_tuples_list:
                    dict_of_validation_schema_by_index[field_name] = curr_validation_schema

            mutable_package_schema = copy.deepcopy(package_schema)
            mutable_package_schema = self._update_package_with_locale_defaults(mutable_package_schema,
                                                                               study_default_locale)
            mutable_package_schema.update(dict_of_validation_schema_by_index)

            file_name = xlsx_builder.write_workbook(study_name, mutable_package_schema, wiz_state.regex_handler,
                                                    dict_of_field_schemas_by_index, wiz_state.make_readme_text())

            self.redirect("/download/{0}".format(file_name))
        except Exception as e:
            self.send_error(exc_info=sys.exc_info())

    def write_error(self, status_code, **kwargs):
        wiz_state = self.application.settings["wizard_state"]

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

        self.render("metadata_error_template.html", mailto_url=mailto_url, error_trace=error_details,
                    main_url=wiz_state.main_url)

    def data_received(self, chunk):
        # PyCharm tells me that this abstract method must be implemented to derive from RequestHandler ...
        pass

    def _update_package_with_locale_defaults(self, package_schema, study_default_locale):
        wiz_state = self.application.settings["wizard_state"]

        locale_fields_to_modify = None
        for curr_locale_dict in wiz_state.default_locales_list:
            curr_locale, curr_locale_subdict = metadata_package_schema_builder.get_single_key_and_subdict(curr_locale_dict)
            if study_default_locale == curr_locale:
                locale_fields_to_modify = curr_locale_subdict
                break

        if locale_fields_to_modify is None:
            raise ValueError("Default study locale '{0}' was not found among known default locales.".format(
                study_default_locale))

        package_schema = metadata_package_schema_builder.update_schema(package_schema, locale_fields_to_modify)
        return package_schema


class DownloadHandler(tornado.web.RequestHandler):
    def get(self, slug):
        wiz_state = self.application.settings["wizard_state"]
        self.render("metadata_download_template.html", template_file_name=slug, main_url=wiz_state.main_url)

    def data_received(self, chunk):
        # PyCharm tells me that this abstract method must be implemented to derive from RequestHandler ...
        pass


if __name__ == "__main__":
    wizard_state = MetadataWizardState()
    is_deployed = _parse_cmd_line_args()
    wizard_state.set_up(is_deployed)

    settings = {
        "static_path": wizard_state.static_path,
        "wizard_state": wizard_state
    }
    application = tornado.web.Application([
        (r"/", MainHandler),
        (r"/download/([^/]+)", DownloadHandler),
        (r"/(upload)$", UploadHandler),
        (r"/(package)$", PackageHandler),
        (r"/(merge)$", MergeHandler)
    ], **settings)

    application.listen(wizard_state.listen_port)
    tornado.ioloop.IOLoop.instance().start()

