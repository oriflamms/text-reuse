#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
from collections import Counter
from pathlib import Path

import pandas as pd


def clean_text(text):
    """Remove html tags and convert to lowercase"""
    text = text.replace("</p>", " ")
    text = text.replace("<p>", " ")
    text = text.replace("<br/>", " ")
    text = text.replace("<br />", " ")
    text = text.replace("...", " ")
    text = text.replace(",", " ")
    return text.lower()


def make_stats(filename):
    """Parse the csv file and print stats."""
    # parse the file
    df = pd.read_csv(filename)

    # extract useful reference texts for text_reuse
    df_text = df[["Text"]]

    # refraction of the text
    df_text = df_text.dropna()
    df_text = df_text.reset_index()

    # remove html tags and lower case
    df_text["clean_text"] = df_text["Text"].apply(clean_text)

    df_text["text_length"] = df_text["clean_text"].str.split().str.len()
    stat_text = df_text["text_length"].describe()
    print(stat_text)

    # list words with their frequencies
    word_freq = Counter(" ".join(df_text["clean_text"].values).split())
    print(f"Number of different word : {len(word_freq)}")

    with open("word_frequencies.csv", "w") as word_file:
        for (word, freq) in word_freq.most_common():
            word_file.write(f"{word}\t{freq}\n")


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
    make_stats(args["file"])


if __name__ == "__main__":
    main()
