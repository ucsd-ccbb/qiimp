import metadata_package_schema_builder
import xlsx_basics
import xlsx_validation_builder


class ValidationWorksheet(xlsx_basics.MetadataWorksheet):
    def __init__(self, workbook, num_attributes, num_samples, a_regex_handler):
        super().__init__(workbook, num_attributes, num_samples, a_regex_handler, make_sheet=False)

        self.SAMPLE_NAME_HEADER = metadata_package_schema_builder.SAMPLE_NAME_HEADER
        self.IS_ABSENT_HEADER = "is_absent"
        self.IS_VALID_ROW_HEADER = "is_valid_row"
        self.ROW_IN_METADATA_HEADER = "row_in_metadata"
        self.ROW_ORDER_WEIGHT_HEADER = "row_order_weight"
        self.ROW_RANK_HEADER = "row_rank"
        self.IS_VALID_COL_HEADER = "is_valid_col"
        self.COL_IN_METADATA_HEADER = "col_in_metadata"
        self.COL_ORDER_WEIGHT_HEADER = "col_order_weight"
        self.COL_RANK_HEADER = "col_rank"

        self._col_offset = self._num_field_columns + 10
        self.first_static_grid_col_index = self.first_data_col_index + self._col_offset
        self.last_static_grid_col_index = self.last_data_col_index + self._col_offset

        self.first_helper_rows_row_index = self.last_data_row_index + 2
        self.helper_rows_header_col_index = self.first_static_grid_col_index - 1

        self.name_link_col_index = 0  # column indices are zero-based

        # the validation column for the sample name in the static grid should be in the same relative place it is in the
        # metadata grid; right now, this is equivalent to self.first_static_grid_col_index, but I give it its own
        # instance variable in case that changes in the future.
        self.name_static_col_index = self.name_col_index + self._col_offset

        self.worksheet = self._create_worksheet("validation")

    def hide_columns(self, first_col_index, last_col_index=None):
        first_col_letter = xlsx_basics.get_col_letters(first_col_index)
        last_col_letter = first_col_letter if last_col_index is None else xlsx_basics.get_col_letters(last_col_index)
        self.worksheet.set_column('{0}:{1}'.format(first_col_letter, last_col_letter), None, None, {'hidden': True})


# I know what you're thinking: if all these functions take in the ValidationWorksheet object as their first argument,
# why the heck aren't they methods of the Validation Worksheet object?  Well, they don't *all* take that in as their
# first argument, but that aside, it is because I ALSO want to pass the data contained in the ValidationWorksheet
# object to a completely *different*, non-overlapping set of functionality later on.  I don't want to stuff both those
# unrelated sets of functionality in the same object, and since top-level functions are just fine in Python,  I don't
# have to ... those functions are in a different module to keep them separate.
def write_static_validation_grid_and_helpers(val_sheet, schema_dict):
    _write_static_validation_grid(val_sheet, schema_dict)
    return _write_static_helper_rows_and_cols(val_sheet)


