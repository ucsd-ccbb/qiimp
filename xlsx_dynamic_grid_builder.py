import xlsx_basics
import xlsx_static_grid_builder


def write_dynamic_validation_grid(val_sheet, index_and_range_str_tuple_by_header_dict):
    """

    :type val_sheet: xlsx_static_grid_builder.ValidationWorksheet
    """
    # fill out the dynamic grid

    # =IF(
    #       B7=" ",
    #       " ",
    #       HYPERLINK(
    #           CONCATENATE(
    #               "#metadata!",
    #               ADDRESS(
    #                   INDEX(
    #                      $AL$2:$AL$11,
    #                      MATCH(
    #                        ROWS($AJ$2: AJ7),
    #                        $AJ$2:$AJ$11,
    #                        0
    #                      ),
    #                      0
    #                   ),
    #                   $AQ$14
    #               )
    #           ),
    #           INDEX(
    #               $AO$2:$AO$11,
    #               MATCH(
    #                   ROWS($AJ$2: AJ7),
    #                   $AJ$2:$AJ$11,
    #                   0
    #               ),
    #               0
    #           )
    #       )
    # )

    # Add the standard url link format.
    url_format = val_sheet.workbook.add_format({
        'font_color': 'blue',
        'underline': 1
    })

    # TODO: write the anonymized name column--this is just placeholder code
    xlsx_basics.write_header(val_sheet, val_sheet.ANONYMIZED_NAME_HEADER, 0)
    for curr_row_index in range(val_sheet.first_data_row_index, val_sheet.last_data_row_index + 1):
        row_rank_num = _format_dynamic_rank_formula_str(val_sheet, curr_row_index,
                                                        index_and_range_str_tuple_by_header_dict,
                                                        for_row=True)
        anonymized_name_metadata_col_single_cell_range_str = xlsx_basics.format_range(
            # TODO: Need to replace w col index of real anonymized name validation column in static grid!
            # am currently ASSUMING that it is the first column; can I be sure of that?
            val_sheet.first_static_grid_col_index,
            index_and_range_str_tuple_by_header_dict[val_sheet.COL_IN_METADATA_HEADER][0],
            first_row_fixed=True, first_col_fixed=True, last_col_fixed=True, last_row_fixed=True)

        row_in_metadata_fixed_range_str = index_and_range_str_tuple_by_header_dict[val_sheet.ROW_IN_METADATA_HEADER][1]
        metadata_row_index_str = "INDEX({row_in_metadata_fixed_range_str},{row_rank_num},0)".format(
            row_in_metadata_fixed_range_str=row_in_metadata_fixed_range_str, row_rank_num=row_rank_num)

        concat_str = "CONCATENATE(\"#metadata!\",ADDRESS({metadata_row_index_str}," \
                     "{anonymized_name_metadata_col_single_cell_range_str}))".format(metadata_row_index_str=metadata_row_index_str,
                                                                                     anonymized_name_metadata_col_single_cell_range_str=anonymized_name_metadata_col_single_cell_range_str)

        conditional_name_fixed_range_str = index_and_range_str_tuple_by_header_dict[val_sheet.ANONYMIZED_NAME_HEADER][1]
        conditional_name_index_str = "INDEX({conditional_name_fixed_range_str},{row_num},0)".format(conditional_name_fixed_range_str=conditional_name_fixed_range_str,
                                                                   row_num=row_rank_num)
        # TODO: refactor hardcoded zero
        curr_cell = xlsx_basics.format_range(0, curr_row_index)
        first_grid_cell= xlsx_basics.format_range(val_sheet.first_data_col_index, curr_row_index)
        full_formula = "=IF({first_grid_cell}=\" \",\" \",HYPERLINK({concat_str},{conditional_name_index_str}))".format(
            first_grid_cell=first_grid_cell, concat_str=concat_str, conditional_name_index_str=conditional_name_index_str)
        val_sheet.worksheet.write_formula(curr_cell, full_formula, url_format)

    # write the colored hyperlink columns
    # apparently can't add alignment to a conditional format :(
    centered_format = xlsx_basics.make_format(val_sheet.workbook, {'align': 'center'})

    # at outer level, move across columns
    for curr_col_index in range(val_sheet.first_data_col_index, val_sheet.last_data_col_index + 1):
        val_sheet.worksheet.set_column(curr_col_index, curr_col_index, None, centered_format)

        col_rank_num = _format_dynamic_rank_formula_str(val_sheet,
                                                        val_sheet.first_static_grid_col_index + curr_col_index - 1,
                                                        index_and_range_str_tuple_by_header_dict, for_row=False)

        col_already_valid_condition = _format_range_already_valid_formula_str(
            val_sheet, col_rank_num, index_and_range_str_tuple_by_header_dict, for_row=False)

        first_data_cell_in_col_range_str = xlsx_basics.format_range(curr_col_index, val_sheet.first_data_row_index)
        static_grid_header_row_fixed_range_str = xlsx_basics.format_single_static_grid_row_range(val_sheet, val_sheet.name_row_index,
                                                                                                 first_col_fixed=True, first_row_fixed=True,
                                                                                                 last_col_fixed=True, last_row_fixed=True)

        header_formula = "=IF({first_data_cell_in_col_range_str}=\" \", \" \", INDEX({static_grid_header_row_fixed_range_str}, 1, {col_rank_num}))".format(
            first_data_cell_in_col_range_str=first_data_cell_in_col_range_str, static_grid_header_row_fixed_range_str=static_grid_header_row_fixed_range_str, col_rank_num=col_rank_num
        )
        xlsx_basics.write_header(val_sheet, header_formula, curr_col_index)

        # at inner level, move down rows
        for curr_row_index in range(val_sheet.first_data_row_index, val_sheet.last_data_row_index + 1):
            cell_formula = _generate_dynamic_grid_cell_formula_str(val_sheet, col_rank_num, col_already_valid_condition,
                                                                   curr_row_index,
                                                                   index_and_range_str_tuple_by_header_dict)
            curr_cell = xlsx_basics.format_range(curr_col_index, curr_row_index)
            val_sheet.worksheet.write_formula(curr_cell, cell_formula)

    _write_dynamic_grid_conditional_formatting(val_sheet)


