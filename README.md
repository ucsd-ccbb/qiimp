# cmi_metadata_wizard
Web application to collect metadata specifications from an experimenter and produce metadata input files with appropriate constraints

Note that this repository contains the full code necessary for the metadata wizard proof-of-concept demo to function, which includes code that ccbb-ucsd did not write (contained in the "third-party" folder).


## Installation

    conda create -n metadata_wizard python=3 openpyxl tornado xlsxwriter PyYAML panda
    source activate metadata_wizard
    cd <working dir>
    pip install --upgrade git+git://github.com/ucsd-ccbb/cmi_metadata_wizard.git
    cp <working dir>/config.txt /home/ec2-user/miniconda3/lib/python3.5/site-packages/metadata_wizard/settings/config.txt
    start_metadata_wizard_server --deployed
