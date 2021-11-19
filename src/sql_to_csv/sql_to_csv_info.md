# SQL to CSV information

This file has the following use :

* Compare the number of books in Arkindex and in the SQL database
* Write in csv file the uid of the page and its transcription (one book = one csv, named after the uid of the book)
* Write in a txt file the book as a single line with the name of the ID of the book

As of the 08/11/2021 there was 1115 book listed on Arkindex and 1158 in the SQL db

## How to use :

To launch the code : `python src/sql_to_csv/sql_to_csv.py --file <path> --savefile <path> --output-format <string>`

Example txt: `python src/sql_to_csv/sql_to_csv.py --file tests/data/horae-50-mss-ml-20211116-121450.sqlite --savefile folder/ --output-format txt`
Example txt: `python src/sql_to_csv/sql_to_csv.py --file tests/data/horae-50-mss-ml-20211116-121450.sqlite --savefile folder/ --output-format csv`