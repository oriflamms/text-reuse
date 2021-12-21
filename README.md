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

| command                                                                                                                      | output               | use                                     | wid                                                                       |
|------------------------------------------------------------------------------------------------------------------------------|----------------------|-----------------------------------------|---------------------------------------------------------------------------|
| `python src/horae_reference_texts/ref_texts.py --f tests/data/Export_stutzmann_horae_t65_Work_Psalms.csv`                    | *_frequencies.csv    | none                                    | Check statistic                                                           |
| `python src/horae_reference_texts/ref_texts.py --f tests/data/Export_stutzmann_horae_t65_Work_Psalms.csv -t trash/ -l Psalm` | [id_arkindex]*.csv   | none                                    | Check text from the liturgical function                                   |
| `python src/horae_reference_texts/ref_texts.py --f tests/data/Export_stutzmann_horae_t65_Work_Psalms.csv -m trash/ -l Psalm` | metadata_heurist.csv | text_matcher_interface.py  text_eval.py | Have the metadata of the heurist export on the text from the lit function |


### sql-to-csv
In command line you can extract in csv or in txt the text contained in a sqlite dump.
The file fill be named after the ID of the book and will be constructed :
* tuples { ID line, text of the page }  for csv extraction
* an only line for all the book for txt extraction
You can also specify with `-a` the extraction of only the fully annotated volumes with the format bio and text (extraction text line)

| command                                                                                                                    | output                                           | use                                      | wid                                                                                                                                                |
|----------------------------------------------------------------------------------------------------------------------------|--------------------------------------------------|------------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------|
| `python src/sql_to_csv/sql_to_csv.py -s tests/data/new_horae-complete-20211213-162802.sqlite -a -o trash/ -f txt -l Psalm` | line_*.txt  true_*.bio complete_text_segment.csv | text_matcher_interface.py   text_eval.py | For fully annotated books : .txt : transcription of the volumes (text_line) .bio : bio format of the truth  complete.csv : dataframe of evaluation |
| `python src/sql_to_csv/sql_to_csv.py -s tests/data/horae-50-mss-ml-20211116-121450.sqlite -o folder/ -f txt`               | [volume_id]*.txt                                 | text_matcher_interface.py                | transcription of the volumes (paragraph) for 50mss corpus                                                                                          |
| `python src/sql_to_csv/sql_to_csv.py -s tests/data/horae-50-mss-ml-20211116-121450.sqlite -o folder/ -f csv`               | [volume_id].csv                                  | none                                     | transcription of the volumes, one row per page with ID.                                                                                            |
| `python src/sql_to_csv/sql_to_csv.py -s tests/data/horae-50-mss-ml-20211116-121450.sqlite -o folder/ -f txt -t -l Psalm`   | 50_mss_text_segment.csv                          | text_eval.py                             | dataframe of evaluation                                                                                                                            |
| `python src/sql_to_csv/sql_to_csv.py -s tests/data/horae-50-mss-ml-20211116-121450.sqlite -o folder/ -f txt -m`            | metadata_volume.csv                              | text_eval.py                             | metadata for the volume                                                                                                                            |


### text-matcher
In command line you can have information on the matches of an input volume and input folder of reference texts.
You have to specify the path of the metadata file that have information on the ID Arkindex and the ID Annotation (you can generate it with sql-to-csv)
You also have to specify the path of the HTML file where the script will be written. !!! Careful the code will overwrite it and you will loose what's on it !!!
A normalisation of the text will be done automatically, if you don't want it set `--normalization False`
You can also specify the parameter of the text_matcher with `-t` for the threshold, `-c` for the cutoff and `-g` for the ngrams. By defaults those values are at 3 5 3 respectively.
There is the possibility to create a HTML file for à bio file with `-b [path of the folder with file .bio]`

| command                                                                                                                                       | output                                                              | use                           | wid                                                              |
|-----------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------------------------------|-------------------------------|------------------------------------------------------------------|
| `python src/text-matcher/text_matcher_interface.py -v trash/vol/ -r data/psalm/ -m data/metadata_heurist.csv -o trash/ -n -t 3 -c 4 -g 3`     | line_date_*.bio  line_date_*.html evaluation_df.csv                 | NERval none text_eval.py      | Evaluation and observation with parameter of the textmatcher     |
| `python src/text-matcher/text_matcher_interface.py -v trash/vol/ -r data/psalm/ -m data/metadata_heurist.csv -o trash/ -n -b trash/line_bio/` | line_date_*.bio  line_date_*.html evaluation_df.csv true_date*.html | NERval none text_eval.py none | Evaluation and observation with default parameter of textmatcher |


### text_eval
In command line you can fill a csv with predictions and a csv with the real values to have the precision and the recall of the text-matcher
Works with the matching of h_tag at the end of the name of prayer.
Generate the csv of data with the sum of each text found in the file.

| command                                                                                                                                                                                       | output                          | use  | wid                                                            |
|-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------|------|----------------------------------------------------------------|
| `python src/evaluation/text_eval.py -p tests/data/h_evaluation_df.csv -t tests/data/h_50mms_text_segment.csv -h tests/data/metadata_heurist.csv -v tests/data/metadata_volume.csv -o folder/` | result_pred.csv result_true.csv | none | Evaluate the dataframe in input (classication multiple output) |

