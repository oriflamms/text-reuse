#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Importation of the library
import csv
import sqlite3

# Connects to the sqlite database
conn = sqlite3.connect("horae-complete-20211102-092924.sqlite")
cursor = conn.cursor()


# List all volumes + check that the number is correct according to Arkindex
def list_volume_name():
    cursor.execute("""select name from element where type="volume" group by name;""")
    name_book = cursor.fetchall()

    cursor.execute(
        """select count(*) from (select * from element where type="volume" group by name);"""
    )
    ttl_book = cursor.fetchall()
    print(
        "We have 1113 book listed in Arkindex and", ttl_book[0][0], "book in the db"
    )  # as of the 08/11/2021
    return name_book


# Lists all pages of each volume, then all single pages (if necessary)
# Example on the book with the name : "États-Unis, Cambridge, Harvard College Library, Lat. 251 (Sum. 60)"
def list_page_by_volume(name_volume):
    cursor.execute(
        """select * from element where element.id in (
    select child_id from element_path where parent_id=(
    select id from element where name='"""
        + name_volume
        + """'));"""
    )
    return cursor.fetchall()


#####################################################################
# Save the transcript and the page uid in a csv file, in page order,#
# one line per page, one file per volume                            #
#####################################################################

# Functions to fetch the information

# Get the transcript of each page/single page (check with mlb if there are all the time single pages)
def get_transcription_from_pageid_with_paragraph(page_id):
    cursor.execute(
        """select text from transcription where element_id in (
    select id from element where id in (
    select child_id from element_path where parent_id='"""
        + page_id
        + """')
    and type="paragraph" order by polygon)"""
    )
    return cursor.fetchall()


# Get the list a page from a book id
def get_list_page(book_id):
    cursor.execute(
        """select id from element where id in (
    select child_id from element_path where parent_id='"""
        + book_id
        + """')
    order by created;"""
    )
    return cursor.fetchall()


# Get the list a books from db
def get_list_book():
    cursor.execute("""select id from element where type="volume" group by name;""")
    list_book = cursor.fetchall()
    return list_book


# Saving a book in a csv
def save_book_as_csv(book_id):
    name = book_id + ".csv"
    with open(name, "w") as file:
        writer = csv.writer(file)

        li = get_list_page(book_id)
        for i in li:
            page_id = i[0]
            trans = get_transcription_from_pageid_with_paragraph(i[0])
            writer.writerow([page_id, trans])


# Saving all the book in their respective csv
def save_all_books():
    list_book = get_list_book()
    for i in list_book:
        save_book_as_csv(i[0])


# Use the volume uid as a file name : 91aceb13-792e-4a29-8767-07debe442f4d.csv for example
# b ="91aceb13-792e-4a29-8767-07debe442f4d"
# save_book_as_csv(b)

list_volume_name()
conn.close()