# write invariant sample by feature grid
def _write_static_validation_grid(val_sheet, schema_dict):
    """

    :type val_sheet: ValidationWorksheet
    """
    curr_grid_col_index = None
    sorted_keys = xlsx_basics.sort_keys(schema_dict)
    for field_index, field_name in enumerate(sorted_keys):
        field_specs_dict = schema_dict[field_name]
        curr_grid_col_index = val_sheet.first_static_grid_col_index + field_index

        xlsx_basics.write_header(val_sheet, field_name, curr_grid_col_index)

        unformatted_formula_str = xlsx_validation_builder.get_formula_constraint(field_specs_dict,
                                                                                 val_sheet.regex_handler)
        if unformatted_formula_str is not None:
            curr_metadata_col_index = val_sheet.first_data_col_index + field_index
            # metadata_cell_range_str = xlsx_basics.format_single_col_range(val_sheet, curr_metadata_col_index,
            #                                                    sheet_name=val_sheet.metadata_sheet_name)

            cell_enumerator = xlsx_basics.loop_through_range(curr_grid_col_index, val_sheet.first_data_row_index,
                                                             last_row_index=
                                                             val_sheet.last_allowable_row_for_sample_index)
            for _, curr_row_index, curr_cell_range in cell_enumerator:
                metadata_cell = xlsx_basics.format_range(curr_metadata_col_index, curr_row_index,
                                                         sheet_name=val_sheet.metadata_sheet_name)
                formatted_formula_str = unformatted_formula_str.format(cell=metadata_cell)
                val_sheet.worksheet.write_formula(curr_cell_range, formatted_formula_str)

                # xlsx_basics.format_and_write_array_formula(val_sheet, curr_grid_col_index, unformatted_formula_str,
                #                                            write_col=True, cell_range_str=metadata_cell_range_str)

    # hide all the columns in the static grid.  Use value of curr_grid_col_index left over from last time thru loop.
    if curr_grid_col_index: val_sheet.hide_columns(val_sheet.first_static_grid_col_index, curr_grid_col_index)


def _write_static_helper_rows_and_cols(val_sheet):
    """

    :type val_sheet: ValidationWorksheet
    """
    col_header_and_writer_func_tuple_list = [(val_sheet.SAMPLE_NAME_HEADER, _write_static_name_col),
                                             (val_sheet.IS_ABSENT_HEADER, _write_is_absent_col),
                                             (val_sheet.IS_VALID_ROW_HEADER, _write_is_valid_row_col),
                                             (val_sheet.ROW_IN_METADATA_HEADER, _write_row_in_metadata_col),
                                             (val_sheet.ROW_ORDER_WEIGHT_HEADER, _write_row_order_weight_col),
                                             (val_sheet.ROW_RANK_HEADER, _write_row_rank_col)]
    index_and_range_str_tuple_by_header_dict = _write_static_helper_ranges(val_sheet,
                                                                           col_header_and_writer_func_tuple_list)

    row_header_and_writer_func_tuple_list = [(val_sheet.IS_VALID_COL_HEADER, _write_is_valid_col_row),
                                             (val_sheet.COL_IN_METADATA_HEADER, _write_col_in_metadata_row),
                                             (val_sheet.COL_ORDER_WEIGHT_HEADER, _write_col_order_weight_row),
                                             (val_sheet.COL_RANK_HEADER, _write_col_rank_row)]

    index_and_range_str_tuple_by_header_dict = _write_static_helper_ranges(val_sheet,
                                                                           row_header_and_writer_func_tuple_list,
                                                                           index_and_range_str_tuple_by_header_dict)

    return index_and_range_str_tuple_by_header_dict


def _write_static_helper_ranges(val_sheet, header_and_writer_func_tuple_list,
                                range_index_and_range_str_tuple_by_header_dict=None):
    """

    :type val_sheet: ValidationWorksheet
    """

    def get_col_index(header_index):
        # NB: -2 because leaving an empty column between static validation grid and helper columns
        return val_sheet.first_static_grid_col_index - header_index - 2

    def get_row_index(header_index):
        return val_sheet.first_helper_rows_row_index + header_index

    col_index = None
    write_col = False
    if range_index_and_range_str_tuple_by_header_dict is None:
        range_index_and_range_str_tuple_by_header_dict = {}
        write_col = True

    for curr_header_index, curr_tuple in enumerate(header_and_writer_func_tuple_list):
        curr_header = curr_tuple[0]
        curr_write_method = curr_tuple[1]

        col_index = get_col_index(curr_header_index) if write_col else val_sheet.helper_rows_header_col_index
        row_index = None if write_col else get_row_index(curr_header_index)
        xlsx_basics.write_header(val_sheet, curr_header, col_index, row_index)

        curr_range_index = col_index if write_col else row_index
        curr_range_str = curr_write_method(val_sheet, curr_range_index,
                                           range_index_and_range_str_tuple_by_header_dict)
        range_index_and_range_str_tuple_by_header_dict[curr_header] = (curr_range_index, curr_range_str)

    if write_col and col_index is not None:
        # use the col_index left over from last time through loop
        val_sheet.hide_columns(val_sheet.first_static_grid_col_index-1, col_index)

    return range_index_and_range_str_tuple_by_header_dict


