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
        return self.get_transcription_df_single_page(df)

    def get_transcription_double_page(self, page_id):
        """Get the transcription on a double page with the paragraph in order"""
        self.cursor.execute(
            f"select text, sel.polygon from transcription inner join (select id, polygon from element where id in (select child_id from element_path where parent_id='{page_id}')and type='paragraph' order by polygon) as sel on transcription.element_id=sel.id"
        )
        df = pd.DataFrame(self.cursor.fetchall(), columns=["text", "polygon"])
        # df.to_csv(os.path.join(self.output_path, f"aaa{page_id}.csv"))

        return self.get_transcription_double_page_df(df)

    @staticmethod
    def get_transcription_df_single_page(df):
        """Extract the transcription for single page"""
        transcription = ""
        for index, row in df.iterrows():
            transcription += row["text"] + " "
        transcription = [phrase[0].replace("\n", " ") for phrase in transcription]
        return "".join(transcription)

    @staticmethod
    def get_transcription_double_page_df(df):
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

    def check_type_page_from_book_id(self, book_id):
        """Check the type of the page to apply the right get_transcription algorithm"""
        self.cursor.execute(
            f"select class_name from classification where element_id = '{book_id}'"
        )
        return self.cursor.fetchall()[0][0]

    def save_book_as_csv(self, book_id):
        """Save the book (page id and transcription) in a csv"""
        logging.info(f"Saving {book_id}.csv")
        with open(
            os.path.join(self.output_path, f"{book_id}.csv"), "w"
        ) as save_book_csv:
            writer = csv.writer(save_book_csv)
            self.list_page_id = self.get_list_page(book_id)
            logging.info("looking for transcription")
            type_page = self.check_type_page_from_book_id(book_id)
            if type_page == "single_page":
                for page_id in tqdm(self.list_page_id):
                    page_id = page_id[0]
                    trans = self.get_transcription_from_pageid_with_paragraph(page_id)
                    writer.writerow([page_id, trans])
            elif type_page == "double_page":
                for page_id in tqdm(self.list_page_id):
                    page_id = page_id[0]
                    trans = self.get_transcription_double_page(page_id)
                    writer.writerow([page_id, trans])

    def save_all_books(self):
        """Save all the book (page id and transcription) in their respective csv named 'id_book'.csv"""
        self.list_book_id = self.get_list_book()
        for book_id in tqdm(self.list_book_id):
            self.save_book_as_csv(book_id[0])

    def save_some_book(self, nb_book):
        """Save as much books as the function takes
        You cannot choose the book you save"""
        self.cursor.execute(
            f"select * from element where type = 'volume' limit {str(nb_book)};"
        )
        list_book_id = self.cursor.fetchall()
        for book_id in list_book_id:
            self.save_book_as_csv(book_id[0])

    def save_all_book_as_txt(self):
        """Save all the book (page id and transcription) in their respective csv named 'id_book'.csv"""
        self.list_book_id = self.get_list_book()
        for book_id in tqdm(self.list_book_id):
            self.save_book_as_txt(book_id[0])

    def save_book_as_txt(self, book_id):
        """Save a book in a txt file"""
        with open(os.path.join(self.output_path, f"{book_id}.txt"), "w") as file:
            self.list_page_id = self.get_list_page(book_id)
            type_page = self.check_type_page_from_book_id(book_id)
            if type_page == "simple_page":
                for page_id in self.list_page_id:
                    trans = self.get_transcription_from_pageid_with_paragraph(
                        page_id[0]
                    )
                    file.write(trans)
            elif type_page == "double_page":
                for page_id in self.list_page_id:
                    trans = self.get_transcription_double_page(page_id[0])
                    file.write(trans)
                # logging.info(str(type_page))

    def get_all_text_segment_psalm(self, liturgical_function):
        """
        Return a csv with all correspondence between a volume and the text of the liturgical function that can be found
        inside
        """
        # Get the name of text segment with that are Psalm
        self.cursor.execute(
            f"select name from element where id in (select child_id from element_path where parent_id in (select child_id from element_path where parent_id in (select id from element where type='volume'))) and type = 'text_segment' and name like '%{liturgical_function}%' group by name;"
        )
        columns = []
        index = []
        # create an array with the good name for index and column
        for i in self.cursor.fetchall():
            columns.append(i[0])
        for i in self.get_list_book():
            index.append(i[0])

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
            os.path.join(self.output_path, "50mms_text_segment.csv"),
            index=True,
        )


def main():
    """Collect arguments and run."""
    parser = argparse.ArgumentParser(
        description="Take a sql file and return csv (default) or txt by file of the books",
    )
    parser.add_argument(
        "--file",
        help="path of the sqlite db",
        required=True,
        type=Path,
    )
    parser.add_argument(
        "--savefile",
        help="path where the files will be created",
        required=True,
        type=Path,
    )
    parser.add_argument(
        "--output-format",
        help="choose between an export in csv or in txt",
        required=True,
    )
    parser.add_argument(
        "--text-segment",
        required=False,
        help="Export a csv called 50mss_text_segment.csv with information of what volume contains what text segment (y/n)",
        default="n",
    )
    parser.add_argument(
        "--liturgical-function",
        help="specifies the liturgical function of the reference's text. Case sensitive",
        required=False,
        default="",
    )

    args = vars(parser.parse_args())

    with SqlToCsv(args["file"], args["savefile"]) as f:
        # Save the book in csv format in the folder specified
        if args["output_format"] == "csv":
            f.save_all_books()
        # Save the book in txt format in the folder specified
        elif args["output_format"] == "txt":
            f.save_all_book_as_txt()
        # Save the csv of correspondence between volumes and the text specified
        if args["text_segment"] == "y":
            f.get_all_text_segment_psalm(args["liturgical_function"])


if __name__ == "__main__":
    main()
