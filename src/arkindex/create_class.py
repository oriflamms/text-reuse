#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import csv
import logging
from pathlib import Path

from apistar.exceptions import ErrorResponse
from arkindex import ArkindexClient, options_from_env

logging.basicConfig(
    format="[%(levelname)s] %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


class CreateClass:
    def __init__(self, args):
        self.cli = ArkindexClient(**options_from_env())
        self.corpus_id = args.get("corpus")
        self.metadata_path = args.get("metadata_heurist")

    def create_request(self):
        # Read the metadata
        with open(self.metadata_path, newline="") as meta_file:
            class_list = csv.reader(meta_file, delimiter=",")

            for row in class_list:
                body = {"name": row[1]}

                try:
                    self.cli.request("CreateMLClass", id=self.corpus_id, body=body)
                    logger.info(f"Created class {row[1]} in corpus {self.corpus_id}")

                except ErrorResponse as e:
                    logger.error(
                        f"Failed to create class {row[1]} in corpus {self.corpus_id}: {e.status_code} - {e.content}."
                    )

    def create_begin_inside_class(self):
        # Create beginning class
        try:
            self.cli.request(
                "CreateMLClass", id=self.corpus_id, body={"name": "Beginning"}
            )
            logger.info(f"Created class Beginning in corpus {self.corpus_id}")

        except ErrorResponse as e:
            logger.error(
                f"Failed to create class Beginning in corpus {self.corpus_id}: {e.status_code} - {e.content}."
            )

        # Create inside class
        try:
            self.cli.request(
                "CreateMLClass", id=self.corpus_id, body={"name": "Inside"}
            )
            logger.info(f"Created class Inside in corpus {self.corpus_id}")

        except ErrorResponse as e:
            logger.error(
                f"Failed to create class Inside in corpus {self.corpus_id}: {e.status_code} - {e.content}."
            )

    def run(self):
        self.create_request()
        self.create_begin_inside_class()


def main():
    parser = argparse.ArgumentParser(
        description="Create ML Classes in the indicated Arkindex corpus"
    )
    parser.add_argument(
        "-c", "--corpus", help="UUID of the Arkindex corpus", required=True, type=Path
    )
    parser.add_argument(
        "-m",
        "--metadata-heurist",
        help="Path of the csv containing the metadata",
        required=True,
        type=Path,
    )

    args = vars(parser.parse_args())

    CreateClass(args).run()


if __name__ == "__main__":
    main()
