# cmi_metadata_wizard
Web application to collect metadata specifications from an experimenter and produce metadata input files with appropriate constraints

Note that this repository contains the full code necessary for the metadata wizard proof-of-concept demo to function, which includes code that ccbb-ucsd did not write (contained in the "third-party" folder).

## Requirements

* Hardware: A linux or OSX machine/instance with at least 1 GB of memory and at least 8 GB of storage
* Software: An installation of the `conda` package manager (either `Anaconda` or `miniconda`)

## Installation

1. Create and source a `conda` environment for the metadata wizard

        conda create -n metadata_wizard python=3 openpyxl tornado xlsxwriter PyYAML pandas git
        source activate metadata_wizard
    
3. Install the metadata wizard from github.com

        pip install --upgrade git+git://github.com/ucsd-ccbb/cmi_metadata_wizard.git
    
4. Find the `config.txt` file 

    * Find the location of your `conda` install's `site-packages` folder by running
        
            pip show cmi-metadata-wizard
    
    * Look for the line in the output that starts with `Location: ` and find the path it lists (for example, `/Users/Me/Applications/miniconda3/envs/metadata_wizard/lib/python3.6/site-packages`).  This will be referred to below as `sitepackagespath`.
    * The `config.txt` file will be at `sitepackagespath/metadata_wizard/settings/config.txt`
    
6. Edit the `[DEPLOYED]` section of the `config.txt` file to set the appropriate values for your installation

    * Set the `websocket_url` variable to the public hostname of the machine/instance (e.g., `ec2-34-215-148-70.us-west-2.compute.amazonaws.com`).  
    * If you want the port used to be something other than the default (8183), set the `listen_port` variable to the desired port. **Be sure that public access to this port is enabled on your machine!**
    
7. Start the metadata wizard

        start_metadata_wizard_server --deployed
    
   * If you are running the metadata wizard on your local host instead of on a publicly available host, run it *without* the `--deployed` switch.  It will then use the settings in the `[LOCAL]` section of the config instead of the `[DEPLOYED]` section. 
   * Note that seeing a number of `DeprecationWarning`s and `UserWarning`s like the examples below are expected and does not indicate a failure:
   
            /home/ec2-user/miniconda3/envs/metadata_wizard/lib/python3.6/site-packages/metadata_wizard/metadata_wizard_settings.py:48: DeprecationWarning: Call to deprecated function get_sheet_names (Use wb.sheetnames).sheet_names = openpyxl_workbook.get_sheet_names()
            /home/ec2-user/miniconda3/envs/metadata_wizard/lib/python3.6/site-packages/metadata_wizard/metadata_package_schema_builder.py:154: UserWarning: No filename specified for 'None'.
            warnings.warn("No filename specified for '{0}'.".format(a_dict))
  
  * When the metadata wizard is accessible, a `server ready` message will be printed to `STDOUT`
  * To stop the metadata wizard, type `Ctrl+c`

8. Access the metadata wizard through a browser at the URL of your instance + the port number, e.g. `http://ec2-18-236-71-136.us-west-2.compute.amazonaws.com:8181/`
    
    * Note that seeing a number of `tornado` warnings printed to the server `STDERR` when accessing the site, like the ones shown below, is expected and does not indicate a failure:
    
            WARNING:tornado.access:404 GET /static/third-party/microbiome/img/body-bg.png (128.54.20.205) 0.60ms
            WARNING:tornado.access:404 GET /static/third-party/microbiome/fonts/glyphicons-halflings-regular.woff (128.54.20.205) 0.45ms
            WARNING:tornado.access:404 GET /static/third-party/microbiome/fonts/glyphicons-halflings-regular.ttf (128.54.20.205) 0.49ms
            WARNING:tornado.access:404 GET /favicon.ico (128.54.20.205) 0.59ms
    
