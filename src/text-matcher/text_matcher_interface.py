#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
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

    listpouet = []
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
            listpouet.append([pair[1], myMatch.locationsA, myMatch.locationsB])
    return listpouet


def interface(txt1, txt2):

    f = open("./src/text-matcher/interface.html", "w")
    text = getting_info(txt1, txt2, 3, 5, 3, False)

    f.write(
        """
    <html>
    <head><link rel="stylesheet" href="style.css"></head>
    <body>
    <h1>Text matcher interface</h1>"""
    )

    for i in text:
        i[0] = i[0].split("/")
        psalm = i[0][-1].replace(".txt", "")

        f.write(
            f'<p><mark data-entity="psalm id">{psalm}</mark><br> '
            f'<mark data-entity="position : book of hours">between {i[1][0][0]} and {i[1][0][1]}</mark>'
            f'<mark data-entity="position : psalm">between {i[2][0][0]} and {i[2][0][1]}</mark><br><br>'
        )

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

    args = vars(parser.parse_args())

    # getting_info(str(args["input_txt"]), str(args["input_folder"]), 3, 5, 3, False)
    interface(str(args["input_txt"]), str(args["input_folder"]))


if __name__ == "__main__":
    main()