def _write_dynamic_grid_conditional_formatting(val_sheet):
    """

    :type val_sheet: xlsx_static_grid_builder.ValidationWorksheet
    """
    # Light red fill with dark red text
    red_format = xlsx_basics.make_format(val_sheet.workbook, {'bg_color': '#FFC7CE', 'font_color': '#9C0006',
                                                              'underline': 1})

    # Green fill with (same) green text
    green_format = xlsx_basics.make_format(val_sheet.workbook, {'bg_color': '#C6EFCE', 'font_color': '#C6EFCE'})

    # TODO: hmm, maybe need to extend this to entire columns, in case user adds more samples?
    dynamic_grid_range = xlsx_basics.format_range(val_sheet.first_data_col_index, val_sheet.first_data_row_index,
                                                  val_sheet.last_data_col_index, val_sheet.last_data_row_index)

    val_sheet.worksheet.conditional_format(dynamic_grid_range, {'type': 'cell',
                                                                'criteria': '==',
                                                                'value': "\"\"",
                                                                'format': green_format})

    val_sheet.worksheet.conditional_format(dynamic_grid_range, {'type': 'cell',
                                                                'criteria': '==',
                                                                'value': "\"Fix\"",
                                                                'format': red_format})


def _generate_dynamic_grid_cell_formula_str(val_sheet, col_rank_num, col_already_valid_condition, curr_row_index,
                                            index_and_range_str_tuple_by_header_dict):
    """

    :type val_sheet: xlsx_static_grid_builder.ValidationWorksheet
    """
    # =IF(OR(INDEX($AK$2:$AK$11,MATCH(ROWS($A$2:A2),$AJ$2:$AJ$11,0),1)>=100000,
    # INDEX($AQ$15:$BW$15,1,MATCH(COLUMNS($AQ$16:AQ16),$AQ$16:$BW$16,0))>=100000)," ",
    # IF(INDEX($AQ$2:$BW$11,MATCH(ROWS($AJ$2:AJ2),$AJ$2:$AJ$11,0),MATCH(COLUMNS($AQ$16:AQ16),$AQ$16:$BW$16,0)),
    # HYPERLINK("#",""),HYPERLINK(CONCATENATE("#metadata!",
    # ADDRESS(INDEX($AL$2:$AL$11,MATCH(ROWS($AJ$2:AJ2),$AJ$2:$AJ$11,0),0),
    # INDEX($AQ$14:$BW$14,1,MATCH(COLUMNS($AQ$16:AQ16),$AQ$16:$BW$16,0)))),"Fix")))

    row_rank_num = _format_dynamic_rank_formula_str(val_sheet, curr_row_index, index_and_range_str_tuple_by_header_dict,
                                                    for_row=True)

    row_already_valid_condition = _format_range_already_valid_formula_str(val_sheet, row_rank_num,
                                                                          index_and_range_str_tuple_by_header_dict,
                                                                          for_row=True)

    static_grid_cell_contents = _format_static_grid_cell_reference_formula_str(val_sheet, row_rank_num, col_rank_num)

    hyperlink_to_metadata_grid_cell = _format_hyperlink_to_metadata_grid_cell(
        val_sheet, row_rank_num, col_rank_num, index_and_range_str_tuple_by_header_dict)

    # if the validation status of the metadata row and column entitled to this cell is TRUE, just put an empty
    # hyperlink in the cell; if the validation status of the metadata row and column entitled to this cell is FALSE,
    # put a hyperlink to the relevant metadata cell
    hyperlink_for_valid_or_invalid_cell = "IF({is_valid_cell}, HYPERLINK(\"#\",\"\"), {metadata_hyperlink})".format(
        is_valid_cell=static_grid_cell_contents, metadata_hyperlink=hyperlink_to_metadata_grid_cell)

    # big finish!
    result = "=IF(OR({row_already_valid},{col_already_valid}), \" \",{hyperlink_for_valid_or_invalid_cell})".format(
        row_already_valid=row_already_valid_condition, col_already_valid=col_already_valid_condition,
        hyperlink_for_valid_or_invalid_cell=hyperlink_for_valid_or_invalid_cell)

    return result


