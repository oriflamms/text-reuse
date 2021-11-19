# Text-matcher information
The purpose of text_matcher_interface.py is to create a HTML interface to help the user better see the correspondence between a volume and the reference texts inside.
It takes as argument :
* the txt file of a volume to study
* a directory of reference texts to be found in the volume concerned
* an html file to display the interface
* a csv file of metadata containing tuples with the Arkindex ID and the annotation of the reference texts

## How to use :

To launch the code : `python src/text-matcher/text_matcher_interface.py --input-txt <path> --input-folder <path> --metadata <path> --input-html <path>`

Example : `python src/text-matcher/text_matcher_interface.py --input-txt data/50texts/0a7da4a2-23ad-4d97-a868-c2960f1f0d2a.txt --input-folder data/psalm/ --metadata tests/data/metadata.csv  --input-html src/text-matcher/interface.html`

On top of the page you can see a counter with the number of recognised text.

Once the interface is on display look throughout the text to see the green box containing the match, you can hoover them to see the name of the reference text.

