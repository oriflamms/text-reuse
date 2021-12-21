#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import csv
import glob
import itertools
import logging
import os.path
from datetime import datetime
from pathlib import Path, PurePosixPath

import pandas as pd
from text_matcher.matcher import Matcher, Text
from text_matcher.text_matcher import getFiles

ARKINDEX_VOLUME_URL = "https://arkindex.teklia.com/element/"
HEURIST_TEXT_URL = "https://heurist.huma-num.fr/heurist/hclient/framecontent/recordEdit.php?db=stutzmann_horae&recID="
DATE = datetime.today().strftime("%Y-%m-%d")


class CreatingHtml:
    def __init__(
        self,
        volume_path,
        references_path,
        metadata_path,
        output_path,
        normalize,
        threshold,
        cutoff,
        ngrams,
    ):
        self.volumes = volume_path
        self.reference = references_path
        self.metadata_heurist = metadata_path
        self.output_path = output_path
        self.normalize = normalize
        self.threshold = threshold
        self.cutoff = cutoff
        self.ngrams = ngrams

        logging.info(normalize)

    @staticmethod
    def normalize_txt(txt):
        txt = txt.replace("\xa0", " ")
        txt = txt.replace("j", "i")
        txt = txt.replace("J", "I")
        txt = "".join(txt)
        txt = txt.replace("v", "u")
        txt = txt.replace("V", "U")
        txt = txt.replace("ë", "e")
        txt = txt.replace("Ë", "E")
        txt = txt.replace("æ", "e")
        txt = txt.replace("Æ", "E")
        txt = txt.replace("œ", "e")
        txt = txt.replace("Œ", "E")
        return txt

    def getting_info(self, text1, text2, stops):
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

            # Put this in a dictionary, so we don't have to process a file twice.
            for filename in [filenameA, filenameB]:
                if filename not in prevTextObjs:
                    if self.normalize:
                        prevTextObjs[filename] = Text(
                            self.normalize_txt(texts[filename]), filename
                        )
                        logging.info("Normalization Done")
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
                threshold=self.threshold,
                cutoff=self.cutoff,
                ngramSize=self.ngrams,
                removeStopwords=stops,
            )
            myMatch.match()

            # Write to the log, but only if a match is found.
            if myMatch.numMatches > 0:
                list_object.append([pair[1], myMatch.locationsA, myMatch.locationsB])
        return list_object

    def new_interface(self, text, ref, df):
        # Prepare the list of match

        match = self.getting_info(text, ref, False)

        # Organizing match
        list_match = []
        for ref_match in reversed(match):
            name_ref = os.path.basename(ref_match[0]).replace(".txt", "")
            for i in range(len(ref_match[1])):
                list_match.append([ref_match[1][i], ref_match[2][i], name_ref])

        df_match = pd.DataFrame(
            data=list_match, columns=["pos_text", "pos_ref", "name_ref"]
        )

        # Order the match in function of their localization in the text
        match = sorted(match, key=lambda x: x[1])

        # Read the text of interest
        with open(text, "r") as file_text:
            text_raw = file_text.read()

        # Copy text for bio file
        bio_text = text_raw

        # Read the metadata
        with open(self.metadata_heurist, newline="") as meta_file:
            meta = list(csv.reader(meta_file, delimiter=","))

        # Create the name of the output file
        id_volume = os.path.basename(text).split("_")[-1].replace(".txt", "")
        output_name = "_".join([DATE, id_volume])

        # Get the Arkindex link
        volume_url = os.path.join(ARKINDEX_VOLUME_URL, id_volume)

        # Create assert value
        ass_match_count = len(match)
        count = 0
        list_save_name = []
        for index, row in df_match.sort_values(
            by="pos_text", ascending=False
        ).iterrows():
            # Initiate the text of reference
            text_ref = ""
            # Check if the text hasn't already been treated
            if row["name_ref"] not in list_save_name:
                # List the treated reference text
                list_save_name.append(row["name_ref"])

                # Get information from the metadata
                for data in meta:
                    if data[0] == row["name_ref"]:
                        raw_name = data[1]
                        heurist_name = f"<b>{data[1]}</b><br>"

                # Sort a dataframe containing the proper information on the reference text
                df_name = df_match[df_match["name_ref"] == row["name_ref"]]

                # Get the reference text
                with open(
                    os.path.join(ref, f"{row['name_ref']}.txt"), "r"
                ) as psalm_file:
                    text_ref = self.normalize_txt(psalm_file.read())

                # Add the proper tag to the reference text
                for index_name, row_name in df_name.sort_values(
                    by="pos_ref", ascending=False
                ).iterrows():
                    text_ref = (
                        text_ref[: row_name["pos_ref"][1]]
                        + "</mark>"
                        + text_ref[row_name["pos_ref"][1] :]
                    )
                    text_ref = (
                        text_ref[: row_name["pos_ref"][0]]
                        + "<mark>"
                        + text_ref[row_name["pos_ref"][0] :]
                    )

                # Adding the final tag
                text_ref = (
                    '<span class="marginnote">' + heurist_name + text_ref + "</span>"
                )

            # Adding the proper tagging
            text_raw = (
                text_raw[: row["pos_text"][1]]
                + "</mark>"
                + text_raw[row["pos_text"][1] :]
            )
            text_raw = (
                text_raw[: row["pos_text"][0]]
                + text_ref
                + "<mark>"
                + text_raw[row["pos_text"][0] :]
            )
            count += 1
            # Adding marks to the bio eval text
            # bio_text = bio_text[: row['pos_text'][0]] + '/' + bio_text
            bio_text = (
                bio_text[: row["pos_text"][1]] + "/" + bio_text[row["pos_text"][1] :]
            )
            count += 1
            bio_text = (
                bio_text[: row["pos_text"][0]]
                + f"{raw_name.split()[-1]}-"
                + bio_text[row["pos_text"][0] :]
            )

            # Adding it in the evaluation dataframe
            df.loc[id_volume, raw_name.split()[-1]] = 1

        # Create list of word with bio tag
        tag = "O"
        list_bio = []
        for word in bio_text.split():
            if "-" in word:
                tag = f"B-{word.split('-')[0]}"
                list_bio.append([word.split("-")[1], tag])
            elif "B" in tag:
                tag = tag.replace("B", "I")
                list_bio.append([word, tag])
            elif "/" in word:
                list_bio.append([word.replace("/", ""), tag])
                tag = "O"
            else:
                list_bio.append([word, tag])

        assert ass_match_count == len(list_save_name)
        assert len(df_match) == len(list_match)

        # Create the html
        with open(
            os.path.join(self.output_path, f"line_{output_name}.html"), "w"
        ) as html_file:
            html_file.write(
                '<html><head><meta charset="UTF-8"><link rel="stylesheet" href="style.css"><title>Text Matcher</title></head><body>'
            )
            html_file.write("<h1>Text matcher interface</h1>")
            html_file.write(
                f'<p><a href="{volume_url}">Lien du volume sur Arkindex</a></p>'
            )
            html_file.write(f"<p>Number of recognised texts : {str(len(match))}</p>")
            html_file.write(f"<p>Number of match : {str(len(list_match))}</p>")
            html_file.write(
                f"<p>Parameter of the matche:<br> threshold: {self.threshold}, cutoff: {self.cutoff}, ngrams: {self.ngrams}</p>"
            )
            html_file.write(f"<h2>Text du volume</h2><p>{text_raw}</p>")
            html_file.write("</body></html>")

        # Write bio file
        with open(
            os.path.join(self.output_path, f"line_{output_name}.bio"), "a"
        ) as file:
            for row in list_bio:
                file.write(f'{" ".join(row)}\n')

    def create_html(self):
        # Get the path of the text in the htmls
        texts = getFiles(self.volumes)

        # Creation of the column for the evaluation df
        df = pd.read_csv(self.metadata_heurist)
        columns = df["ID Annotation"].to_numpy()

        # Creation if the index for the evaluation df
        index = []
        for filename in texts:
            index.append(os.path.basename(filename).split("_")[-1].replace(".txt", ""))

        # Creation of the df
        df = pd.DataFrame(0, columns=columns, index=index)

        # Go through the volumes and apply text-matcher to them while creating html
        for filename in texts:
            self.new_interface(str(filename), str(self.reference), df)

        # Give proper name with h_tag to the column of the df
        new_column = []
        for i in df.columns:
            new_column.append(str(i).split()[-1])

        df = df.set_axis(new_column, axis="columns")

        # Export the dataframe with a csv format
        df.to_csv(os.path.join(self.output_path, "evaluation_df.csv"), index=True)

    def create_html_bio(self, folder):
        logging.info("Creating html file from bio")
        list_bio_file = []
        if os.path.isdir(folder):
            list_bio_file = glob.glob(folder + "/**/*.bio", recursive=True)
        elif os.path.isfile(folder):
            list_bio_file = folder

        if not list_bio_file:
            logging.info("no bio file found")

        for file in list_bio_file:
            self.save_html_bio(file)

    def save_html_bio(self, bio_file):
        # Read the file
        with open(bio_file, "r") as fd:
            data_raw = fd.readlines()

        # Fetch the id of the volume
        logging.info(os.path.basename(bio_file).split("_")[-1])
        volume = os.path.basename(bio_file).split("_")[-1]
        volume_id = volume.replace(".bio", "")

        # Normalize the data
        data_list = []
        word_list = []
        for row in data_raw:
            data_list.append(row.split())
            word_list.append(self.normalize_txt(row.split()[0]))

        # Creating the dataframe
        df_bio = pd.DataFrame(data=data_list, columns=["word", "h_tag"])

        # Get the index of the match
        list_index = []
        nb_func = 0

        for index, row in df_bio.iterrows():
            # Check the index for beginning plus add index for end in case it follow another tag I
            if row["h_tag"][0] == "B":
                if index != 0 and df_bio.loc[index - 1, "h_tag"][0] == "I":
                    list_index.append(
                        ["end", index, df_bio.loc[index - 1, "h_tag"].split("-")[1]]
                    )
                nb_func += 1
                list_index.append(["start", index, row["h_tag"].split("-")[1]])
            # Check the index for the end in case it follow à O:
            if (
                index != 0
                and row["h_tag"] == "O"
                and df_bio.loc[index - 1, "h_tag"][0] == "I"
            ):
                list_index.append(
                    ["end", index, df_bio.loc[index - 1, "h_tag"].split("-")[1]]
                )

        # Read the metadata
        with open(self.metadata_heurist, newline="") as meta_file:
            data = list(csv.reader(meta_file, delimiter=","))

        # Creation of the link for the html
        volume_url = os.path.join(ARKINDEX_VOLUME_URL, volume_id)

        # Add the html tag
        end_tag = "</mark>"
        start_tag = "<mark>"

        for row in reversed(list_index):
            if row[0] == "start":
                # word_list.insert(row[1], start_tag)
                for data_row in data:
                    if data_row[1].split()[-1] == row[2]:
                        word_list.insert(
                            row[1],
                            (
                                start_tag
                                + f'<span class="marginnote">{data_row[1]}</span>'
                            ),
                        )

            elif row[0] == "end":
                word_list.insert(row[1], end_tag)

        # Recreate the text
        text_volume = " ".join(str(row) for row in word_list)

        # Create the name of the output file
        output_name = "_".join([DATE, volume_id])

        with open(
            os.path.join(self.output_path, f"true_{output_name}.html"), "w"
        ) as html_file:
            html_file.write(
                '<html><head><meta charset="UTF-8"><link rel="stylesheet" href="style.css"><title>Text True</title></head><body>'
            )
            html_file.write("<h1>True file interface</h1>")
            html_file.write(
                f'<p><a href="{volume_url}">Lien du volume sur Arkindex</a></p>'
            )
            html_file.write(f"<p><br>Number of recognised texts : {nb_func}</p>")
            html_file.write(f"<h2>Text du volume</h2><p>{text_volume}</p>")
            html_file.write("</body></html>")


