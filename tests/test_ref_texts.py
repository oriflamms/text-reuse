# -*- coding: utf-8 -*-
import os

from horae_reference_texts.ref_texts import ReferenceTexts

FIXTURES = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "data",
)


def test_dummy():
    reftext = ReferenceTexts(
        os.path.join(FIXTURES, "test_export_heurist_horae.csv"), []
    )
    count, mean, std, min, max, nb_different_words = reftext.get_statistics()
    assert count == 111
    assert min == 1.0
    assert max == 503.0
    assert nb_different_words == 1515
    assert mean == 29.594594594594593
