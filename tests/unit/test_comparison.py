import pytest
from app.utils.comparison import compare


def test_matching_dicts():
    assert compare({"answer": "Paris"}, {"answer": "Paris"}) is True


def test_mismatching_dicts():
    assert compare({"answer": "Paris"}, {"answer": "Lyon"}) is False


def test_first_none():
    assert compare(None, {"answer": "Paris"}) is False


def test_second_none():
    assert compare({"answer": "Paris"}, None) is False


def test_both_none():
    assert compare(None, None) is False


def test_different_keys():
    assert compare({"answer": "Paris"}, {"city": "Paris"}) is False
