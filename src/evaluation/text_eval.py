#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
from pathlib import Path
import pandas as pd
from sklearn.metrics import classification_report
import warnings
warnings.filterwarnings('ignore')


def evaluation(pred_file, true_file):
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

    # apply classification report

    for index, row in new_df_true.iterrows():
        print(f"For volume_id {index}")
        print(classification_report(row, new_df_pred.loc[index]))


def main():
    parser = argparse.ArgumentParser(
        description="Evaluate text-matcher for two file"
    )
    parser.add_argument(
        "--pred-file",
        type=Path,
        required=True,
        help="Path of the csv with prediction"
    )
    parser.add_argument(
        "--true-file",
        type=Path,
        required=True,
        help="Path of the csv with true value"
    )

    args = vars(parser.parse_args())

    evaluation(args["pred_file"], args["true_file"])


if __name__ == "__main__":
    main()
