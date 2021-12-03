#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse
import warnings
from pathlib import Path

import pandas as pd
from sklearn.metrics import classification_report, multilabel_confusion_matrix

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


def evaluation(pred_file, true_file):
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

    # apply classification report
    for index, row in new_df_true.iterrows():
        print(f"For volume_id {index}")
        print(classification_report(row, new_df_pred.loc[index]))

    print("The classification report upon the whole dataframe")
    print(classification_report(new_df_true, new_df_pred, target_names=list_columns))

    # print(classification_report(y_true, y_pred, target_names=target_names))

    # confusion matrix
    print(multilabel_confusion_matrix(new_df_true, new_df_pred))


def main():
    parser = argparse.ArgumentParser(description="Evaluate text-matcher for two file")
    parser.add_argument(
        "--pred-file", type=Path, required=True, help="Path of the csv with prediction"
    )
    parser.add_argument(
        "--true-file", type=Path, required=True, help="Path of the csv with true value"
    )

    args = vars(parser.parse_args())

    # evaluate the matcher
    evaluation(args["pred_file"], args["true_file"])

    # Count the match between the column of the dataframe
    # count_the_match(args["pred_file"], args["true_file"])


if __name__ == "__main__":
    main()
