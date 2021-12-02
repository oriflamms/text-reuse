# Text Reuse - HORAE project

text-reuse is a project that aims to help on the HORAE project (correspondence analysis of books of Heurs).

At this moment there are three features in the code:
* ref-texts: statistics on reference texts and file export
* sql-to-csv : sql database processing and export
* text-matcher : comparisons between two entities with details
* text-eval : evaluate the matcher

## Usage
### Installation
To install the project
Cloning the repository : `git clone https://gitlab.com/teklia/irht/text-reuse.git`
Install the tests : `pip3 install tox`
Run the test : `tox`


### ref-texts
In command line you can have statistic on the input file (Heurist base), you can also specify the liturgical function of the texts of interest.
You can extract the text in txt files (each text will have its own file named after its Arkindex ID)
You can also extract the metadata in a csv which contain the Arkindex ID and the Annotation ID (name of the element)

Example of line commands :
* Only the stats : `python src/horae_reference_texts/ref_texts.py --file tests/data/Export_stutzmann_horae_t65_Work.csv`
* Only the stats with a specification on the liturgical function: `python src/horae_reference_texts/ref_texts.py --file tests/data/Export_stutzmann_horae_t65_Work.csv --liturgical-function Psalm`
* Stats and output in txt format : `python src/horae_reference_texts/ref_texts.py --file tests/data/test_export_heurist_horae.csv --text-path folder/`
* Stats and metadata file in csv format : `python src/horae_reference_texts/ref_texts.py --file tests/data/Export_stutzmann_horae_t65_Work.csv --metadata-path folder/`
* Stats, metadata and output in txt file : `python src/horae_reference_texts/ref_texts.py --file tests/data/Export_stutzmann_horae_t65_Work.csv --metadata-path folder/ --text-path folder/`


### sql-to-csv
In command line you can extract in csv or in txt the text contained in a sqlite dump.
The file fill be named after the ID of the book and will be constructed :
* tuples { ID line, text of the page }  for csv extraction
* an only line for all the book for txt extraction

Example of line commands :
* In txt : `python src/sql_to_csv/sql_to_csv.py --file tests/data/horae-50-mss-ml-20211116-121450.sqlite --savefile folder/ --output-format txt`
* In csv : `python src/sql_to_csv/sql_to_csv.py --file tests/data/horae-50-mss-ml-20211116-121450.sqlite --savefile folder/ --output-format csv`


### text-matcher
In command line you can have information on the matches of an input volume and input folder of reference texts.
You have to specify the path of the metadata file that have information on the ID Arkindex and the ID Annotation (you can generate it with sql-to-csv)
You also have to specify the path of the HTML file where the script will be written. !!! Careful the code will overwrite it and you will loose what's on it !!!
A normalisation of the text will be done automatically, if you don't want it set `--normalization False`

Example of line commands :
* `python src/text-matcher/text_matcher_interface.py --input-txt tests/data/test_volume/0a7da4a2-23ad-4d97-a868-c2960f1f0d2a.txt --input-folder tests/data/test_psaume/ --metadata tests/data/metadata.csv --output-html src/text-matcher/interface.html`


### text_eval
In command line you can fill a csv with predictions and a csv with the real values to have the precision and the recall of the text-matcher
Works with the matching of h_tag at the end of the name of prayer

Example of lign commands :
* `python src/evaluation/text_eval.py --pred-file tests/data/h_evaluation_df.csv --true-file tests/data/h_50mms_text_segment.csv`

