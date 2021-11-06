# -*- coding: utf-8 -*-
import os

from horae_reference_texts.parser import make_stats

FIXTURES = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "data",
)


def test_dummy():
    count, mean, std, min, max, nb_different_words = make_stats(
        os.path.join(FIXTURES, "test_export_heurist_horae.csv")
    )
    assert count == 111
