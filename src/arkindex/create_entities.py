#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import argparse
import csv
import glob
import logging
import os
from pathlib import Path

from apistar.exceptions import ErrorResponse
from arkindex import ArkindexClient, options_from_env


class CreateEntities:
    """
    Create entities in an Arkindex corpus from a list of reference texts that comes from the Heurist base from the IRHT
    """

    def __init__(self, args):
        self.cli = ArkindexClient(**options_from_env())
        self.corpus_id = args.get("corpus")
        if os.path.isdir(args.get("reference")):
            self.folder_ref = glob.glob(
                str(args.get("reference")) + "/**/*.txt", recursive=True
            )
        else:
            raise logging.info(f"ERROR : {args.get('reference')} is not a directory")
        self.metadata_path = args.get("heurist_metadata")
        self.entity_dict = {}
        logging.basicConfig(format="[%(levelname)s] %(message)s", level=logging.INFO)

    def run(self):
        """Create the body of the request for each reference text"""

        # Read the metadata
        with open(self.metadata_path, newline="") as meta_file:
            entity_list = csv.reader(meta_file, delimiter=",")

            for meta_row in entity_list:
                text_path = [
                    ref
                    for ref in self.folder_ref
                    if meta_row[0] in os.path.basename(ref)
                ]
                if text_path:
                    name = meta_row[1]
                    heurist_id = meta_row[2]
                    old_arkindex_heurist_id = meta_row[0]
                    with open(text_path[0], "r") as psalm_file:
                        property1 = psalm_file.read()

                    self.entity_dict["name"] = name
                    self.entity_dict["type"] = "misc"
                    self.entity_dict["metas"] = {
                        "text": property1,
                        "heurist_id": heurist_id,
                        "arkindex_id": old_arkindex_heurist_id,
                    }
                    self.entity_dict["corpus"] = self.corpus_id

                    self.push_to_arkindex()

        # Create beginning entity
        self.create_begin_inside_entity()

    def push_to_arkindex(self):
        """Create the entity on Arkindex"""
        logging.info(
            f"Sending {self.entity_dict['name']} entity to corpus id {self.corpus_id}"
        )
        try:
            self.cli.request("CreateEntity", body=self.entity_dict)
        except ErrorResponse as e:
            logging.error(
                f"Failed to create entity {self.entity_dict['name']} in corpus {self.corpus_id}: {e.status_code} - {e.content}."
            )

    def create_begin_inside_entity(self):
        """Create the entity of beginning"""
        logging.info("Creating beginning entity")
        try:
            body = {
                "name": "Beginning",
                "type": "misc",
                "metas": {"text": "Beginning marker"},
                "corpus": self.corpus_id,
            }
            self.cli.request("CreateEntity", body=body)
        except ErrorResponse as e:
            logging.error(
                f"Failed to create entity Beginning in corpus {self.corpus_id}: {e.status_code} - {e.content}."
            )
        logging.info("Creating inside entity")
        try:
            body = {
                "name": "Inside",
                "type": "misc",
                "metas": {"text": "Beginning marker"},
                "corpus": self.corpus_id,
            }
            self.cli.request("CreateEntity", body=body)
        except ErrorResponse as e:
            logging.error(
                f"Failed to create entity Beginning in corpus {self.corpus_id}: {e.status_code} - {e.content}."
            )


def main():
    parser = argparse.ArgumentParser(
        description="Take a folder of reference text and add it to Arkindex entities"
    )
    parser.add_argument(
        "--reference",
        help="Folder of reference text under format txt",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "--heurist-metadata",
        help="Csv of metadata from heurist base with arkindex ID, heurist ID and name of reference text",
        type=Path,
        required=True,
    )
    parser.add_argument(
        "--corpus",
        help="UUID of the corpus where the entities will be created",
        type=str,
        required=True,
    )
    args = vars(parser.parse_args())

    entity_creator = CreateEntities(args)
    entity_creator.run()


if __name__ == "__main__":
    main()
