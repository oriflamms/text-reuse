#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Importation of the library
import argparse
import ast
import csv
import logging
import os.path
import sqlite3
from pathlib import Path

import pandas as pd
from shapely.geometry import Polygon
from tqdm import tqdm


class SqlToCsv:
    def __init__(self, file, output_path):
        """Initialise the class"""
        self.db_name = file
        self.output_path = output_path
        self.conn = None
        self.cursor = None
        self.list_book_id = []
        self.list_page_id = []
        self.transcription = []
        self.type_page = ""
        logging.basicConfig(format="[%(levelname)s] %(message)s", level=logging.DEBUG)

    def __enter__(self):
        """Create a connection to the database"""
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        return self

    def __exit__(self, *args, **kwargs):
        """Exit the connection of the database"""
        self.conn.close()

    def get_list_book(self):
        """Get and return a list of all the books of the db"""
        logging.info("looking for books in the database")
        self.cursor.execute('select id from element where type="volume";')
        self.list_book_id = self.cursor.fetchall()
        logging.info(f"{len(self.list_book_id)} books found")
        return self.list_book_id

    def get_list_page(self, book_id):
        """Get and return the list of all the page of a book"""
        logging.info(f"looking for pages in book {book_id}")
        self.cursor.execute(
            f"select child_id, ordering from element_path where parent_id = '{book_id}' order by ordering;"
        )
        self.list_page_id = self.cursor.fetchall()
        logging.info(f"{len(self.list_page_id)} pages found")
        return self.list_page_id

    def get_transcription_from_pageid_with_paragraph(self, page_id):
        """Get and return the transcription for simple page"""
        self.cursor.execute(
            f"select text from transcription where element_id in (select id from element where id in ("
            f"select child_id from element_path where parent_id='{page_id}')and type='paragraph' order by polygon)"
        )
        df = pd.DataFrame(self.cursor.fetchall(), columns=["text"])
        return self.get_transcription_df_single_page_para(df)

    def get_transcription_double_page(self, page_id):
        """Get the transcription on a double page with the paragraph in order"""
        self.cursor.execute(
            f"select text, sel.polygon from transcription inner join (select id, polygon from element where id in (select child_id from element_path where parent_id='{page_id}')and type='paragraph' order by polygon) as sel on transcription.element_id=sel.id"
        )
        df = pd.DataFrame(self.cursor.fetchall(), columns=["text", "polygon"])

        return self.get_transcription_double_page_df_para(df)

    @staticmethod
    def get_transcription_df_single_page_para(df):
        """Extract the transcription for single page"""
        transcription = ""
        for index, row in df.iterrows():
            transcription += row["text"] + " "
        transcription = [phrase[0].replace("\n", " ") for phrase in transcription]
        return "".join(transcription)

    @staticmethod
    def get_transcription_double_page_df_para(df):
        """Extract the transcription for double page"""
        df["polygon"] = df.polygon.apply(lambda x: Polygon(ast.literal_eval(str(x))))
        df["x_axis"] = df.polygon.apply(lambda a: a.centroid.x)  # order on which page
        df["y_axis"] = df.polygon.apply(
            lambda a: a.centroid.y
        )  # order where on the page
        transcription = ""

        # Check if the dataframe is empty else return empty string
        if len(df.index) != 0:
            # Create a limit between the pages
            df = df.sort_values(by=["y_axis"])
            stat = df["x_axis"].describe()
            x_limit = (stat[4] + stat[7]) / 2

            # Get the transcription
            for i in [0, 1]:
                for index, row in df.iterrows():
                    if i == 0 and row["x_axis"] < x_limit:
                        transcription += row["text"] + " "
                    if i == 1 and row["x_axis"] > x_limit:
                        transcription += row["text"] + " "
            transcription = [phrase[0].replace("\n", " ") for phrase in transcription]
        return "".join(transcription)

    def check_type_page_from_book_id_complete(self, book_id):
        """Check the type of the page to apply the right get_transcription algorithm for the complete corpus"""
        self.cursor.execute(
            f"select value from metadata where name = 'Digitization Type' and element_id = '{book_id}'"
        )
        self.type_page = self.cursor.fetchall()[0][0]

    def save_book_complete_para(self, book_id):
        """Save book from complete corpus"""
        list_word_id_page = []
        with open(os.path.join(self.output_path, f"para_{book_id}.txt"), "w") as file:
            self.list_page_id = self.get_list_page(book_id)
            self.check_type_page_from_book_id_complete(book_id)

            # Extraction for single paged book
            if self.type_page == "single page":
                for page_id in self.list_page_id:
                    trans = self.get_transcription_from_pageid_with_paragraph(
                        page_id[0]
                    )
                    file.write(trans)
                    if trans:
                        for word in trans.split():
                            list_word_id_page.append([word, page_id[0]])

            # Extraction for double paged book
            elif self.type_page == "double page":
                for page_id in self.list_page_id:
                    trans = self.get_transcription_from_pageid_with_paragraph(
                        page_id[0]
                    )
                    file.write(trans)
                    if trans:
                        for word in trans.split():
                            list_word_id_page.append([word, page_id[0]])

            else:
                logging.info("The Digitization type is not regular")

            with open(
                os.path.join(self.output_path, f"idpage_{book_id}.txt"), "w", newline=""
            ) as f:
                writer = csv.writer(f)
                writer.writerows(list_word_id_page)

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

    def save_bio_and_line(self, book_id, lit_function):
        """Save bio file for the 10 fully annotated volume and export also the text with a line fetching"""
        # Get pages
        self.get_list_page(book_id)

        # Create dataframe for the whole volume
        df_volume = pd.DataFrame(columns=["id", "function", "page"])

        # Add h_tag at each page that has text_segment
        for page in self.list_page_id:
            id_page = page[0]
            nb_page = page[1] + 1

            # Create dataframe for the text_line in the page
            self.cursor.execute(
                f"select id, polygon from element where id in (select child_id from element_path where parent_id='{id_page}') and type='text_line'"
            )
            df_text_lines = pd.DataFrame(
                data=self.cursor.fetchall(), columns=["id", "polygon"]
            )

            # Turn polygon into shape
            df_text_lines["polygon"] = df_text_lines.polygon.apply(
                lambda x: Polygon(ast.literal_eval(str(x)))
            )

            # Order the text_line with y coordinate of the center of polygon
            df_text_lines["y_axis"] = df_text_lines.polygon.apply(
                lambda a: a.centroid.y
            )
            df_text_lines = df_text_lines.sort_values(by=["y_axis"])
            df_text_lines = df_text_lines.reset_index(drop=True)

            # Add column for liturgical function
            df_text_lines["function"] = ""

            # Find text_segment in the page
            self.cursor.execute(
                f"select name, polygon from element where id in (select child_id from element_path where parent_id='{id_page}') and type='text_segment'"
            )

            # Create dataframe for text_segment
            df_text_segment = pd.DataFrame(
                data=self.cursor.fetchall(), columns=["name", "polygon"]
            )

            # Check if there is text_segment
            if not df_text_segment.empty:
                # Turn polygon into shape
                df_text_segment["polygon"] = df_text_segment.polygon.apply(
                    lambda x: Polygon(ast.literal_eval(str(x)))
                )

                # Order text_segment
                df_text_segment["y_axis"] = df_text_segment.polygon.apply(
                    lambda a: a.centroid.y
                )
                df_text_segment = df_text_segment.sort_values(by=["y_axis"])
                df_text_segment = df_text_segment.reset_index(drop=True)

                for index_segment, row_segment in df_text_segment.iterrows():
                    for index_line, row_line in df_text_lines.iterrows():
                        if row_line["polygon"].intersects(row_segment["polygon"]):
                            df_text_lines.loc[index_line, "function"] = row_segment[
                                "name"
                            ].split()[-1]

            # Add the number of the page to the dataframe
            df_text_lines["page"] = nb_page
            # Add to the dataframe of the volume
            df_volume = pd.concat(
                [df_volume, df_text_lines[["id", "function", "page"]]],
                ignore_index=True,
            )

        # Initialize the dataframe if it doesn't begin with a function
        if df_volume.loc[0, "function"] == "":
            df_volume.loc[0, "function"] = "none"

        # Complete the empty row with missing value
        for index_volume, row_volume in df_volume.iterrows():
            if index_volume != 0 and row_volume["function"] == "":
                df_volume.loc[index_volume, "function"] = df_volume.loc[
                    index_volume - 1, "function"
                ]

        # Remove the liturgical function that are not asked
        if lit_function:
            logging.info(lit_function)

            # Find the liturgical function that are accepted
            self.cursor.execute(
                f"select name from element where id in (select child_id from element_path where parent_id in (select child_id from element_path where parent_id = '{book_id}')) and type = 'text_segment' and name like '%{lit_function}%'"
            )
            df_function = pd.DataFrame(data=self.cursor.fetchall(), columns=["name"])

            # Get the h_tag
            df_function["h_tag"] = ""
            for index, row in df_function.iterrows():
                row["h_tag"] = row["name"].split()[-1]

            # Get a list of the h_tag
            np_h_tag = df_function["h_tag"].to_numpy()

            # Suppress the function not wanted
            for index, row in df_volume.iterrows():
                if row["function"] not in np_h_tag:
                    row["function"] = "none"
        else:
            logging.info("No liturgical function")

        # Add a column for the text
        df_volume["text"] = ""

        # Get transcription
        for index, row in df_volume.iterrows():
            self.cursor.execute(
                f"""select text from transcription where element_id = '{row["id"]}';"""
            )
            text = self.cursor.fetchall()
            if text:
                row["text"] = text[0][0]

        # Create bio tag
        bio_data = []
        function = ""
        bio_tag = ""
        for index, row in df_volume.iterrows():
            if row["text"]:
                for word in row["text"].split():
                    if row["function"] == "none":
                        bio_tag = "O"
                    elif row["function"] == function and function != "none":
                        bio_tag = f'I-{row["function"]}'
                    elif row["function"] != function:
                        bio_tag = f'B-{row["function"]}'
                    # bio_data.append([word, bio_tag, row["page"]])
                    bio_data.append([word, bio_tag])
                    function = row["function"]

        # Export bio file
        with open(os.path.join(self.output_path, f"true_{book_id}.bio"), "a") as file:
            for row in bio_data:
                file.write(
                    f'{" ".join(self.normalize_txt(str(word)) for word in row)}\n'
                )

        # Export line file
        with open(os.path.join(self.output_path, f"line_{book_id}.txt"), "a") as file:
            for row in bio_data:
                file.write(f"{self.normalize_txt(row[0])} ")

    def save_fully_annotated_books(self, lit_function, empty_line):
        list_book = [
            "d1dd24a0-ca6a-4513-b86d-1d9547717c21",
            "beb498f0-3ae1-44f6-837d-94ec92eb0953",
            "23071571-8dd6-4d88-8c42-82a03fe5b4d5",
            "a1353358-dcb4-4968-977f-6cda8e65a3a4",
            "2cf86092-20b7-4455-b90e-6deb9c8ce777",
            "5c1d9d2b-7623-4168-8853-f4858d4ba39d",
            "eecf5f36-b31b-4f90-b9ac-d2f263acc9ea",
            "29f43007-92c8-4927-b048-fa75899b31e7",
            "68d4ffae-a5e5-4069-a751-48b543d72c37",
            "a8a73f3a-beae-4c5e-be09-7d038649e8b1",
        ]
        for book in tqdm(list_book):
            self.save_bio_and_line(book, lit_function)
            if empty_line:
                self.collect_empty_transcription(book)

        self.get_text_segment_complete(lit_function, list_book)

    def get_text_segment_complete(self, liturgical_function, list_id_corpus):
        # Get the name of text segment with that are Psalm
        self.cursor.execute(
            "select name from element where id in (select child_id from element_path where parent_id in (select child_id from element_path where parent_id in ('d1dd24a0-ca6a-4513-b86d-1d9547717c21','beb498f0-3ae1-44f6-837d-94ec92eb0953','23071571-8dd6-4d88-8c42-82a03fe5b4d5','a1353358-dcb4-4968-977f-6cda8e65a3a4','2cf86092-20b7-4455-b90e-6deb9c8ce777','5c1d9d2b-7623-4168-8853-f4858d4ba39d','eecf5f36-b31b-4f90-b9ac-d2f263acc9ea','29f43007-92c8-4927-b048-fa75899b31e7','68d4ffae-a5e5-4069-a751-48b543d72c37','a8a73f3a-beae-4c5e-be09-7d038649e8b1'))) and type = 'text_segment' and name like '%Psalm%' group by name;"
        )
        columns = []
        index = []

        # create an array with the good name for index and column
        for i in self.cursor.fetchall():
            columns.append(i[0])
        for i in list_id_corpus:
            index.append(i)

        # Creation of the dataframe filled with 0 and with the id of volume as row and the name of text segment as column
        df = pd.DataFrame(0, columns=columns, index=index)

        # Put a 1 in the dataframe if the volume contain the text segment
        for index, row in df.iterrows():
            # Find text segment for each volume
            self.cursor.execute(
                f"select name from element where id in (select child_id from element_path where parent_id in (select child_id from element_path where parent_id = '{index}')) and type = 'text_segment' and name like '%{liturgical_function}%';"
            )
            for i in self.cursor.fetchall():
                if i[0] in df.columns:
                    row[i[0]] = 1

        new_column = []
        for i in df.columns:
            new_column.append(str(i).split()[-1])
            # print(str(i).split()[-1])

        df = df.set_axis(new_column, axis="columns")

        # Extract the dataframe as a csv
        df.to_csv(
            os.path.join(self.output_path, "complete_text_segment.csv"),
            index=True,
        )

    def get_meta_vol(self):
        """Generate the metadata for a corpus (complete)"""
        self.cursor.execute("select id, name from element where type = 'volume'")
        df_vol = pd.DataFrame.from_records(
            data=self.cursor.fetchall(), columns=["id", "name"]
        )
        df_vol.to_csv(
            os.path.join(self.output_path, "metadata_volume.csv"),
            index=False,
        )

    def collect_empty_transcription(self, id_book):
        """Collect the empty transcription text_line from a book"""
        logging.info(f"Checking text_line for volume {id_book}")
        self.get_list_page(id_book)

        empty_transcription = [["id_page", "num_page", "id_text_line"]]

        # Check for all the page of the volume
        for id_page in self.list_page_id:
            # Find ids of text_line from a page
            self.cursor.execute(
                f"select id from element where id in (select child_id from element_path where parent_id = '{id_page[0]}') and type='text_line'"
            )

            # Check if the text_line is empty for all text_line
            for id_text_line in self.cursor.fetchall():
                # Get the transcription from a text_line id
                self.cursor.execute(
                    f"select text from transcription where element_id='{id_text_line[0]}'"
                )
                if not self.cursor.fetchall():
                    empty_transcription.append(
                        [id_page[0], id_page[1], id_text_line[0]]
                    )

        with open(
            os.path.join(self.output_path, f"empty-transcription_{id_book}.csv"),
            "w",
            newline="",
        ) as f:
            writer = csv.writer(f)
            writer.writerows(empty_transcription)

    def managing_function(
        self, text_segment, metadata_volume, liturgical_function, empty_line
    ):
        self.get_list_book()

        list_id_book = []
        for id_book in tqdm(self.list_book_id):
            print(id_book[0])
            list_id_book.append(id_book[0])
            self.save_book_complete_para(id_book[0])

            if empty_line:
                self.collect_empty_transcription(id_book[0])

        if text_segment:
            self.get_text_segment_complete(liturgical_function, list_id_book)

        if metadata_volume:
            self.get_meta_vol()