def _format_dynamic_rank_formula_str(val_sheet, curr_range_index, index_and_range_str_tuple_by_header_dict, for_row):
    """

    :type val_sheet: xlsx_static_grid_builder.ValidationWorksheet
    """
    # #1: Get the row_rank for the metadata row that should be shown in this validation row
    # (e.g., if we're in validation row 5, we should be showing the metadata row with row_rank 5).
    # MATCH(ROWS($AJ$2:AJ2),$AJ$2:$AJ$11,0)
    # or
    # # 2: Get the col_rank for the metadata column that should be shown in this validation column
    # (e.g., if we're in validation column 6, we should be showing the metadata column with col_rank 6).
    # MATCH(COLUMNS($AQ$16:AQ16),$AQ$16:$BW$16,0)

    # TODO: I think the second AJ occurrence in ROWS should be fixed, so wrote code this way, but it ISN'T this
    # way in manual worksheet; double-check code functionality!

    rank_header = val_sheet.ROW_RANK_HEADER if for_row else val_sheet.COL_RANK_HEADER
    rank_index_and_range_tuple = index_and_range_str_tuple_by_header_dict[rank_header]
    rank_range_index = rank_index_and_range_tuple[0]
    rank_fixed_range_str = rank_index_and_range_tuple[1]

    if for_row:
        excel_func_name = "ROWS"
        first_col_index = rank_range_index
        first_row_index = val_sheet.first_data_row_index
        last_col_index = rank_range_index
        last_row_index = curr_range_index
    else:
        excel_func_name = "COLUMNS"
        first_col_index = val_sheet.first_static_grid_col_index
        first_row_index = rank_range_index
        last_col_index = curr_range_index
        last_row_index = rank_range_index

    rank_to_curr_point_range = xlsx_basics.format_range(first_col_index, first_row_index,
                                                        second_col_index=last_col_index,
                                                        second_row_index=last_row_index, first_col_fixed=True,
                                                        first_row_fixed=True)

    rank_num = "MATCH({excel_func_name}({rank_to_curr_point_range}),{rank_fixed_range_str},0)".format(
        excel_func_name=excel_func_name, rank_to_curr_point_range=rank_to_curr_point_range,
        rank_fixed_range_str=rank_fixed_range_str)
    return rank_num


def _format_range_already_valid_formula_str(val_sheet, rank_num, index_and_range_str_tuple_by_header_dict, for_row):
    """

    :type val_sheet: xlsx_static_grid_builder.ValidationWorksheet
    """
    # Get the value for row_order_weight for the metadata row ranked to be shown on this validation row
    # (column is 1 because the range is only 1 column wide, so always want first column, and they're 0-indexed :)
    # If the row_order_weight for the metadata row that should be shown on this line is >=10000,
    # that means that this metadata row is already valid across all columns (or just doesn't exist);
    # either way, string will evaluate to true (which means any content for this metadata row shouldn't be shown
    # in the dynamic grid).
    # (INDEX($AK$2:$AK$11,MATCH(ROWS($A$2:A2),$AJ$2:$AJ$11,0),1)>=100000
    # or
    # Get the value for col_order_weight for the metadata column that should be shown in this validation column
    # (row is 1 because the range is only 1 row long, so we always want the first row, and they're *1*-indexed :)
    # If the col_order_weight for the metadata column that should be shown in this column is >=10000,
    # that means that this metadata column is already valid across all rows, which means any content for this
    # metadata column shouldn't be shown in the dynamic grid).
    # INDEX($AQ$15:$BW$15,1,MATCH(COLUMNS($AQ$16:AQ16),$AQ$16:$BW$16,0))>=100000)

    if for_row:
        order_weight_header = val_sheet.ROW_ORDER_WEIGHT_HEADER
        row_num = rank_num
        col_num = 1
    else:
        order_weight_header = val_sheet.COL_ORDER_WEIGHT_HEADER
        row_num = 1
        col_num = rank_num

    order_weight_fixed_range_str = index_and_range_str_tuple_by_header_dict[order_weight_header][1]
    range_already_valid_condition = "INDEX({order_weight_fixed_range_str},{row_num},{col_num})>=100000".format(
        order_weight_fixed_range_str=order_weight_fixed_range_str, row_num=row_num, col_num=col_num)
    return range_already_valid_condition


