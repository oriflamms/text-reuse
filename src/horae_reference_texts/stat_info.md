# Information on the stats of the file

In ref_texts we used the file `Export_stutzmann_horae_t65_Work.csv`
in order to analyse the text of reference.
In those texts we calculated the following statistics :

* count of words : 14814.0
* mean : 25.60577831780748
* min : 1.0
* max : 1510.0
* standard deviation : 39.212935881792724
* nb of different words : 41889

The 100 most used words and 100 least used words are stocked on
files generated during the computing of the code.

# How to use :

To launch the code :
* Only the stats : `python src/horae_reference_texts/ref_texts.py --file <path>`
* Only the stats with a specification on the liturgical function: `python src/horae_reference_texts/ref_texts.py --file <path> --liturgical-function <string>`
* Stats and output in txt format : `python src/horae_reference_texts/ref_texts.py --file <path> --output-path <path>`
* Stats and metadata file in csv format : `python src/horae_reference_texts/ref_texts.py --file <path> --metadata-path <path>`

Example : `python src/horae_reference_texts/ref_texts.py --file tests/data/Export_stutzmann_horae_t65_Work.csv --liturgical-function Psalm --output-path /folder/`