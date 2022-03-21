#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import ast
import json
import logging
import os.path
import sqlite3
from collections import namedtuple

from apistar.exceptions import ErrorResponse
from arkindex import ArkindexClient, options_from_env
from shapely.geometry import Polygon

NewPageClassification = namedtuple("NewPageClassification", ["id_page", "list_class"])
TextSegment = namedtuple("TextSegment", ["name_ref", "x", "y", "w", "h"])
LineTranscription = namedtuple("LineTranscription", ["text", "x", "y", "w", "h"])
ID_RANGE = "https://arkindex.teklia.com/api/v1/"


class JsonCreator:
    def __init__(self, args):
        self.cli = ArkindexClient(**options_from_env())
        self.sql_file = args.get("sql_file")
        self.conn = None
        self.cursor = None
        self.digitization_type = None
        self.output_path = args.get("output_path")

    def __enter__(self):
        """Create a connection to the database"""
        self.conn = sqlite3.connect(self.sql_file)
        self.cursor = self.conn.cursor()
        return self

    def __exit__(self, *args, **kwargs):
        """Exit the connection of the database"""
        self.conn.close()

    def get_digitization_type(self, id_volume):
        """Set the digitization type"""
        self.cursor.execute(
            f"select value from metadata where name = 'Digitization Type' and element_id = '{id_volume}'"
        )
        # Get the first element of the first list (the only element) of the request
        self.digitization_type = self.cursor.fetchall()[0][0]

    def text_segment_creation(self, polygon, name_ref):
        mp = Polygon(ast.literal_eval(str(polygon)))
        x, y = mp.minimum_rotated_rectangle.exterior.coords.xy
        return TextSegment(
            name_ref, min(x), min(y), (max(x) - min(x)), (max(y) - min(y))
        )

    def line_transcription_creation(self, polygon, text):
        coord = Polygon(ast.literal_eval(str(polygon)))
        x, y = coord.minimum_rotated_rectangle.exterior.coords.xy
        return LineTranscription(
            text, min(x), min(y), (max(x) - min(x)), (max(y) - min(y))
        )

    def get_list_page_for_classification(self, id_folder):
        """Return list of namedtuple of PageClassification with id_page, ordering and list_class"""
        self.cursor.execute(
            f"select child_id, ordering from element_path where parent_id = '{id_folder}' order by ordering"
        )
        list_page_ordering = self.cursor.fetchall()

        line_transcriptions = {}
        text_segments = {}
        page_classification = []

        # Iterating through pages
        for fetched_page in list_page_ordering:
            # Giving proper name to variables
            id_page = fetched_page[0]

            # Get transcription and position on page and save it in a dictionary ordered by page id
            self.cursor.execute(
                f"select text, sel.polygon from transcription inner join (select id, polygon from element where id in (select child_id from element_path where parent_id='{id_page}') and type='text_line') as sel on transcription.element_id=sel.id"
            )
            list_text_lines = []
            for transcription in self.cursor.fetchall():
                # Giving proper name to variables
                trans_text = transcription[0]
                poly_text = transcription[1]

                list_text_lines.append(
                    self.line_transcription_creation(poly_text, trans_text)
                )
            if self.digitization_type == "single page" and list_text_lines:
                list_text_lines = sorted(list_text_lines, key=lambda x: x.y)

            elif self.digitization_type == "double page" and list_text_lines:
                # Order on the x_axis to find the min and max value
                sorted_lines_x = sorted(list_text_lines, key=lambda x: x[1])
                # Find the limit between left and right pages
                x_limit = (sorted_lines_x[0][1] + sorted_lines_x[-1][1]) / 2

                # Order list
                sorted_lines_y = sorted(list_text_lines, key=lambda x: x[2])

                list_text_lines = [row for row in sorted_lines_y if row[1] < x_limit]
                list_text_lines += [row for row in sorted_lines_y if row[1] >= x_limit]

            line_transcriptions[id_page] = list_text_lines

            # Get text_segment in page and save it in a dictionary ordered by page id
            self.cursor.execute(
                f"select name, polygon from element where id in (select child_id from element_path where parent_id='{id_page}') and type='text_segment'"
            )
            list_text_segments = []
            list_class_new = []
            for segment in self.cursor.fetchall():
                list_text_segments.append(
                    self.text_segment_creation(segment[1], segment[0])
                )
                list_class_new.append(segment[0])
            text_segments[id_page] = list_text_segments
            page_classification.append(NewPageClassification(id_page, list_class_new))

        return line_transcriptions, text_segments, page_classification

    def form_formulary(self, id_folder):
        """Forming formulary"""
        self.get_digitization_type(id_folder)
        try:
            manifest = self.cli.request("RetrieveFolderManifest", id=f"{id_folder}")
        except ErrorResponse as e:
            logging.error(f"Failed to retrieve folder manifest. {e.content}")

        (
            line_transcriptions,
            text_segments,
            page_classification,
        ) = self.get_list_page_for_classification(id_folder)

        # Add transcription on page at their right position
        for element in manifest["sequences"][0]["canvases"]:
            # Getting id of page from element["id"], ex :
            # https://arkindex.teklia.com/api/v1/iiif/e334e709-ecaa-4405-adf9-58918aa9ec63/canvas/ -> e334e709-ecaa-4405-adf9-58918aa9ec63
            page_id = element["@id"].split("/")[-3]

            # Creating annotation index
            element["annotations"] = [
                {"id": f"{ID_RANGE}l1", "type": "AnnotationPage", "items": []}
            ]
            # Add text_segment as tagging annotation in manifest
            if text_segments[page_id]:
                for ind, text_segment in enumerate(text_segments[page_id]):
                    element["annotations"][0]["items"].append(
                        {
                            "id": f"{ID_RANGE}l1/ts/{ind}",
                            "type": "Annotation",
                            "motivation": "tagging",
                            "body": {
                                "type": "TextualBody",
                                "value": text_segment.name_ref,
                                "format": "text/plain",
                            },
                            "target": f"{element['@id']}#xywh={text_segment.x},{text_segment.y},{text_segment.w},{text_segment.h}",
                        }
                    )
            # Add transcription as commenting annotation in manifest
            if line_transcriptions[page_id]:
                for ind, transcription in enumerate(line_transcriptions[page_id]):
                    element["annotations"][0]["items"].append(
                        {
                            "id": f"{ID_RANGE}l1/{ind}",
                            "type": "Annotation",
                            "motivation": "commenting",
                            "body": {
                                "type": "TextualBody",
                                "value": transcription.text,
                                "format": "text/plain",
                            },
                            "target": f"{element['@id']}#xywh={transcription.x},{transcription.y},{transcription.w},{transcription.h}",
                        }
                    )

        # Create list to match id in page classification to json id
        report = {}
        for element in manifest["structures"]:
            if "canvases" in element.keys():
                report[element["canvases"][0].split("/")[-3]] = element["canvases"][0]

        list_ref = []  # List of ref already registered
        class_ranges = {}

        # Create range
        for page in page_classification:
            # Check if there is a class in the page
            if page.list_class:
                # Act on each class of the page
                for ind, p_class in enumerate(page.list_class):
                    # Register the class
                    if p_class not in list_ref:
                        list_ref.append(p_class)
                        class_ranges[p_class] = {
                            "@id": f"{ID_RANGE}_{ind}/range/",
                            "@type": "sc:Range",
                            "label": p_class,
                            "ranges": [],
                        }
                    class_ranges[p_class]["ranges"].append(report[page.id_page])

        # Create ranges
        new_structures = []
        new_range = []
        for element in manifest["structures"]:
            if "canvases" in element.keys():
                for keys in class_ranges.keys():
                    # Test if the range belong in the page
                    if (
                        class_ranges[keys]["ranges"][0].split("/")[-3]
                        == element["canvases"][0].split("/")[-3]
                    ):
                        new_structures.append(class_ranges[keys])
                        new_range.append(class_ranges[keys]["@id"])

            new_structures.append(element)

        manifest["structures"] = new_structures

        manifest["structures"][0]["ranges"] = new_range

        with open(os.path.join(self.output_path, f"{id_folder}.json"), "w") as outfile:
            json.dump(manifest, outfile)

    def run(self):
        self.cursor.execute("select id from element where type = 'folder'")
        id_folder = self.cursor.fetchall()
        for id_row in id_folder:
            try:
                self.form_formulary(id_row[0])
                print(f"Manifest for volume {id_row[0]} was created")
            except (NameError, KeyError):
                print(
                    f"Something went wrong on volume {id_row[0]}, the volume might not be in the corpus or not be in the sql dump"
                    f"Assure you that you use the last exported sql dump or charge a new one"
                )
                pass


def main():
    """Takes arguments and run the program"""
    parser = argparse.ArgumentParser(
        description="Take a sql dump and create a iiif manifest",
    )
    parser.add_argument(
        "-s",
        "--sql-file",
        help="sql dump of the Arkindex corpus where the text-reuse worker has been applied",
        required=True,
    )
    parser.add_argument(
        "-o",
        "--output-path",
        help="Path where the output will be created",
        required=True,
    )

    args = vars(parser.parse_args())
    with JsonCreator(args) as f:
        f.run()


if __name__ == "__main__":
    main()
