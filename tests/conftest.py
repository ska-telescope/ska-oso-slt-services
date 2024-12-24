import json
import os

import pytest


def load_string_from_file(filename):
    """
    Return a file from the current directory as a string
    """
    cwd, _ = os.path.split(__file__)
    path = os.path.join(cwd, filename)
    with open(path, "r", encoding="utf-8") as json_file:
        json_data = json.load(json_file)
        return json_data


json_file_path = "unit/ska_oso_slt_services/routers/test_data_files"


@pytest.fixture
def existing_shift_data():
    """Fixture to load and return existing shift data from a JSON file.

    Returns contents of the JSON file containing existing shift data loaded as a string.
    """
    return load_string_from_file(f"{json_file_path}/testfile_existing_shift_data.json")


@pytest.fixture
def updated_shift_data():
    """Fixture to load and return updated shift data from a JSON file.

    Returns contents of the JSON file containing updated shift data loaded as a string.
    """
    return load_string_from_file(f"{json_file_path}/testfile_update_shift_data.json")


@pytest.fixture
def shift_log_comment_data():
    """Fixture to load and return shift log comment data from a JSON file.

    Returns contents of the JSON file containing shift log comment data
    loaded as a string.
    """
    return load_string_from_file(
        f"{json_file_path}/testfile_shift_log_comments_data.json"
    )


@pytest.fixture
def shift_initial_comment_data():
    """Fixture to load and return shift initial comment data from a JSON file.

    Returns contents of the JSON file containing shift initial comment data
    loaded as a string.
    """
    return load_string_from_file(
        f"{json_file_path}/testfile_initial_log_comment_data.json"
    )


@pytest.fixture
def current_shift_data():
    """Fixture to load and return current shift data from a JSON file.

    Returns contents of the JSON file containing current shift data loaded as a string.
    """
    return load_string_from_file(f"{json_file_path}/testfile_current_shift_data.json")


@pytest.fixture
def shift_comment_data():
    """Fixture to load and return existing shift comment data from a JSON file.

    Returns contents of the JSON file containing shift comment data loaded as a string.
    """
    return load_string_from_file(f"{json_file_path}/testfile_shift_comment_data.json")


@pytest.fixture
def shift_data():
    """Fixture to load and return existing shift data from a JSON file.

    Returns contents of the JSON file containing shift data loaded as a string.
    """
    return load_string_from_file(f"{json_file_path}/testfile_sample_shift_data.json")


@pytest.fixture
def shift_history_data():
    """Fixture to load and return existing shift history data from a JSON file.

    Returns contents of the JSON file containing shift history data loaded as a string.
    """
    return load_string_from_file(
        f"{json_file_path}/testfile_sample_shift_history_data.json"
    )


@pytest.fixture
def shift_comment_image_data():
    """Fixture to load and return shift comment image data from a JSON file.

    Returns contents of the JSON file containing shift comment image data
    loaded as a string.
    """
    return load_string_from_file(
        f"{json_file_path}/testfile_shift_comment_image_data.json"
    )


@pytest.fixture
def shift_log_comment_image_data():
    """Fixture to load and return shift comment image data from a JSON file.

    Returns contents of the JSON file containing shift comment image data
    loaded as a string.
    """
    return load_string_from_file(
        f"{json_file_path}/testfile_shift_log_comment_image_data.json"
    )


@pytest.fixture
def shift_patch_log_data():
    """Fixture to load and return shift patch log data from a JSON file.

    Returns contents of the JSON file containing shift patch log data
    loaded as a string.
    """
    return load_string_from_file(f"{json_file_path}/testfile_patch_shift_log_data.json")


@pytest.fixture
def get_shift_comment_image_data():
    """Fixture to load and return get shift comment image data from a JSON file.

    Returns contents of the JSON file containing get shift comment image data
    loaded as a string.
    """
    return load_string_from_file(
        f"{json_file_path}/testfile_get_shift_comment_image_data.json"
    )


@pytest.fixture
def set_telescope_type():
    return "mid"