def main():
    """Collect arguments and run."""
    parser = argparse.ArgumentParser(
        description="Take a sql file and return csv (default) or txt by file of the books"
        "For the fully annotated book from the complete base you can specify -a and also a liturgical function with -l",
    )
    parser.add_argument(
        "-s",
        "--sql-file",
        help="path of the sqlite db",
        required=True,
        type=Path,
    )
    parser.add_argument(
        "-o",
        "--output-path",
        help="path where the files will be created",
        required=True,
        type=Path,
    )
    parser.add_argument(
        "-a",
        "--fully-annotated",
        help="Extraction of only annotated volume, if not precised extraction on all the database",
        required=False,
        action="store_true",
    )
    parser.add_argument(
        "-t",
        "--text-segment",
        required=False,
        action="store_true",
        help="Export a csv called 50mss_text_segment.csv with information of what volume contains what text segment (y/n)",
    )
    parser.add_argument(
        "-m",
        "--metadata-volume",
        required=False,
        action="store_true",
        help="Generate a metadata file with id of volume and name",
    )
    parser.add_argument(
        "-l",
        "--liturgical-function",
        help="specifies the liturgical function of the reference's text. Case sensitive",
        required=False,
        default="",
    )
    parser.add_argument(
        "-e",
        "--empty-line",
        help="Collect the text_line without transcription for the fully annotated book",
        required=False,
        action="store_true",
    )

    args = vars(parser.parse_args())

    with SqlToCsv(args["sql_file"], args["output_path"]) as f:

        # f.save_book_complete_para('6d6e6acd-393b-4f66-bdd5-4d9f06ad5c24')

        # Get books fully annotated
        if args["fully_annotated"]:
            logging.info("Extraction for fully annotated book")
            f.save_fully_annotated_books(
                args["liturgical_function"], args["empty_line"]
            )

        else:
            f.managing_function(
                args["text_segment"],
                args["metadata_volume"],
                args["liturgical_function"],
                args["empty_line"],
            )


if __name__ == "__main__":
    main()
