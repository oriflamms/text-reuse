# -*- coding: utf-8 -*-
import os

from horae_reference_texts.ref_texts import ReferenceTexts

FIXTURES = os.path.join(
    os.path.dirname(os.path.realpath(__file__)),
    "data",
)


def test_dummy():
    reftext = ReferenceTexts(
        os.path.join(FIXTURES, "test_export_heurist_horae.csv"), ""
    )
    count, mean, std, min, max, nb_different_words = reftext.get_statistics()
    assert count == 111
    assert min == 1.0
    assert max == 483.0
    assert nb_different_words == 1457
    assert mean == 28.945945945945947