# NB: Do not remove unused parameter: this function is used in a context with a fixed expected interface that includes
# all three of these arguments.
def _write_static_name_col(val_sheet, col_index, index_and_range_tuple_by_header_dict):
    """

    :type val_sheet: ValidationWorksheet
    """
    # write sample_name column: e.g., =IF(metadata!B2:B11="","",metadata!B2:B11)
    # TODO: +1 is a hack to get it to show name rather than sample id ... think of less fragile way
    metadata_name_data_range = xlsx_basics.format_single_col_range(val_sheet, val_sheet.sample_id_col_index + 1,
                                                                   sheet_name=val_sheet.metadata_sheet_name)
    return xlsx_basics.format_and_write_array_formula(val_sheet, col_index, "IF({cell}=\"\",\"\",{cell})",
                                                      write_col=True, cell_range_str=metadata_name_data_range)


def _write_is_absent_col(val_sheet, col_index, index_and_range_tuple_by_header_dict):
    """

    :type val_sheet: ValidationWorksheet
    """
    # write is_absent column: e.g., =COUNTBLANK(metadata!B2:AH2)=COLUMNS(metadata!B2:AH2)
    metadata_single_row_range = xlsx_basics.format_single_data_grid_row_range(val_sheet, "{{curr_row_index}}",
                                                                              sheet_name=val_sheet.metadata_sheet_name)
    # When {{ and/or }} are put IN to string by a format call, as in first format call here, they aren't collapsed to
    # { and }, so second (empty) format call does that.
    is_absent_partial_formula = "=COUNTBLANK({metadata_single_row_range})=COLUMNS({metadata_single_row_range})".format(
        metadata_single_row_range=metadata_single_row_range).format()

    # Note: when I use the is_absent range later, I need it to be fixed, so making it so now
    return xlsx_basics.copy_formula_throughout_range(val_sheet.worksheet, is_absent_partial_formula,
                                                     first_col_index=col_index,
                                                     first_row_index=val_sheet.first_data_row_index,
                                                     last_row_index=val_sheet.last_data_row_index,
                                                     first_col_fixed=True, last_col_fixed=True)


def _write_is_valid_row_col(val_sheet, col_index, index_and_range_tuple_by_header_dict):
    """

    :type val_sheet: ValidationWorksheet
    """
    # write is_valid_row column: e.g., =IF(AO2,TRUE,AND(AQ2:BW2))
    is_absent_col_index = index_and_range_tuple_by_header_dict[val_sheet.IS_ABSENT_HEADER][0]
    is_absent_single_cell_range_str = xlsx_basics.format_range(is_absent_col_index, "{{curr_row_index}}")
    static_grid_single_row_range_str = xlsx_basics.format_range(val_sheet.first_static_grid_col_index,
                                                                "{{curr_row_index}}",
                                                                val_sheet.last_static_grid_col_index)
    # When {{ and/or }} are put IN to string by a format call, as in first format call here, they aren't collapsed to
    # { and }, so second (empty) format call does that.
    is_valid_row_partial_formula = "IF({is_absent_1cell_range_str},TRUE,AND({static_grid_1row_range_str}))".format(
        is_absent_1cell_range_str=is_absent_single_cell_range_str,
        static_grid_1row_range_str=static_grid_single_row_range_str).format()

    return xlsx_basics.copy_formula_throughout_range(val_sheet.worksheet, is_valid_row_partial_formula, col_index,
                                                     val_sheet.first_data_row_index,
                                                     last_row_index=val_sheet.last_data_row_index)


