# -*- coding: utf-8 -*-
import os

import pandas as pd
from sql_to_csv.sql_to_csv import SqlToCsv

FIXTURES = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "data",
)


def test_dummy():
    # get the dummy file test
    df_simple = pd.read_csv(
        os.path.join(FIXTURES, "single48f50e0e-4874-451e-b47a-0e6f6859d9c2.csv")
    )
    df_double = pd.read_csv(
        os.path.join(FIXTURES, "double1bdc52cf-49ad-4ffd-b510-2efb2ff38f84.csv")
    )

    # apply the function
    test_simple = SqlToCsv.get_transcription_df_single_page(df_simple)
    test_double = SqlToCsv.get_transcription_double_page_df(df_double)

    # asserts
    assert type("a") == type(test_simple)
    assert type("a") == type(test_double)
