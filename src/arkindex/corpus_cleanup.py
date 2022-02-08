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

    def run(self):
        # Destroying text_segment in all the volume of the corpus
        corpus_volumes = self.cli.paginate(
            "ListElements", corpus=self.corpus_id, type=self.type
        )
        for volume in corpus_volumes:
            self.destroy_transcription(volume["id"])

        # Destroying the class in the volume of the corpus
        self.destroy_text_segments()

        # Destroying the entities of the corpus
        if self.full_cleanup:
            self.destroy_entities()


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
