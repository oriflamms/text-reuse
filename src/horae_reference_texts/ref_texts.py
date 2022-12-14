#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import csv
import logging
import os.path
import re
from collections import Counter
from pathlib import Path

import pandas as pd

pd.options.mode.chained_assignment = None  # default='warn'

EXPORT_METADATA_NB = "metadata_nb_name.csv"


class ReferenceTexts:
    def __init__(self, file, liturgical_function):
        """Initialise the class and parse the csv file."""
        self.file = file
        self.count = 0
        self.mean = 0
        self.std = 0
        self.min = 0
        self.max = 0
        self.nb_different_words = 0
        self.liturgical_function = liturgical_function
        logging.basicConfig(format="[%(levelname)s] %(message)s", level=logging.DEBUG)

        # parse the file
        self.df = pd.read_csv(self.file)

        def clean_text(text):
            """Remove html tags and convert to lowercase"""
            text = re.sub(r"[^\w\s]", "", text)
            text = text.replace("<p>", " ")
            text = text.replace("</p>", " ")
            text = text.replace("<br>", " ")
            text = text.replace("<br />", " ")
            text = text.replace("<br/>", " ")
            text = text.replace("<sup>", " ")
            text = text.replace("</sup>", " ")
            text = text.replace("…", " ")
            text = text.replace("(...)", " ")
            return text.lower()

        # extract useful reference texts for text_reuse
        if self.liturgical_function:
            # create the dataframe for the application of write_in_text
            self.df_text = self.df[
                self.df["Liturgical function"] == self.liturgical_function
            ]
            self.df_text = self.df_text[["Text", "ID Arkindex"]]
        else:
            # create the standard dataframe
            self.df_text = self.df[["Text", "ID Arkindex"]]

        # refraction of the text
        self.df_text = self.df_text.dropna()
        self.df_text = self.df_text.reset_index()

        # remove html tags and lower case
        self.df_text["clean_text"] = self.df_text["Text"].apply(clean_text)

    def write_in_txt(self, output_path):
        """Write in txt file the clean text for each psalm's text in a htmls"""
        for index, row in self.df_text.iterrows():
            with open(
                os.path.join(output_path, f'{row["ID Arkindex"]}.txt'),
                "w",
                encoding="utf8",
            ) as f:
                f.write(row["clean_text"])

    def write_metadata(self, metadata_path):
        df_meta = self.df[self.df["Liturgical function"] == self.liturgical_function]
        df_meta[["ID Arkindex", "ID Annotation", "Work H-ID"]].to_csv(
            os.path.join(metadata_path, "metadata_heurist.csv"), index=False
        )

    def write_nb_of_word_metadata(self, metadata_path, export_name):
        name_nb_list = [
            [r["ID Annotation"].split()[-1], len(str(r["Text"]).split())]
            for i, r in self.df.iterrows()
        ]
        with open(os.path.join(metadata_path, export_name), "w") as nb_file:
            writer = csv.writer(nb_file)
            writer.writerows(name_nb_list)

    def get_statistics(self):
        """Return the stats and create files on frequencies"""
        self.df_text["text_length"] = self.df_text["clean_text"].str.split().str.len()
        stat_text = self.df_text["text_length"].describe()
        self.count, self.mean, self.std, self.min = stat_text[0:4]
        logging.info(f"count of words :{self.count}")
        logging.info(f"mean : {self.mean}")
        logging.info(f"min : {self.min}")
        logging.info(f"standard deviation : {self.std}")
        self.max = stat_text[7]
        logging.info(f"max : {self.max}")
        # list words with their frequencies
        word_freq = Counter(
            " ".join(self.df_text["clean_text"].values).split()
        ).most_common()
        self.nb_different_words = len(word_freq)
        logging.info(f"nb of different words : {self.nb_different_words}")

        # Write the frequencies of word in a csv
        with open(
            "word_frequencies.csv", "w", encoding="utf8", newline=""
        ) as word_file:
            writer = csv.writer(word_file, delimiter="\t")
            word_file.write(
                "Number of different word : " + str(self.nb_different_words) + "\n\n"
            )
            writer.writerows(word_freq)

        freq_char = Counter(" ".join(self.df_text["clean_text"].values)).most_common()
        nb_different_chars = len(freq_char)

        # Write the frequencies of characters in a csv
        with open(
            "character_frequencies.csv", "w", encoding="utf8", newline=""
        ) as char_file:
            writer = csv.writer(char_file, delimiter="\t")
            char_file.write(
                "Number of different character : " + str(nb_different_chars) + "\n\n"
            )
            writer.writerows(freq_char)

        freq_text = Counter(self.df_text["clean_text"].values).most_common()
        nb_different_text = len(freq_text)

        # Write the frequencies of texts in a csv
        with open(
            "text_frequencies.csv", "w", encoding="utf8", newline=""
        ) as text_file:
            writer = csv.writer(text_file, delimiter="\t")
            text_file.write(
                "Number of different text : " + str(nb_different_text) + "\n\n"
            )
            writer.writerows(freq_text)

        return (
            self.count,
            self.mean,
            self.std,
            self.min,
            self.max,
            self.nb_different_words,
        )


def main():
    """Collect arguments and run."""
    parser = argparse.ArgumentParser(
        description="Parse a heurist export and make stats, you can also specify a liturgical function ",
    )
    parser.add_argument(
        "-f",
        "--file-heurist",
        help="path of the csv heurist file",
        required=True,
        type=Path,
    )
    parser.add_argument(
        "-o",
        "--output-path",
        help="path of the output files for the ref text named after their ID Arkindex",
        required=False,
        default=False,
        type=Path,
    )
    parser.add_argument(
        "-l",
        "--liturgical-function",
        help="specifies the liturgical function of the reference's text. Case sensitive",
        required=False,
        default="",
    )
    parser.add_argument(
        "-m",
        "--metadata-path",
        help="path of the output file for metadata",
        required=False,
        default="",
        type=Path,
    )
    parser.add_argument(
        "-n",
        "--nb-word",
        help="path of the output file nb_word file where there is the number of word and the h_tag",
        required=False,
        default="",
        type=Path,
    )

    args = vars(parser.parse_args())

    f = ReferenceTexts(args["file_heurist"], args["liturgical_function"])
    f.get_statistics()

    if args["output_path"] and args["liturgical_function"] != []:
        f.write_in_txt(args["output_path"])

    if args["metadata_path"] and args["liturgical_function"]:
        f.write_metadata(args["metadata_path"])

    if args["nb_word"] and args["liturgical_function"]:
        f.write_nb_of_word_metadata(args["nb_word"], EXPORT_METADATA_NB)


if __name__ == "__main__":
    main()
