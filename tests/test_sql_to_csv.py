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

    # the data to assert
    single_assert = "statis gaudio fod vivere fidelium Deus omnium conditor et redemper torro animabus famulo rum famularum quae tu aurum remissionem annorum eorum tribue peccatorum ut indulgentiam quam semper optaverunt prius supplicationibus conse quaetur Qui vivis et re regnas Deus per omnia secula seculorum amen requiescant in pacem "
    double_asert = "me pries luy que il vueille me pries luy que il vueille egesimo octavoir mon cuer calum egesimo octavoir mon cuer calum servir et amer servir et amer Ave maria Ave maria Eratres doulce dame pour Eratres doulce dame pour Arcelle grant ioie que Arcelle grant ioie que vous eustes au iour de nost vous eustes au iour de nost quant prae doule filia nascum quant prae doule filia nascum de populus Doulce dame pries de populus Doulce dame pries luy que il mortiorem habens luy que il mortiorem habens Mitte natuite ama redemptio Mitte natuite ama redemptio Ave maria Ave maria Patres doulce dame post Patres doulce dame post Sur icelle grant ioitum Sur icelle grant ioitum que vous eustes quant vos que vous eustes quant vos trigis robis viderent ostris trigis robis viderent ostris a vostre doule fili cor muliere a vostre doule fili cor muliere et encens et il les receut et encens et il les receut Doulce dame pries luper quae Doulce dame pries luper quae il vueille recesservoir mam il vueille recesservoir mam quant elephara Domini quant elephara Domini corpus corpus Lae maria Lae maria Et tres doulce dame per Et tres doulce dame per Assur icelle grant more Assur icelle grant more que vous eustes quant vos que vous eustes quant vos Christus in templum Christus in templum invenirent curribus invenirent curribus "

    # asserts
    assert single_assert == test_simple
    assert double_asert == test_double
