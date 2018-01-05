*How to use this workbook:*

1) Start on the 'Metadata' tab:a) Entering your sample names, either one by
one or via copy-paste. Note: Sample names may only contain alphanumeric
characters (A-Z,a-z,0-9) and the period character (.)b) As you enter each
sample name, fields (columns) with only one permitted value will
automatically be completed based on the information you supplied in the web
formc) Fill in the remaining information for each metadata field (column);
if you have provided categorical variables, and/or permitted null values,
cells will contain a dropdown list with the acceptable values to help with
correct entry.
i) If your input is incorrect, you will be alerted and your input will be
deleted so you can try again
ii) You may copy-paste information from another excel file or document to
complete the fields, but if you do the dropdown lists and built-in
error-correction support functions will be removed
d) for fields auto-populated by the online wizard, you can access the field
definitions on the Data Dictionary tab
2) Once you have completed entering your samples, go to the 'Validation'
tab which will display any errors detected based on the rules provided in
the web form.
a) You will see which cells need to be altered with a red "Fix" cell.
b) By selecting "Fix" in a cell, you will be brought to that incorrect cell
within the "Metadata" sheet as to change it.
c) Once there are no red "Fix" cells, your metadata will be considered
valid for uploading to Qiita.
i) Note: Qiita only accepts .tsv or .txt files, so if you only have a
single metadata file (single sample type), you should save the workbook and
then use "Save As..." to save the first sheet as a plain tab-separated
value file.
ii) If you have more than one metadata file (multiple sample types), then
use the online wizard to merge your files together before uploading. All
metadata fields not present for a sample will be described as 'not
applicable' for those samples.

*Troubleshooting:*
*I can't find the metadata field(s) I want.*
Return to the Metadata Wizard online form, and click on 'PACKAGE FIELDS'.
Then click the button Select File to upload your template. Collapse the
'PACKAGE FIELDS' section and click on the 'CUSTOM FIELDS' section. Enter
the custom field(s) you'd like to add in the text box and click 'Add
Field'. Complete the form to describe your new field(s). Submit the form
and download the new template.

*I can't find the categorical value I want/I want to add more options to my
metadata field.*
Return to the Metadata Wizard online form, and click on 'PACKAGE FIELDS'.
Then click the button Select File to upload your template. Collapse the
'PACKAGE FIELDS' section and click on the 'CUSTOM FIELDS' section. Select
the field where you'd like to enter the value and ensure the Categorical
Field Type is selected. Modify the parameters to add a new category or null
value to your field as appropriate. Submit the form and download the new
template.


*I can't enter the numeric value I want.*
Return to the Metadata Wizard online form, and click on 'PACKAGE FIELDS'.
Then click the button Select File to upload your template. Collapse the
'PACKAGE FIELDS' section and click on the 'CUSTOM FIELDS' section. Select
the field where you'd like to enter the value and ensure the Continuous
Field Type is selected. Modify the parameters to add a new category or null
value to your field as appropriate. Submit the form and download the new
template.


*I have protected health information that I do not want to display.*
Return to the Metadata Wizard online form, and click on 'PACKAGE FIELDS'.
Then click the button Select File to upload your template. Collapse the
'PACKAGE FIELDS' section and click on the 'CUSTOM FIELDS' section. Select
the field where you'd like to enter the value and ensure the EBI Null Value
'missing: restricted access' is selected. In the 'Default' section, select
the option 'Allowed Missing Default' and ensure 'missing: restricted
access' is selected. Submit the form and download the new template.

This file was created by the Metadata Wizard VERSION at GENERATION_TIMESTAMP.