# NB: Do not remove unused parameter: this function is used in a context with a fixed expected interface that includes
# all three of these arguments.
def _write_row_in_metadata_col(val_sheet, col_index, index_and_range_tuple_by_header_dict):
    """

    :type val_sheet: ValidationWorksheet
    """
    # write row_in_metadata column: e.g., =ROW(metadata!A2:A11)
    metadata_sample_id_range_str = xlsx_basics.format_single_col_range(val_sheet, val_sheet.first_data_col_index,
                                                                       sheet_name=val_sheet.metadata_sheet_name)
    return xlsx_basics.format_and_write_array_formula(val_sheet, col_index, "ROW({cell})", write_col=True,
                                                      cell_range_str=metadata_sample_id_range_str)


def _write_row_order_weight_col(val_sheet, col_index, index_and_range_tuple_by_header_dict):
    """

    :type val_sheet: ValidationWorksheet
    """
    # write row_order_weight column: e.g., =INT(AM2:AM11)*100000+AL2:AL11
    row_order_weight_formula_str = _format_order_weight_formula(
        index_and_range_tuple_by_header_dict, val_sheet.IS_VALID_ROW_HEADER,
        val_sheet.ROW_IN_METADATA_HEADER)
    return xlsx_basics.format_and_write_array_formula(val_sheet, col_index, row_order_weight_formula_str,
                                                      write_col=True)


def _write_row_rank_col(val_sheet, col_index, index_and_range_tuple_by_header_dict):
    """

    :type val_sheet: ValidationWorksheet
    """
    # write row_rank column: e.g., =COUNTIF(AK$2:AK$11,"<="&$AK2:AK11)
    row_rank_formula_str = _format_rank_formula(val_sheet, index_and_range_tuple_by_header_dict,
                                                val_sheet.ROW_ORDER_WEIGHT_HEADER, write_col=True)
    return xlsx_basics.format_and_write_array_formula(val_sheet, col_index, row_rank_formula_str, write_col=True)


def _write_is_valid_col_row(val_sheet, row_index, index_and_range_tuple_by_header_dict):
    """

    :type val_sheet: ValidationWorksheet
    """
    # NB: For this one, each *cell* needs to be an array formula based on the cell's column, but the entire ROW
    # can't be an array formula--needs to be copied across :(
    # write is_valid_column row: for single cell, {=AND(IF($AO$2:$AO$11,TRUE,AQ2:AQ11))}
    is_absent_col_range = index_and_range_tuple_by_header_dict[val_sheet.IS_ABSENT_HEADER][1]
    # NB: No extra format call needed here because the {{ and }} are in the string when the (first and only) format
    # call is made, rather than being added by it, so that format call collapses them to { and }
    partial_formula_str = "AND(IF({is_absent_col_range},TRUE,{{curr_col_letter}}{first_row_index}:{{curr_col_letter}}" \
                          "{last_row_index}))".format(is_absent_col_range=is_absent_col_range,
                                                      first_row_index=val_sheet.first_data_row_index,
                                                      last_row_index=val_sheet.last_data_row_index)

    return xlsx_basics.copy_formula_throughout_range(val_sheet.worksheet, partial_formula_str,
                                                     first_col_index=val_sheet.first_static_grid_col_index,
                                                     first_row_index=row_index,
                                                     last_col_index=val_sheet.last_static_grid_col_index,
                                                     last_row_index=row_index,
                                                     is_array_formula=True)


