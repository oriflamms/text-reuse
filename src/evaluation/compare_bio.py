#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import csv
import glob
import os
from pathlib import Path

import pandas as pd

ARKINDEX_VOLUME_URL = "https://arkindex.teklia.com/element/"


class Compare:
    def __init__(
        self,
        first_text=None,
        second_text=None,
        heurist_metadata=None,
        volume_metadata=None,
        reference_texts=None,
        output_path=None,
    ):
        """Initializes the class and generates the htmls that correspond to the input path types"""
        self.output_path = output_path
        self.name_output = None

        # Check the folder of reference texts
        if os.path.isdir(reference_texts):
            self.reference_texts = glob.glob(
                str(reference_texts) + "/**/*.txt", recursive=True
            )
        else:
            raise Exception("Your path to the reference folder do not lead to a folder")

        # Read the volume metadata
        with open(volume_metadata, "r") as file:
            self.volume_metadata = list(csv.reader(file, delimiter=","))

        # Check if the input are both directories and in that case create the html for each .bio file found
        if os.path.isdir(first_text) and os.path.isdir(second_text):
            print("Both directory")
            self.first_list = glob.glob(str(first_text) + "/**/*.bio", recursive=True)
            self.second_list = glob.glob(str(second_text) + "/**/*.bio", recursive=True)

            for first_file in self.first_list:
                for second_file in self.second_list:
                    if (
                        os.path.basename(first_file).split("_")[-1]
                        == os.path.basename(second_file).split("_")[-1]
                    ):
                        self.name_output = f"{'_'.join([os.path.basename(second_file).split('_')[1], os.path.basename(second_file).split('_')[-1].replace('.bio', '')])}.html"
                        self.first_text = self.read_bio(first_file, heurist_metadata)
                        self.second_text = self.read_bio(second_file, heurist_metadata)
                        self.align_text()

            print(f"The files have been generated at {self.output_path}")

        # Check if both of the input are the same type
        elif os.path.isdir(first_text) ^ os.path.isdir(second_text):
            if os.path.isdir(first_text):
                print("Your first argument is a directory but not your second.")
            else:
                print("Your second argument is a directory but not your first")
            raise Exception("Both of your argument must be the the same type")

        # Generate the comparison html for one couple
        else:
            print("Both file")
            self.name_output = "output.html"
            self.first_text = self.read_bio(first_text, heurist_metadata)
            self.second_text = self.read_bio(second_text, heurist_metadata)
            self.align_text()

            print(f"The file has been generated at {self.output_path}")

    def read_bio(self, bio_file, metadata):
        """Read a bio file and return a list of [WORD, TAG]"""
        with open(bio_file, "r") as file:
            data_raw = file.readlines()

        data_list = []
        word_list = []
        for row in data_raw:
            data_list.append(row.split())
            word_list.append(row.split()[0])

        df_bio = pd.DataFrame(data=data_list, columns=["word", "bio_tag"])

        list_index = []
        nb_func = 0

        for index, row in df_bio.iterrows():
            if index == len(df_bio) - 1:
                pass
            elif row["bio_tag"][0] == "B":
                if df_bio.loc[index + 1, "bio_tag"][0] == "I":
                    list_index.append(["start", index, row["bio_tag"].split("-")[1]])

                if (
                    df_bio.loc[index + 1, "bio_tag"] == "O"
                    or df_bio.loc[index + 1, "bio_tag"][0] == "B"
                ):
                    list_index.append(["solo", index, row["bio_tag"].split("-")[1]])

            elif row["bio_tag"][0] == "I" and (
                df_bio.loc[index + 1, "bio_tag"] == "O"
                or df_bio.loc[index + 1, "bio_tag"][0] == "B"
            ):
                list_index.append(["end", index + 1, row["bio_tag"].split("-")[1]])

        with open(metadata, newline="") as meta_file:
            data = list(csv.reader(meta_file, delimiter=","))

        end_tag = "</hov></marka>"
        start_tag = "<marka>"

        # for path in self.reference_texts:
        #   print(os.path.basename(path).replace('.txt',''))

        for row in reversed(list_index):
            if row[0] == "start" or row[0] == "solo":
                for data_row in data:
                    if data_row[1].split()[-1] == row[2]:
                        text_ref = ""
                        for ref_path in self.reference_texts:
                            if data_row[0] == os.path.basename(ref_path).replace(
                                ".txt", ""
                            ):
                                with open(os.path.join(ref_path), "r") as psalm_file:
                                    text_ref = psalm_file.read()
                        if row[0] == "start":
                            word_list.insert(
                                row[1],
                                (
                                    start_tag
                                    + f'<hov title="{data_row[1]} | Texte : {text_ref}">'
                                ),
                            )
                        if row[0] == "solo":
                            word_list.insert(
                                row[1],
                                (
                                    start_tag
                                    + f'<hov title="{data_row[1]} | Texte : {text_ref}">'
                                    + end_tag
                                ),
                            )
                        if start_tag == "<marka>":
                            start_tag = "<markb>"
                            end_tag = "</hov></markb>"
                        else:
                            start_tag = "<marka>"
                            end_tag = "</hov></marka>"

            elif row[0] == "end":
                word_list.insert(row[1], end_tag)

        text_volume = f'<p>Number of recognised texts : {nb_func}<br>{" ".join(str(row) for row in word_list)}</p>'
        return text_volume

    def align_text(self):
        """Align two text side-by-side and export the html file"""
        # Fetch the volume reference and create the Arkindex url
        ref_volume = ""
        volume_url = ""
        for row in self.volume_metadata:
            if row[0] == self.name_output.split("_")[-1].replace(".html", ""):
                ref_volume = row[1]
                volume_url = os.path.join(ARKINDEX_VOLUME_URL, row[0])

        # Fetch the information on the parameter of text matcher
        threshold = self.name_output.split("_")[0][0]
        cutoff = self.name_output.split("_")[0][1]
        ngram = self.name_output.split("_")[0][2]
        mindistance = self.name_output.split("_")[0][3:]

        # Compose the side by side layout
        content = f' <div class="row"><div class="column">{self.first_text}</div><div class="column">{self.second_text}</div></div> '

        # Write html file
        with open(os.path.join(self.output_path, self.name_output), "w") as html_file:
            html_file.write(
                '<html><head><meta charset="UTF-8"><link rel="stylesheet" href="com_style.css"><title>Align text</title></head><body>'
            )
            html_file.write("<center><h1>Content</h1>")
            html_file.write(
                "<p><marka><hov title='Just like that'>Hover on the highlighted text to see the referenced text</hov></marka><br>"
                f"Volume references: {ref_volume}<br>"
                f"<a href='{volume_url}'>Arkindex link</a><br>"
                f"Text-Matcher parameter:<br>Threshold: {threshold} - Cutoff: {cutoff} - Ngrams: {ngram} - Mindistance: {mindistance}<br>"
                f"Left text : True text | Right text : Matched text</p>"
            )
            html_file.write(f"<h2>Text du volume</h2></center>{content}")
            html_file.write("</body></html>")


def main():
    parser = argparse.ArgumentParser(
        description="Take two .bio file and create a HTML file with both text side by side and marking for iob tag"
    )
    parser.add_argument(
        "-f",
        "--first-file",
        help="First .bio file. (True file)",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "-s",
        "--second-file",
        help="Second .bio file. (Matched file with a name like 'line_params_date_id-volume.bio)",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "-m",
        "--metadata-heurist",
        help="Metadata csv file from the Heurist base",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "-v",
        "--volume-metadata",
        help="Metadata csv file from the Arkindex base ([id,name])",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "-r",
        "--reference",
        help="Folder containing the reference texts",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "-o",
        "--output-path",
        help="Path where the file will be generated",
        type=Path,
        required=True,
    )

    args = vars(parser.parse_args())
    Compare(
        args["first_file"],
        args["second_file"],
        args["metadata_heurist"],
        args["volume_metadata"],
        args["reference"],
        args["output_path"],
    )


if __name__ == "__main__":
    main()
