curl https://repo.continuum.io/miniconda/Miniconda3-latest-Linux-x86_64.sh -o miniconda_py3.sh
bash miniconda_py3.sh -b -p $HOME/miniconda3
echo "export PATH=\"$HOME/miniconda3/bin:\$PATH\"" >>$HOME/.bashrc
source $HOME/.bashrc		
conda update conda -y
conda install python=3.5 -y
conda install pyyaml -y
conda install tornado -y
conda install xlsxwriter -y
conda install openpyxl -y
conda install pandas -y
conda install git -y
git clone https://github.com/ucsd-ccbb/qiimp.git
cd qiimp
# ensure URL/port in metadata_wizard_server.py main and in metadataWizard.js document.ready are set for instance
python metadata_wizard_server.py
