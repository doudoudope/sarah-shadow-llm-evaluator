import pytest
from app.utils.json_extract import extract_json


def test_clean_json():
    result = extract_json('{"answer": "Paris"}')
    assert result == {"answer": "Paris"}


def test_json_embedded_in_text():
    result = extract_json('Here is the result: {"answer": "Paris"} hope that helps!')
    assert result == {"answer": "Paris"}


def test_no_json_returns_none():
    result = extract_json("The capital of France is Paris.")
    assert result is None


def test_empty_string_returns_none():
    result = extract_json("")
    assert result is None


def test_malformed_json_returns_none():
    result = extract_json("{answer: Paris}")
    assert result is None


def test_nested_json():
    result = extract_json('{"outer": {"inner": "value"}}')
    assert result == {"outer": {"inner": "value"}}
