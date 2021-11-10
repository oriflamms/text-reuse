#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Importation of the library
import argparse
import csv
import sqlite3
from pathlib import Path


class SqlToCsv:
    def __init__(self, file):
        """Initialise the class"""
        self.db_name = file
        self.conn = None
        self.cursor = None
        self.list_book = []
        self.list_page = []
        self.transcription = []

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
        self.cursor.execute(
            """select id from element where type="volume" group by name;"""
        )
        self.list_book = self.cursor.fetchall()
        return self.list_book

    def get_list_page(self, book_id):
        """Get and return the list of all the page of a book"""
        self.cursor.execute(
            """select id from element where id in (select child_id from element_path where parent_id='"""
            + book_id
            + """')order by created;"""
        )
        self.list_page = self.cursor.fetchall()
        return self.list_page

    def get_transcription_from_pageid_with_paragraph(self, page_id):
        """Get and return the transcription found on a page"""
        self.cursor.execute(
            """select text from transcription where element_id in (select id from element where id in (select child_id from element_path where parent_id='"""
            + page_id
            + """') and type="paragraph" order by polygon)"""
        )
        self.transcription = self.cursor.fetchall()
        return self.transcription

    def save_book_as_csv(self, book_id):
        """Save the book (page id and transcription) in a csv"""
        name = book_id + ".csv"
        with open(name, "w") as file:
            writer = csv.writer(file)

            li = self.get_list_page(book_id)
            for i in li:
                page_id = i[0]
                trans = self.get_transcription_from_pageid_with_paragraph(i[0])
                writer.writerow([page_id, trans])

    def save_all_books(self):
        """Save all the book (page id and transcription) in their respective csv"""
        list_book = self.get_list_book()
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
