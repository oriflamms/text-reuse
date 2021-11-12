#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Importation of the library
import argparse
import csv
import logging
import sqlite3
from pathlib import Path


class SqlToCsv:
    def __init__(self, file):
        """Initialise the class"""
        self.db_name = file
        self.conn = None
        self.cursor = None
        self.list_book_id = []
        self.list_page = []
        self.transcription = []
        logging.basicConfig(format="[%(levelname)s] %(message)s", level=logging.DEBUG)

    def __enter__(self):
        """Create a connection to the database"""
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        return self

    def __exit__(self):
        """Exit the connection of the database"""
        self.conn.close()

    def get_list_book(self):
        """Get and return a list of all the books of the db"""
        logging.info("looking for books in the database")
        self.cursor.execute(
            """select id from element where type="volume" group by name;"""
        )
        self.list_book_id = self.cursor.fetchall()
        logging.info(f"{len(self.list_book_id)} books found")
        return self.list_book_id

    def get_list_page(self, book_id):
        """Get and return the list of all the page of a book"""
        logging.info(f"looking for pages in book {book_id}")
        self.cursor.execute(
            """select id from element where id in (select child_id from element_path where parent_id='"""
            + book_id
            + """')order by created;"""
        )
        self.list_page = self.cursor.fetchall()
        logging.info(f"{len(self.list_page)} pages found")
        return self.list_page

    def get_transcription_from_pageid_with_paragraph(self, page_id):
        logging.info(f"looking for transcription in page {page_id}")
        self.cursor.execute(
            """select text from transcription where element_id in (
            select id from element where id in (
            select child_id from element_path where parent_id='"""
            + page_id
            + """')
            and type="paragraph" order by polygon)"""
        )
        translation = self.cursor.fetchall()
        translation = [phrase[0].replace("\n", " ") for phrase in translation]
        logging.info(f"{len(translation)} transcriptions found")
        return " ".join(translation)

    def save_book_as_csv(self, book_id):
        """Save the book (page id and transcription) in a csv"""
        with open(f"{book_id}.csv", "w") as save_book_csv:
            writer = csv.writer(save_book_csv)
            self.list_page = self.get_list_page(book_id)
            for i in self.list_page:
                page_id = i[0]
                trans = self.get_transcription_from_pageid_with_paragraph(page_id)
                writer.writerow([page_id, trans])

    def save_all_books(self):
        """Save all the book (page id and transcription) in their respective csv named 'id_book'.csv"""
        self.list_book_id = self.get_list_book()
        for i in self.list_book_id:
            self.save_book_as_csv(i[0])

    def save_some_book(self, nb_book):
        self.cursor.execute(
            """select * from element where type = 'volume' limit """
            + str(nb_book)
            + """;"""
        )
        list_book = self.cursor.fetchall()
        for i in list_book:
            self.save_book_as_csv(i[0])


def main():
    """Collect arguments and run."""
    parser = argparse.ArgumentParser(
        description="Take a sql file and return csv file of the books",
    )
    parser.add_argument(
        "--file",
        help="path of the csv file",
        required=True,
        type=Path,
    )
    args = vars(parser.parse_args())

    f = SqlToCsv(args["file"])
    f.__enter__()
    f.save_all_books()
    f.__exit__()


if __name__ == "__main__":
    main()
