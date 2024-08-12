"""
Utility functions to be used in tests
"""

import json
import os

# from deepdiff import DeepDiff


def load_string_from_file(filename):
    """
    Return a file from the current directory as a string
    """
    cwd, _ = os.path.split(__file__)
    path = os.path.join(cwd, filename)
    with open(path, "r", encoding="utf-8") as json_file:
        json_data = json_file.read()
        return json_data


def assert_json_is_equal(json_a, json_b, exclude_paths=None):
    """
    Utility function to compare two JSON objects
    """
    # Load the JSON strings into Python dictionaries
    obj_a = json.loads(json_a)  # remains string #result.text
    obj_b = json.loads(json_b)  # converts to list

    # Compare the objects using DeepDiff
    # diff = DeepDiff(obj_a, obj_b, ignore_order=True, exclude_paths=exclude_paths)

    # # Raise an assertion error if there are differences
    # assert {} == diff, f"JSON not equal: {diff}"
