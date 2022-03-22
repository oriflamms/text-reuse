#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import itertools
import logging

from apistar.exceptions import ErrorResponse
from arkindex import ArkindexClient, options_from_env
from shapely.geometry import Polygon
from text_matcher.matcher import Matcher, Text


class CreateMatchArkindex:
    def __init__(self, args):
        """Initiate the class"""
        self.cli = ArkindexClient(**options_from_env())
        self.corpus_id = args.get("corpus")
        self.type_element_parent = args.get("type")
        self.entities_classes = []
        logging.basicConfig(format="[%(levelname)s] %(message)s", level=logging.INFO)

    @staticmethod
    def normalization(text):
        text = text.replace("j", "i")
        text = text.replace("J", "I")
        text = text.replace("v", "u")
        text = text.replace("V", "U")
        text = text.replace("ë", "e")
        text = text.replace("Ë", "E")
        text = text.replace("æ", "e")
        text = text.replace("Æ", "E")
        text = text.replace("œ", "e")
        text = text.replace("Œ", "E")
        return text

    def text_matcher(self, volume_transcription):
        """Match volume against text of reference and return position of match"""
        # Pairs of text to be matched against
        pairs = list(
            itertools.product(["volume"], [item[0] for item in self.entities_classes])
        )

        # Dictionary of texts
        texts = {"volume": volume_transcription}
        for row in self.entities_classes:
            texts[row[0]] = row[2]

        prev_text_objs = {}
        matches = []
        # Find the match for each pair:
        for index, pair in enumerate(pairs):
            filename_a, filename_b = pair[0], pair[1]

            # Put this in a dictionary, so we don't have to process a file twice.
            for filename in [filename_a, filename_b]:
                if filename not in prev_text_objs:
                    prev_text_objs[filename] = Text(
                        self.normalization(texts[filename]), filename
                    )
                    save_text = texts[filename]

            # More convenient naming
            text_obj_a = prev_text_objs[filename_a]
            text_obj_b = prev_text_objs[filename_b]

            # Reset the table of previous text objects, so we don't overload memory.
            prev_text_objs = {filename_a: text_obj_a, filename_b: text_obj_b}

            # Do the matching
            pair_match = Matcher(
                text_obj_a,
                text_obj_b,
                threshold=7,
                cutoff=4,
                ngramSize=7,
                removeStopwords=False,
                minDistance=200,
            )
            pair_match.match()

            # Write to the log, but only if a match is found
            if pair_match.numMatches > 0:
                matches.append(
                    [
                        pair[1],
                        pair_match.locationsA,
                        pair_match.locationsB,
                        len(save_text),
                    ]
                )

        return matches

    def list_corpus_entities_and_classes(self):
        """List the entity and the class inside the corpus"""
        logging.info("Listing the entities and the classes of the corpus")
        # Listing the entities
        try:
            corpus_entities = self.cli.paginate("ListCorpusEntities", id=self.corpus_id)
        except ErrorResponse as e:
            logging.error(
                f"Failed to list corpus entity in corpus {self.corpus_id}: {e.status_code} - {e.content}."
            )

        # Insert in tab all the information necessary to connect entities with their class : [id_entity, name_obj, text_obj, EMPTY] (EMPTY : where the class ID will be)
        for entity in corpus_entities:
            self.entities_classes.append(
                [entity["id"], entity["name"], entity["metas"]["text"], ""]
            )

        # Listing the classes
        try:
            corpus_classes = self.cli.paginate("ListCorpusMLClasses", id=self.corpus_id)
        except ErrorResponse as e:
            logging.error(
                f"Failed to list classes in corpus {self.corpus_id}: {e.status_code} - {e.content}"
            )

        # Add the class_id in EMPTY to complete the link between class and entity
        for _class in corpus_classes:
            for row in self.entities_classes:
                if _class["name"] == row[1]:
                    row[3] = _class["id"]

    # get_text_lines_centroid
    def get_text_lines_from_page_id(self, page_id):
        """Fetch text_line from a page id"""
        logging.info("Getting text line")
        # Get info on text_line
        try:
            list_text_line = self.cli.paginate(
                "ListTranscriptions",
                id=page_id,
                recursive=True,
                element_type="text_line",
            )
        except ErrorResponse as e:
            logging.error(
                f"Failed to list transcription in corpus {self.corpus_id}: {e.status_code} - {e.content}."
            )

        page_text_line = []
        for element in list_text_line:
            page_text_line.append(
                [
                    element["text"],
                    Polygon(element["element"]["zone"]["polygon"]).centroid.x,
                    Polygon(element["element"]["zone"]["polygon"]).centroid.y,
                    element["element"]["zone"]["polygon"],
                    element["element"]["id"],
                ]
            )

        return page_text_line

    @staticmethod
    def order_single_page(page_text_line):
        """Order position in single paged book"""
        # Order on the y_axis
        return sorted(page_text_line, key=lambda x: x[2])

    @staticmethod
    def order_double_page(page_text_line):
        """Order position in double paged book"""
        logging.info("Double page")
        # Order on the x_axis to find the min and max value
        temp = sorted(page_text_line, key=lambda x: x[1])
        # Find the limit between left and right pages
        x_limit = (temp[0][1] + temp[-1][1]) / 2

        # Order list
        temp = sorted(page_text_line, key=lambda x: x[2])
        page_text_line = []
        for i in [0, 1]:
            for ind, row in enumerate(temp):
                if i == 0 and row[1] < x_limit:
                    page_text_line.append(row)
                if i == 1 and row[1] > x_limit:
                    page_text_line.append(row)

        return page_text_line

    def check_type_volume(self, volume_id):
        """Check if the volume is double paged or single paged"""
        logging.info("Check volume digitization type")
        try:
            volume_metadata = self.cli.paginate("ListElementMetaData", id=volume_id)
            digitization_type = next(
                item for item in volume_metadata if item["name"] == "Digitization Type"
            )["value"]
        except ErrorResponse as e:
            logging.error(
                f"Failed to list metadata for volume {volume_id}: {e.status_code} - {e.content}."
            )
            return
        except StopIteration:
            raise StopIteration(
                f"Failed to retrieve Digitization Type metadata for volume {volume_id}."
            )

        return digitization_type

    def create_transcription(self, id_page, page_transcription):
        """Create a transcription for a page"""
        logging.info("Sending page transcription to Arkindex")
        body_request = {"text": page_transcription}
        try:
            page_transcription = self.cli.request(
                "CreateTranscription", id=id_page, body=body_request
            )
        except ErrorResponse as e:
            logging.error(
                f"Failed to create {body_request} on page {id_page}: {e.status_code} - {e.content}."
            )

        return page_transcription["id"]

    def create_transcription_entity(self, id_transcription, id_entity, offset, length):
        """Create an element of transcription for a transcription"""
        logging.info("Create transcription entity")
        body_request_transcription_entity = {
            "entity": id_entity,
            "offset": offset,
            "length": length,
        }
        try:
            self.cli.request(
                "CreateTranscriptionEntity",
                id=id_transcription,
                body=body_request_transcription_entity,
            )
        except ErrorResponse as e:
            logging.error(
                f"Failed to create transcription entity {body_request_transcription_entity} in corpus {self.corpus_id}: {e.status_code} - {e.content}."
            )

    def create_text_segment(self, parent_id, name, polygon, ml_class):
        logging.info("Create element")
        body = {
            "type": "text_segment",
            "name": name,
            "corpus": self.corpus_id,
            "parent": parent_id,
            "polygon": polygon,
        }
        try:
            response_create_element = self.cli.request(
                "CreateElement",
                slim_output=True,
                body=body,
            )
        except ErrorResponse as e:
            logging.error(
                f"Failed to create text_segment element {body} in corpus {self.corpus_id}: {e.status_code} - {e.content}."
            )

        self.create_classification(response_create_element["id"], ml_class)

    def form_transcription_book(self, volume_id):
        """Form transcription from a book id on Arkindex"""
        list_page_id_transcription_id = []
        letter_page_id_offset = []
        volume_transcription = ""
        logging.info("Forming transcription")
        # Check type of the book
        digitization_type = self.check_type_volume(volume_id)

        # Get the volume transcription
        logging.info("Getting page")
        # Get info on pages
        try:
            volume_pages = self.cli.paginate(
                "ListElementChildren", id=volume_id, type="page"
            )
        except ErrorResponse as e:
            logging.error(
                f"Failed to list element children in corpus {self.corpus_id}: {e.status_code} - {e.content}."
            )

        for page in volume_pages:

            page_text_lines = self.get_text_lines_from_page_id(page["id"])
            if digitization_type == "double page" and page_text_lines:
                page_text_lines = self.order_double_page(page_text_lines)
            elif digitization_type == "single page" and page_text_lines:
                page_text_lines = self.order_single_page(page_text_lines)

            # Form the text of the transcription
            offset = 0
            page_transcription = ""
            for row in page_text_lines:
                volume_transcription += row[0] + " "
                for char in list(row[0]):
                    letter_page_id_offset.append(
                        [char, page["id"], offset, row[3], row[4]]
                    )
                    offset += 1
                page_transcription += row[0] + "\n"
                letter_page_id_offset.append(
                    [" ", page["id"], offset + 1, row[3], row[4]]
                )

            # Create transcription on page
            if page_transcription:
                id_transcription = self.create_transcription(
                    page["id"], page_transcription
                )
                # Create a list with relation between transcription id and page id
                list_page_id_transcription_id.append([page["id"], id_transcription])
        return (
            volume_transcription,
            list_page_id_transcription_id,
            letter_page_id_offset,
        )

    def create_classification(self, element_id, ml_class):
        logging.info("Creating classification")
        try:
            self.cli.request(
                "CreateClassification",
                body={"element": element_id, "ml_class": ml_class},
            )
        except ErrorResponse as e:
            logging.error(
                f"Failed to create classification {ml_class} in text_line {element_id}: {e.status_code} - {e.content}."
            )

    def push_matches_to_arkindex(
        self, matched_results, list_page_id_transcription_id, letter_page_id_offset
    ):
        """Push match to Arkindex"""
        for match in matched_results:

            # Iterate through match inside each reference text
            for intra_match in match[1]:

                offset = letter_page_id_offset[intra_match[0]][2]
                id_entity = match[0]
                # start_match = intra_match[0]  # Start indicated by text-matcher
                # end_match = intra_match[1]  # End indicated by text-matcher
                start_approx = (
                    intra_match[0] - match[2][0][0]
                )  # Start extended with the info on the text of ref
                end_approx = (
                    intra_match[1] + match[3] - match[2][0][1]
                )  # End extended with the info on the text of ref
                text_line_id = letter_page_id_offset[start_approx][4]

                # Add class to text_line at the beginning of the match
                for entity_class in self.entities_classes:
                    if match[0] == entity_class[0]:
                        # Catch the id of the class and add the class to the text_line
                        class_id = entity_class[3]
                        self.create_classification(text_line_id, class_id)

                    elif "Beginning" in entity_class:
                        # Add Beginning class to text_line
                        self.create_classification(text_line_id, entity_class[3])

                    elif "Inside" in entity_class:
                        # Catch the id of the Inside class
                        i_class_id = entity_class[3]

                # Create entity for the intra match
                for entity_class in self.entities_classes:
                    if match[0] == entity_class[0]:
                        self.create_text_segment(
                            letter_page_id_offset[start_approx][1],
                            entity_class[1],
                            letter_page_id_offset[start_approx][3],
                            entity_class[3],
                        )

                # Create transcription entity for each intra_match
                for ind, row in enumerate(
                    letter_page_id_offset[start_approx:end_approx]
                ):
                    if (
                        start_approx + ind == end_approx - 1
                        or row[1] != letter_page_id_offset[start_approx + ind + 1][1]
                    ):  # Check if the match continue on a different page
                        # Get the id of the transcription on the page
                        id_transcription = [
                            info_trans[1]
                            for info_trans in list_page_id_transcription_id
                            if row[1] in info_trans[0]
                        ]
                        # Push the transcription entity on Arkindex
                        self.create_transcription_entity(
                            id_transcription[0],
                            id_entity,
                            offset,
                            row[2] - offset,  # Number of character in the entity
                        )
                        offset = 0

                    # Add class in the metadata of the new text_line
                    if row[4] != text_line_id:
                        text_line_id = row[4]

                        # Add Beginning class to text_line
                        self.create_classification(text_line_id, i_class_id)

                        # Add the class to the text_line
                        self.create_classification(text_line_id, class_id)

    def run(self):
        # List all the volume in corpus
        try:
            corpus_volumes = self.cli.paginate(
                "ListElements", corpus=self.corpus_id, type=self.type_element_parent
            )
        except ErrorResponse as e:
            logging.error(
                f"Failed to list volume in corpus {self.corpus_id}: {e.status_code} - {e.content}"
            )

        self.list_corpus_entities_and_classes()

        for volume in corpus_volumes:

            # Form the volume transcription
            (
                volume_transcription,
                list_page_id_transcription_id,
                letter_page_id_offset,
            ) = self.form_transcription_book(volume["id"])

            # Apply text_matcher
            matched_results = self.text_matcher(volume_transcription)

            # Send match to Arkindex
            self.push_matches_to_arkindex(
                matched_results, list_page_id_transcription_id, letter_page_id_offset
            )


def main():
    parser = argparse.ArgumentParser(
        description="Get the volume transcription applies text-matcher and add the result in Arkindex"
    )
    parser.add_argument(
        "-c",
        "--corpus",
        help="ID of the Arkindex corpus",
        required=True,
        type=str,
    )
    parser.add_argument(
        "-t",
        "--type",
        help="Type of the element to apply text matcher (folder or volume)",
        default="folder",
        required=False,
        type=str,
    )

    args = vars(parser.parse_args())
    CreateMatchArkindex(args).run()


if __name__ == "__main__":
    main()
