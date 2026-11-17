"""Scratch file: proves the CI gate fails when a test fails. Deleted after the run."""


def test_this_must_fail() -> None:
    actual = [1, 2]
    assert actual == [1, 3], "deliberate runtime failure to prove CI catches it"
