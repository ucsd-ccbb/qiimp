# QIIMP
*(Pronounced "chimp"!)*

Web application to collect metadata specifications from an experimenter and produce metadata input files with appropriate constraints

Note that this repository contains the full code necessary for QIIMP to function, which includes code that ccbb-ucsd did not write (contained in the "third-party" folder).

## Requirements

* Hardware: A linux or OSX machine/instance with at least 1 GB of memory and at least 8 GB of storage
* Software: An installation of the `conda` package manager (either `Anaconda` or `miniconda`)

## Installation

1. Create and source a `conda` environment for QIIMP

        conda create -n qiimp python=3 openpyxl tornado xlsxwriter PyYAML pandas git
        source activate qiimp
    
3. Install QIIMP from github.com

        pip install --upgrade git+git://github.com/ucsd-ccbb/qiimp.git
    
4. Find the `config.txt` file 

    * Find the location of your `conda` install's `site-packages` folder by running
        
            pip show qiimp
    
    * Look for the line in the output that starts with `Location: ` and find the path it lists (for example, `/Users/Me/Applications/miniconda3/envs/qiimp/lib/python3.6/site-packages`).  This will be referred to below as `sitepackagespath`.
    * The `config.txt` file will be at `sitepackagespath/qiimp/settings/config.txt`
    
6. Edit the `[DEPLOYED]` section of the `config.txt` file to set the appropriate values for your installation

    * Set the `websocket_url` variable to the public hostname of the machine/instance (e.g., `ec2-34-215-148-70.us-west-2.compute.amazonaws.com`).  
    * If you want the port used to be something other than the default (8183), set the `listen_port` variable to the desired port. **Be sure that public access to this port is enabled on your machine!**
    
7. Start the QIIMP server

        start_qiimp_server --deployed
    
   * If you are running QIIMP on your local host instead of on a publicly available host, run it *without* the `--deployed` switch.  It will then use the settings in the `[LOCAL]` section of the config instead of the `[DEPLOYED]` section. 
   * If you see `UserWarning`s like the examples below:
   
            /home/ec2-user/miniconda3/envs/qiimp/lib/python3.6/site-packages/qiimp/metadata_package_schema_builder.py:163: UserWarning: No filename specified for sample type 'sponge' in environment 'non-vertebrate'.
            warnings.warn("No filename specified for {0}.".format(context_description))
  
        * ... this indicates that not all environments and/or sample types have schema files defined for them in the `settings/environments.yaml` file for the installation.  
        * This is sometimes acceptable, specifically in cases in which the sample type or environment truly has no unique field definitions associated with it, such as the "other" sample type in the "base" environment.
        * However, it is more often an indication that not all expected configuration information for environment and sample type packages has been properly placed in the `settings/packages` directory.  
        * Thus, each such warning should be checked to ensure that it is expected.
  
    * When the QIIMP server is accessible, a `server ready` message will be printed to `STDOUT`

8. Access QIIMP through a browser at the URL of your instance + the port number, e.g. `http://ec2-18-236-71-136.us-west-2.compute.amazonaws.com:8181/`
            
9. If desired (when done using it), stop the QIIMP server by typing `Ctrl+c` on the server command line
    
