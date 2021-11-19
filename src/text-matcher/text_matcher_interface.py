#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import csv
import itertools
import webbrowser
from pathlib import Path

from text_matcher.matcher import Matcher, Text
from text_matcher.text_matcher import getFiles


def getting_info(text1, text2, threshold, cutoff, ngrams, stops):
    texts1 = getFiles(text1)
    texts2 = getFiles(text2)

    pairs = list(itertools.product(texts1, texts2))

    texts = {}
    prevTextObjs = {}
    for filename in texts1 + texts2:
        with open(filename, errors="ignore") as f:
            text = f.read()
        if filename not in texts:
            texts[filename] = text

    list_object = []
    for index, pair in enumerate(pairs):
        filenameA, filenameB = pair[0], pair[1]

        # Put this in a dictionary so we don't have to process a file twice.
        for filename in [filenameA, filenameB]:
            if filename not in prevTextObjs:
                prevTextObjs[filename] = Text(texts[filename], filename)

        # Just more convenient naming.
        textObjA = prevTextObjs[filenameA]
        textObjB = prevTextObjs[filenameB]

        # Reset the table of previous text objects, so we don't overload memory.
        # This means we'll only remember the previous two texts.
        prevTextObjs = {filenameA: textObjA, filenameB: textObjB}

        # Do the matching.
        myMatch = Matcher(
            textObjA,
            textObjB,
            threshold=threshold,
            cutoff=cutoff,
            ngramSize=ngrams,
            removeStopwords=stops,
        )
        myMatch.match()

        # Write to the log, but only if a match is found.
        if myMatch.numMatches > 0:
            list_object.append([pair[1], myMatch.locationsA, myMatch.locationsB])
    return list_object


def interface(txt1, txt2, metadata_path, html_path):

    f = open(html_path, "w")
    text = getting_info(txt1, txt2, 3, 5, 3, False)
    text = sorted(text, key=lambda x: x[1])
    f.write(
        """
    <html>
    <head><link rel="stylesheet" href="style.css"></head>
    <body>
    <h1>Text matcher interface</h1>"""
    )
    file = open(txt1, "r")
    text_volume = file.read()
    with open(metadata_path, newline="") as meta_file:
        data = list(csv.reader(meta_file, delimiter=","))

    f.write(
        '<mark data-entity="match"><div class="tooltip">Hover over green text <span class="tooltiptext">You will '
        "see the reference text</span></div></mark>"
    )
    f.write(f"<br>Number of recognised texts : {str(len(text))}")
    for i in reversed(text):
        i[0] = i[0].split("/")
        psalm = i[0][-1].replace(".txt", "")

        for row in data:
            if row[0] == psalm:
                psalm_name = row[1]

        text_volume = (
            text_volume[: i[1][0][1]]
            + f'<span class="tooltiptext">{psalm_name}</span></div></mark>'
            + text_volume[i[1][0][1] :]
        )
        text_volume = (
            text_volume[: i[1][0][0]]
            + '<mark data-entity="match"><div class="tooltip">'
            + text_volume[i[1][0][0] :]
        )

    f.write(f"<h2>Text du volume</h2><br>{text_volume}")
    f.write(
        """
    </body>
    </html>
    """
    )

    # close the file
    f.close()

    webbrowser.open("./src/text-matcher/interface.html")


def main():
    parser = argparse.ArgumentParser(
        description="Take a text and a repertory of text and find correspondence",
    )
    parser.add_argument("--input-txt", required=True, type=Path)
    parser.add_argument("--input-folder", required=True, type=Path)
    parser.add_argument(
        "--metadata",
        help="File with the metadata to indicate the name of the recognised text",
        required=True,
        type=Path,
    )
    parser.add_argument("--input-html", required=True, type=Path)

    args = vars(parser.parse_args())

    # getting_info(str(args["input_txt"]), str(args["input_folder"]), 3, 5, 3, False)
    interface(
        str(args["input_txt"]),
        str(args["input_folder"]),
        str(args["metadata"]),
        str(args["input_html"]),
    )


if __name__ == "__main__":
    main()
