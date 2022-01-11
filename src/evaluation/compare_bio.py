#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import csv
import os
from pathlib import Path

import pandas as pd


class Compare:
    def __init__(self, first_text, second_text, metadata, output_path):
        self.first_text = self.read_bio(first_text, metadata)
        self.second_text = self.read_bio(second_text, metadata)
        self.output_path = output_path

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
            if row["bio_tag"][0] == "B":
                if index != 0 and df_bio.loc[index - 1, "bio_tag"][0] == "I":
                    list_index.append(
                        ["end", index, df_bio.loc[index - 1, "bio_tag"].split("-")[1]]
                    )
                nb_func += 1
                list_index.append(["start", index, row["bio_tag"].split("-")[1]])
            if (
                index != 0
                and row["bio_tag"] == "O"
                and df_bio.loc[index - 1, "bio_tag"][0] == "I"
            ):
                list_index.append(
                    ["end", index, df_bio.loc[index - 1, "bio_tag"].split("-")[1]]
                )

        with open(metadata, newline="") as meta_file:
            data = list(csv.reader(meta_file, delimiter=","))

        end_tag = "</hov></marka>"
        start_tag = "<marka>"
        for row in reversed(list_index):
            if row[0] == "start":
                for data_row in data:
                    if data_row[1].split()[-1] == row[2]:
                        word_list.insert(
                            row[1], (start_tag + f'<hov title="{data_row[1]}">')
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
        content = f' <div class="row"><div class="column">{self.first_text}</div><div class="column">{self.second_text}</div></div> '

        with open(os.path.join(self.output_path, "test.html"), "w") as html_file:
            html_file.write(
                '<html><head><meta charset="UTF-8"><link rel="stylesheet" href="com_style.css"><title>Align text</title></head><body>'
            )
            html_file.write("<h1>Content</h1>")
            html_file.write(
                "<p><marka><hov title='Just like that'>Hover on the highlighted text to see the referenced text</hov></marka><p>"
            )
            html_file.write(f"<h2>Text du volume</h2>{content}")
            html_file.write("</body></html>")


def main():
    parser = argparse.ArgumentParser(
        description="Take two .bio file and create a HTML file with both text side by side and marking for iob tag"
    )
    parser.add_argument(
        "-f",
        "--first-file",
        help="First .bio file",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "-s",
        "--second-file",
        help="Second .bio file",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "-m",
        "--metadata",
        help="Metadata csv file from the Heurist base",
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
        args["first_file"], args["second_file"], args["metadata"], args["output_path"]
    ).align_text()
    print(f'The file has been generated at {args["output_path"]}')


if __name__ == "__main__":
    main()