def main():
    parser = argparse.ArgumentParser(
        description="Take a text and a repertory of text and find correspondence + generate evaluation.csv + generate bio file for each volume",
    )
    parser.add_argument(
        "-v",
        "--input-volumes",
        required=True,
        type=Path,
        help="Path of the text of interest",
    )
    parser.add_argument(
        "-r",
        "--input-references",
        required=True,
        type=Path,
        help="Path of the folder of the text of reference",
    )
    parser.add_argument(
        "-m",
        "--metadata-heurist",
        type=Path,
        help="File with the metadata to indicate the name of the recognised text",
        required=True,
    )
    parser.add_argument(
        "-o",
        "--output-html",
        required=True,
        type=Path,
        help="Path where the html will be located, please be sure to put the css in the same htmls",
    )
    parser.add_argument(
        "-n",
        "--normalize",
        help="Turn j into i, v into u",
        required=False,
        action="store_true",
    )
    parser.add_argument(
        "-b",
        "--bio-file-true",
        help="Generate html for the ground truth volumes",
        type=Path,
        default=None,
        required=False,
    )
    parser.add_argument(
        "-t",
        "--threshold",
        required=False,
        default=3,
        type=int,
        help="Value of the threshold for the text matcher",
    )
    parser.add_argument(
        "-c",
        "--cutoff",
        required=False,
        default=5,
        type=int,
        help="Value of the cutoff for the text matcher",
    )
    parser.add_argument(
        "-g",
        "--ngrams",
        required=False,
        default=3,
        type=int,
        help="Value of the ngrams for the text matcher",
    )

    args = vars(parser.parse_args())
    creation = CreatingHtml(
        PurePosixPath(args["input_volumes"]).as_posix(),
        args["input_references"],
        str(args["metadata_heurist"]),
        PurePosixPath(args["output_html"]),
        args["normalize"],
        args["threshold"],
        args["cutoff"],
        args["ngrams"],
    )
    creation.create_html()

    if args["bio_file_true"]:
        creation.create_html_bio(str(args["bio_file_true"]))


if __name__ == "__main__":
    main()
