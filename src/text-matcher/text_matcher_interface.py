#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import csv
import itertools
import logging
import os.path
from pathlib import Path, PurePosixPath

import pandas as pd
from text_matcher.matcher import Matcher, Text
from text_matcher.text_matcher import getFiles

ARKINDEX_VOLUME_URL = "https://arkindex.teklia.com/element/"
HEURIST_TEXT_URL = "https://heurist.huma-num.fr/heurist/hclient/framecontent/recordEdit.php?db=stutzmann_horae&recID="


def normalize_txt(txt):
    txt = txt.replace("\xa0", " ")
    txt = txt.replace("j", "i")
    txt = "".join(txt)
    txt = txt.replace("u", "v")
    logging.info("normalization done")
    return txt


def getting_info(text1, text2, threshold, cutoff, ngrams, stops, normalize):
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
                if normalize:
                    prevTextObjs[filename] = Text(
                        normalize_txt(texts[filename]), filename
                    )
                else:
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



def interface(txt1, txt2, metadata_path, html_path, normalize):
    # Prepare the list of match
    match = getting_info(txt1, txt2, 3, 5, 3, False, normalize)
    # Ordering the list of match by order of apparition in the text
    match = sorted(match, key=lambda x: x[1])

    # Read the text of the volume
    with open(txt1, "r") as text_of_interest_file:
        text_volume = text_of_interest_file.read()
        if normalize:
            text_volume = normalize_txt(text_volume)

    # Read the metadata
    with open(metadata_path, newline="") as meta_file:
        data = list(csv.reader(meta_file, delimiter=","))

    # Fetch the id of the volume
    volume = os.path.basename(txt1)
    volume_id = volume.replace(".txt", "")

    # Creation of the link for the html
    volume_url = os.path.join(ARKINDEX_VOLUME_URL, volume_id)

    # Injecting the text of the volume with html marker
    for i in reversed(match):
        with open(f"{i[0]}", "r") as psalm_file:
            psalm_text = psalm_file.read()
            if normalize:
                psalm_text = normalize_txt(psalm_text)

        # Fetch psalm id from input folder to create heurist link
        psalm_id = os.path.basename(i[0])
        psalm_id = psalm_id.replace(".txt", "")

        for row in data:
            if row[0] == psalm_id:
                psalm_name = row[1]
                work_id = row[2]

        heurist_link = os.path.join(HEURIST_TEXT_URL, work_id)

        # Highlighting the matches and putting the link
        text_volume = (
            text_volume[: i[1][0][1]]
            + f'</mark></a><span class="marginnote"><b>{psalm_name}</b><br>{psalm_text[: i[2][0][0]]}<mark>{psalm_text[i[2][0][0]:i[2][0][1]]}</mark>{psalm_text[i[2][0][1]:]}</span>'
            + text_volume[i[1][0][1] :]
        )
        text_volume = (
            text_volume[: i[1][0][0]]
            + f'<a href="{heurist_link}"><mark>'
            + text_volume[i[1][0][0] :]
        )

        # Adding it in the evaluation dataframe
        df.loc[volume_id, psalm_name] = 1

    # Open and write in the html
    with open(html_path, "w") as html_file:
        html_file.write(
            '<html><head><meta charset="UTF-8"><link rel="stylesheet" href="style.css"><title>Text Matcher</title></head><body>'
        )
        html_file.write("<h1>Text matcher interface</h1>")
        html_file.write(
            f'<p><a href="{volume_url}">Lien du volume sur Arkindex</a></p>'
        )
        html_file.write(f"<p><br>Number of recognised texts : {str(len(match))}</p>")
        html_file.write(f"<h2>Text du volume</h2><p>{text_volume}</p>")
        html_file.write("</body></html>")


# A supprimé plus tard
def create_df(metadata, volume_folder, save_path):
    texts = getFiles(volume_folder)
    index = []
    for filename in texts:
        index.append(os.path.basename(filename).replace(".txt", ""))

    df = pd.read_csv(metadata)
    columns = df["ID Annotation"].to_numpy()

    df = pd.DataFrame(0, columns=columns, index=index)
    # logging.info(df)

    # CSV de test vouer à disparaitre
    df.to_csv(os.path.join(save_path, "pouet.csv"), index=True)
    return df


def create_html(volume_folder, reference_folder, metadata, save_path):
    # Get the path of the text in the folder
    texts = getFiles(volume_folder)

    # Creation of the column for the evaluation df
    df = pd.read_csv(metadata)
    columns = df["ID Annotation"].to_numpy()
    logging.info(columns)

    # Creation if the index for the evaluation df
    index = []
    for filename in texts:
        index.append(os.path.basename(filename).replace(".txt", ""))

    # Creation of the df
    df = pd.DataFrame(0, columns=columns, index=index)

    for filename in texts:
        volume_id = os.path.basename(filename)
        volume_html = volume_id.replace(".txt", ".html")
        volume_path = os.path.join(save_path, volume_html)
        interface(str(filename), str(reference_folder), metadata, volume_path, df)

    df.to_csv(os.path.join(save_path, "evaluation_df.csv"), index=True)


def main():
    parser = argparse.ArgumentParser(
        description="Take a text and a repertory of text and find correspondence",
    )
    parser.add_argument(
        "--input-txt",
        required=True,
        type=Path,
        help="Path of the text of interest",
    )
    parser.add_argument(
        "--input-folder",
        required=True,
        type=Path,
        help="Path of the folder of the text of reference",
    )
    parser.add_argument(
        "--metadata",
        help="File with the metadata to indicate the name of the recognised text",
        required=True,
        type=Path,
    )
    parser.add_argument("--output-html", required=True, type=Path)
    parser.add_argument(
        "--output-html",
        required=True,
        type=Path,
        help="Path where the html will be located, please be sure to put the css in the same folder",
    )
    parser.add_argument(
        "--normalize",
        help="Turn j into i, v into u",
        default="True",
        required=False,
        action="store_true",
    )

    args = vars(parser.parse_args())

    """
    interface(
        args["input_txt"],
        PurePosixPath(args["input_folder"]).as_posix(),
        args["metadata"],
        args["output_html"],
    )"""
    create_html(
        PurePosixPath(args["input_txt"]).as_posix(),
        PurePosixPath(args["input_folder"]),
        str(args["metadata"]),
        PurePosixPath(args["output_html"]),
    )

    # Normalize the text before application of the interface
    if args["normalize"].lower():
        interface(
            args["input_txt"],
            PurePosixPath(args["input_folder"]).as_posix(),
            args["metadata"],
            args["output_html"],
            True,
        )
        logging.info("normalization done")
    else:
        interface(
            args["input_txt"],
            PurePosixPath(args["input_folder"]).as_posix(),
            args["metadata"],
            args["output_html"],
            False,
        )


if __name__ == "__main__":
    main()
