#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from collections import Counter
from pathlib import Path

import pandas as pd


class ReferenceTexts:
    def __init__(self, file):
        """Initialise the class and parse the csv file."""
        self.file = file
        self.count = 0
        self.mean = 0
        self.std = 0
        self.min = 0
        self.max = 0
        self.nb_different_words = 0

        # parse the file
        self.df = pd.read_csv(self.file)

        # extract useful reference texts for text_reuse
        self.df_text = self.df[["Text"]]

        # refraction of the text
        self.df_text = self.df_text.dropna()
        self.df_text = self.df_text.reset_index()

        def clean_text(text):
            """Remove html tags and convert to lowercase"""
            text = text.replace("</p>", " ")
            text = text.replace("<p>", " ")
            text = text.replace("<br/>", " ")
            text = text.replace("<br />", " ")
            text = text.replace("...", " ")
            text = text.replace(",", " ")
            return text.lower()

        # remove html tags and lower case
        self.df_text["clean_text"] = self.df_text["Text"].apply(clean_text)

    def get_statistics(self):
        """Return the stats"""
        self.df_text["text_length"] = self.df_text["clean_text"].str.split().str.len()
        stat_text = self.df_text["text_length"].describe()
        self.count, self.mean, self.std, self.min = stat_text[0:4]
        self.max = stat_text[7]

        # list words with their frequencies
        word_freq = Counter(" ".join(self.df_text["clean_text"].values).split())
        self.nb_different_words = len(word_freq)
        with open("word_frequencies.csv", "w", encoding="utf8") as word_file:
            word_file.write(
                f"Number of different words : " f"{self.nb_different_words}\n"
            )
            for (word, freq) in word_freq.most_common():
                word_file.write(f"{word}\t{freq}\n")
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
        description="Parse a heurist export and make stats",
    )
    parser.add_argument(
        "--file",
        help="path of the csv file",
        required=True,
        type=Path,
    )
    args = vars(parser.parse_args())

    f = ReferenceTexts(args["file"])
    f.get_statistics()


if __name__ == "__main__":
    main()