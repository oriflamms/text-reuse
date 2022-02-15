#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import logging

from apistar.exceptions import ErrorResponse
from arkindex import ArkindexClient, options_from_env


class Cleanup:
    """Clean the corpus of entities, transcription and classes on page level"""

    def __init__(self, args):
        self.cli = ArkindexClient(**options_from_env())
        self.corpus_id = args.get("corpus")
        self.full_cleanup = args.get("full_cleanup")
        self.type = args.get("type")
        logging.basicConfig(format="[%(levelname)s] %(message)s", level=logging.INFO)

    def destroy_transcription(self, volume_id):
        """Destroy transcrioption"""
        logging.info("Getting page")
        # Fetch info on pages
        try:
            volume_page = self.cli.paginate(
                "ListElementChildren", id=volume_id, type="page"
            )
        except ErrorResponse as e:
            logging.error(
                f"Failed to list page in volume {volume_id}: {e.status_code} - {e.content}."
            )

        for page in volume_page:
            # Fetch the transcription in the page
            try:
                page_transcription = self.cli.paginate(
                    "ListTranscriptions", id=page["id"], element_type="page"
                )
            except ErrorResponse as e:
                logging.error(
                    f"Failed to list transcription on page {page['id']}: {e.status_code} - {e.content}."
                )
            for transcription in page_transcription:
                # Destroy the transcription
                try:
                    self.cli.request("DestroyTranscription", id=transcription["id"])
                except ErrorResponse as e:
                    logging.error(
                        f"Failed to destroy transcription {transcription['id']} on page {page['id']}: {e.status_code} - {e.content}."
                    )

    def destroy_text_segments(self):
        logging.info(f"Destroying text segments in corpus {self.corpus_id}")
        try:
            self.cli.paginate(
                "DestroyElements", corpus=self.corpus_id, type="text_segment"
            )
        except ErrorResponse as e:
            logging.error(
                f"Failed to destroy text_segment in corpus {self.corpus_id}: {e.status_code} - {e.content}."
            )

    def destroy_entities(self):
        """Destroy entities"""
        logging.info("Listing the entities")
        try:
            corpus_entities = self.cli.paginate("ListCorpusEntities", id=self.corpus_id)
        except ErrorResponse as e:
            logging.error(
                f"Failed to list corpus entities in corpus {self.corpus_id}: {e.status_code} - {e.content}."
            )

        for entity in corpus_entities:
            try:
                self.cli.request("DestroyEntity", id=[entity["id"]])
            except ErrorResponse as e:
                logging.error(
                    f"Failed to destroy entity {[entity['id']]} in corpus {self.corpus_id}: {e.status_code} - {e.content}."
                )

    def destroy_metadata_entity(self):
        # List text_line in corpus https://demo.arkindex.org/api-docs/#tag/elements
        logging.info("Listing text_line")
        try:
            text_lines = self.cli.paginate(
                "ListElements", corpus=self.corpus_id, type="text_line"
            )
        except ErrorResponse as e:
            logging.error(
                f"Failed to list text_line in corpus {self.corpus_id}: {e.status_code} - {e.content}."
            )

        for text_line in text_lines:
            # List Metadata in the corpus https://demo.arkindex.org/api-docs/#operation/ListElementMetaData
            try:
                metadatas = self.cli.paginate("ListElementMetaData", id=text_line["id"])
            except ErrorResponse as e:
                logging.error(
                    f"Failed to list metadata in text_line {text_line['id']}: {e.status_code} - {e.content}."
                )

            for metadata in metadatas:
                if metadata["name"].lower() == "entity":
                    # Destroy metadata https://demo.arkindex.org/api-docs/#operation/DestroyMetaData
                    try:
                        self.cli.request("DestroyMetaData", id=metadata["id"])
                    except ErrorResponse as e:
                        logging.error(
                            f"Failed to destroy entity {metadata['id']} in corpus {self.corpus_id}: {e.status_code} - {e.content}."
                        )

    def clean_classification(self):
        """Destroy classification"""
        print("https://demo.arkindex.org/api-docs/#operation/RejectClassification")
        try:
            text_lines = self.cli.paginate(
                "ListElements",
                corpus=self.corpus_id,
                type="text_line",
                with_classes=True,
            )
        except ErrorResponse as e:
            logging.error(
                f"Failed to list text_line in corpus {self.corpus_id}: {e.status_code} - {e.content}."
            )

        for text_line in text_lines:
            if text_line["classes"]:
                try:
                    self.cli.request(
                        "RejectClassification",
                        id=text_line["classes"][0]["id"],
                        body={
                            "ml_class": text_line["classes"][0]["ml_class"]["id"],
                            "state": "rejected",
                        },
                    )
                except ErrorResponse as e:
                    logging.error(
                        f"Failed to list text_line in corpus {self.corpus_id}: {e.status_code} - {e.content}."
                    )

    def run(self):
        # Destroying text_segment in all the volume of the corpus
        corpus_volumes = self.cli.paginate(
            "ListElements", corpus=self.corpus_id, type=self.type
        )
        self.clean_classification()

        for volume in corpus_volumes:
            self.destroy_transcription(volume["id"])

        # Destroying the class in the volume of the corpus
        self.destroy_text_segments()

        # Destroying the entities of the corpus
        if self.full_cleanup:
            self.destroy_entities()

        # Destroy metadata entity
        # self.destroy_metadata_entity()


def main():

    parser = argparse.ArgumentParser(description="Cleanup the corpus")
    parser.add_argument(
        "-c",
        "--corpus",
        help="ID of the Arkindex corpus",
        required=True,
        type=str,
    )
    parser.add_argument(
        "-f",
        "--full-cleanup",
        help="If true destroy also the entity of the corpus",
        required=False,
        action="store_true",
    )
    parser.add_argument(
        "-t",
        "--type",
        help="Type of the elements containing pages (folder or volume)",
        default="folder",
        required=False,
        type=str,
    )

    args = vars(parser.parse_args())

    Cleanup(args).run()


if __name__ == "__main__":
    main()