def _format_static_grid_cell_reference_formula_str(val_sheet, row_rank_num, col_rank_num):
    """

    :type val_sheet: xlsx_static_grid_builder.ValidationWorksheet
    """
    # The contents here will be either "TRUE" or "FALSE", depending on whether the relevant cell in the metadata
    # sheet is valid or invalid according to the static validation grid
    #
    # INDEX($AQ$2:$BW$11,MATCH(ROWS($AJ$2:AJ2),$AJ$2:$AJ$11,0),MATCH(COLUMNS($AQ$16:AQ16),$AQ$16:$BW$16,0))
    static_grid_fixed_range_str = xlsx_basics.format_range(val_sheet.first_static_grid_col_index,
                                                           val_sheet.first_data_row_index,
                                                           second_col_index=val_sheet.last_static_grid_col_index,
                                                           second_row_index=val_sheet.last_data_row_index,
                                                           first_col_fixed=True, first_row_fixed=True,
                                                           last_col_fixed=True, last_row_fixed=True)

    static_grid_cell_contents = "INDEX({static_grid_fixed_range_str},{row_rank_num},{col_rank_num})".format(
        static_grid_fixed_range_str=static_grid_fixed_range_str, row_rank_num=row_rank_num,
        col_rank_num=col_rank_num)
    return static_grid_cell_contents


def _format_hyperlink_to_metadata_grid_cell(val_sheet, row_rank_num, col_rank_num,
                                            index_and_range_str_tuple_by_header_dict):
    """

    :type val_sheet: xlsx_static_grid_builder.ValidationWorksheet
    """

    # Get the row number and column number of the cell in the metadata sheet that is entitled to this validation
    # cell. Note that these are expected to be in the helper columns in uniformly increasing order, so that if, say,
    # the row rank is 5, the contents of the 5th (well, 6th because there's a header line, but you get the point)
    # cell down in the row_in_metadata column will be the row number in the metadata spreadsheet of the 5th metadata
    # data row (keep in mind there's a header there too, so the number won't really be 5--probably 6)
    #
    # INDEX($AL$2:$AL$11,MATCH(ROWS($AJ$2:AJ2),$AJ$2:$AJ$11,0),0),
    # INDEX($AQ$14:$BW$14,1,MATCH(COLUMNS($AQ$16:AQ16),$AQ$16:$BW$16,0))
    row_in_metadata_fixed_range_str = index_and_range_str_tuple_by_header_dict[val_sheet.ROW_IN_METADATA_HEADER][1]
    col_in_metadata_fixed_range_str = index_and_range_str_tuple_by_header_dict[val_sheet.COL_IN_METADATA_HEADER][1]
    metadata_grid_cell_range = "INDEX({row_in_metadata_fixed_range_str},{row_rank_num},0), " \
                               "INDEX({col_in_metadata_fixed_range_str},1,{col_rank_num}" \
                               ")".format(row_in_metadata_fixed_range_str=row_in_metadata_fixed_range_str,
                                          row_rank_num=row_rank_num,
                                          col_in_metadata_fixed_range_str=col_in_metadata_fixed_range_str,
                                          col_rank_num=col_rank_num)

    hyperlink_to_metadata_grid_cell = "HYPERLINK(CONCATENATE(\"#{sheet_name}!\", " \
                                      "ADDRESS({metadata_grid_cell_range}))," "\"Fix\"" \
                                      ")".format(sheet_name=val_sheet.metadata_sheet_name,
                                                 metadata_grid_cell_range=metadata_grid_cell_range)

    return hyperlink_to_metadata_grid_cell
