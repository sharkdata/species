# Species

Python code used to keep marine monitoring species lists in sync with 
WoRMS, World Register of Marine Species (http://www.marinespecies.org/).

The WoRMS REST webservice (http://www.marinespecies.org/rest/) is used to access WoRMS. 

## Installation

Check that Python3, venv and git are installed. Create a directory for the code. Start a terminal window.

    git clone https://github.com/sharkdata/species.git .
    python3 -m venv venv
    source venv/bin/activate # On Windows "venv\Scripts\activate".
    pip install -r requirements.txt 

## Usage

Edit the file **data_in/indata_taxa_by_name.txt**. 

Add scientific names for the species you want to have in your list. 
Higher taxa will be automatically generated based on the classification for
each taxa in the list.

If there are problems with homonyms there is a possibility to add AphiaId. 
Use the file **data_in/indata_taxa_by_aphia_id.txt**. 

Run the command:

    python extract_taxa_from_worms_main.py

Check the files in **data_out**. You will find some tab delimited text files (that easily 
can be opened in Excel or LibreOffice Calc):

- **taxa_worms.txt**   Contains basic information for each taxa and parent taxa.

- **translate_to_worms.txt**   If the species in the indata list is not valid any longer, the will appear here and translated to the valid taxa.

- **errors.txt**   Contains info about species that couldn't be included automatically. There are two main reasons: Error code 204 = "not found" and error code 206 = "multiple alternatives was found".

To fix the errors, you have to check out valid AphiaID (http://www.marinespecies.org/aphia.php?p=search) for each species and add 
them manually to the file **data_in/indata_taxa_by_aphia_id.txt**. 

If you want to add a few new taxa to existing files, then you can copy the files **taxa_worms.txt** and **translate_to_worms.txt**
from the **data_out** directory to the **data_in** directory and add the new species to the **data_in/indata_species_by_name.txt** file.
Then it will run must faster since WoRMS is only called for the new taxa.

## Contact info

- shark@smhi.se 