# NB: Do not remove unused parameter: this function is used in a context with a fixed expected interface that includes
# all three of these arguments.
def _write_col_in_metadata_row(val_sheet, row_index, index_and_range_tuple_by_header_dict):
    """

    :type val_sheet: ValidationWorksheet
    """
    # write col_in_metadata row: =COLUMN(metadata!B2:AH2)
    metadata_single_row_range = xlsx_basics.format_single_data_grid_row_range(val_sheet, row_index,
                                                                              sheet_name=val_sheet.metadata_sheet_name)
    return xlsx_basics.format_and_write_array_formula(val_sheet, row_index, "COLUMN({cell})", write_col=False,
                                                      cell_range_str=metadata_single_row_range)


def _write_col_order_weight_row(val_sheet, row_index, index_and_range_tuple_by_header_dict):
    """

    :type val_sheet: ValidationWorksheet
    """
    # write col_order_weight row: =INT(AQ13:BW13)*100000+AQ14:BW14
    col_order_weight_formula_str = _format_order_weight_formula(index_and_range_tuple_by_header_dict,
                                                                val_sheet.IS_VALID_COL_HEADER,
                                                                val_sheet.COL_IN_METADATA_HEADER)
    return xlsx_basics.format_and_write_array_formula(val_sheet, row_index, col_order_weight_formula_str,
                                                      write_col=False)


def _write_col_rank_row(val_sheet, row_index, index_and_range_tuple_by_header_dict):
    """

    :type val_sheet: ValidationWorksheet
    """
    # write col_rank row: =COUNTIF($AQ15:$BW15,"<="&AQ$15:BW15)
    col_rank_formula_str = _format_rank_formula(val_sheet, index_and_range_tuple_by_header_dict,
                                                val_sheet.COL_ORDER_WEIGHT_HEADER, write_col=False)
    return xlsx_basics.format_and_write_array_formula(val_sheet, row_index, col_rank_formula_str, write_col=False)


def _format_order_weight_formula(index_and_range_tuple_by_name_dict, is_valid_header, position_in_metadata_header):
    # format row_order_weight column: e.g., =INT(AM2:AM11)*100000+AL2:AL11
    # or
    # format col_order_weight row: =INT(AQ13:BW13)*100000+AQ14:BW14
    is_valid_range_str = index_and_range_tuple_by_name_dict[is_valid_header][1]
    position_in_metadata_range_str = index_and_range_tuple_by_name_dict[position_in_metadata_header][1]
    return "INT({0})*100000+{1}".format(is_valid_range_str, position_in_metadata_range_str)


def _format_rank_formula(val_sheet, index_and_range_tuple_by_name_dict, order_weight_header, write_col):
    """

    :type val_sheet: ValidationWorksheet
    """
    # write row_rank column: e.g., =COUNTIF(AK$2:AK$11,"<="&$AK2:AK11)
    # or
    # write col_rank row: =COUNTIF($AQ15:$BW15,"<="&AQ$15:BW15)
    order_weight_range_index = index_and_range_tuple_by_name_dict[order_weight_header][0]

    range1_first_row_fixed = range1_last_row_fixed = range1_first_col_fixed = range1_last_col_fixed = False
    range2_first_col_fixed = range2_first_row_fixed = False

    if write_col:
        range1_first_row_fixed = range1_last_row_fixed = True
        range2_first_col_fixed = True
        format_func = xlsx_basics.format_single_col_range
    else:
        range1_first_col_fixed = range1_last_col_fixed = True
        range2_first_row_fixed = True
        format_func = xlsx_basics.format_single_static_grid_row_range

    order_weight_range1_str = format_func(val_sheet, order_weight_range_index, first_col_fixed=range1_first_col_fixed,
                                          first_row_fixed=range1_first_row_fixed,
                                          last_col_fixed=range1_last_col_fixed,
                                          last_row_fixed=range1_last_row_fixed)

    order_weight_range2_str = format_func(val_sheet, order_weight_range_index, first_col_fixed=range2_first_col_fixed,
                                          first_row_fixed=range2_first_row_fixed)

    rank_formula_str = "COUNTIF({0},\"<=\"&{1})".format(order_weight_range1_str, order_weight_range2_str)
    return rank_formula_str
