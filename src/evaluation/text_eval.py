#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import csv
import os
import warnings
from pathlib import Path

import pandas as pd
from sklearn.metrics import classification_report

warnings.filterwarnings("ignore")


def count_the_match(pred_file, true_file):
    """Return the number of similar column that exist between the two file"""
    df_pred = pd.read_csv(pred_file, index_col=0)
    df_pred = df_pred.sort_index()

    df_true = pd.read_csv(true_file, index_col=0)
    df_true = df_true.sort_index()

    list_col_true = df_true.columns
    list_col_pred = df_pred.columns
    list_columns = []
    for col in list_col_true:
        if col in list_col_pred:
            list_columns.append(col)

    print(list_columns)


# matcher avec metadata volume pour avoir le nom des volume
def evaluation(pred_file, true_file, metadata_heurist, output_path, metadata_volume):
    """Evaluate the precision and the recall between the prediction and the true file"""
    # read csv and order the row
    df_pred = pd.read_csv(pred_file, index_col=0)
    df_pred = df_pred.sort_index()

    df_true = pd.read_csv(true_file, index_col=0)
    df_true = df_true.sort_index()

    # clean the column to keep only those who exist in both df
    list_col_true = df_true.columns
    list_col_pred = df_pred.columns
    list_columns = []
    for col in list_col_true:
        if col in list_col_pred:
            list_columns.append(col)

    new_df_true = df_true[list_columns]
    new_df_pred = df_pred[list_columns]

    # new column name
    meta_h = pd.read_csv(metadata_heurist)
    list_col = meta_h["ID Annotation"].to_numpy()
    new_name = []
    for name in list_col:
        new_name.append(" ".join(name.split()[-6:]))

    list_new_col = []
    for col in list_columns:
        for i in new_name:
            if i.split()[-1] == col:
                list_new_col.append(i)

    new_df_true = new_df_true.set_axis(list_new_col, axis="columns")
    new_df_pred = new_df_pred.set_axis(list_new_col, axis="columns")

    # volume name
    with open(metadata_volume, newline="") as meta_file:
        meta_v = list(csv.reader(meta_file, delimiter=","))

    # apply classification report
    for index, row in new_df_true.iterrows():
        name_volume = ""
        for row_v in meta_v:
            if row_v[0] == index:
                name_volume = row_v[1]

        if name_volume:
            print(f"For volume_id {index} and volume name: {name_volume}")
        else:
            print(f"For volume_id {index}")
        print(classification_report(row, new_df_pred.loc[index]))

    print("The classification report upon the whole dataframe")
    print(classification_report(new_df_true, new_df_pred, target_names=list_new_col))

    # Multiple output classification report

    # Adding a line for the total
    df_new = pd.DataFrame(0, columns=list_new_col, index=["Total"])
    new_df_true = new_df_true.append(df_new, ignore_index=False)
    new_df_pred = new_df_pred.append(df_new, ignore_index=False)
    for col in list_new_col:
        new_df_true.loc["Total", col] = new_df_true[col].sum()
        new_df_pred.loc["Total", col] = new_df_pred[col].sum()

    # Export of the new csv
    new_df_true.to_csv(os.path.join(output_path, "result_pred.csv"), index=True)
    new_df_true.to_csv(os.path.join(output_path, "result_true.csv"), index=True)


def main():
    parser = argparse.ArgumentParser(description="Evaluate text-matcher for two file")
    parser.add_argument(
        "--pred-file",
        type=Path,
        required=True,
        help="Path of the csv with prediction",
    )
    parser.add_argument(
        "--true-file",
        type=Path,
        required=True,
        help="Path of the csv with true value",
    )
    parser.add_argument(
        "--metadata-heurist",
        type=Path,
        required=True,
        help="Path of the metadata file",
    )
    parser.add_argument(
        "--metadata-volume",
        type=Path,
        required=True,
        help="Path of the metadata of the volume",
    )
    parser.add_argument(
        "--output-path",
        type=Path,
        required=True,
        help="Path where the output will be generated",
    )

    args = vars(parser.parse_args())

    # evaluate the matcher
    evaluation(
        args["pred_file"],
        args["true_file"],
        args["metadata_heurist"],
        args["output_path"],
        args["metadata_volume"],
    )

    # Count the match between the column of the dataframe
    # count_the_match(args["pred_file"], args["true_file"])


if __name__ == "__main__":
    main()
