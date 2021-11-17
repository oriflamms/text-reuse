#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Importation of the library
import argparse
import csv
import logging
import sqlite3
from pathlib import Path

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
            f"select id from element where id in (select child_id from element_path where parent_id='{book_id}')order by created;"
        )
        self.list_page_id = self.cursor.fetchall()
        logging.info(f"{len(self.list_page_id)} pages found")
        return self.list_page_id

    def get_transcription_from_pageid_with_paragraph(self, page_id):
        self.cursor.execute(
            f"select text from transcription where element_id in (select id from element where id in (select child_id from element_path where parent_id='{page_id}')and type='paragraph' order by polygon)"
        )
        transcription = self.cursor.fetchall()
        transcription = [phrase[0].replace("\n", " ") for phrase in transcription]
        return " ".join(transcription)

    def save_book_as_csv(self, book_id):
        """Save the book (page id and transcription) in a csv"""
        logging.info(f"Saving {book_id}.csv")
        with open(f"{self.output_path}/{book_id}.csv", "w") as save_book_csv:
            writer = csv.writer(save_book_csv)
            self.list_page_id = self.get_list_page(book_id)
            logging.info("looking for transcription")
            for page_id in tqdm(self.list_page_id):
                page_id = page_id[0]
                trans = self.get_transcription_from_pageid_with_paragraph(page_id)
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
        with open(f"{self.output_path}/{book_id}.txt", "w") as file:
            self.list_page_id = self.get_list_page(book_id)
            for page_id in self.list_page_id:
                trans = self.get_transcription_from_pageid_with_paragraph(page_id[0])
                file.write(trans)


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

    args = vars(parser.parse_args())

    with SqlToCsv(args["file"], args["savefile"]) as f:
        if args["output_format"] == "csv":
            f.save_all_books()
        elif args["output_format"] == "txt":
            f.save_all_book_as_txt()


if __name__ == "__main__":
    main()
