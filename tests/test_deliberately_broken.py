"""Scratch file: proves the CI gate fails when a test fails. Deleted after the run."""


def test_this_must_fail() -> None:
    assert 1 == 2, "deliberate failure to prove CI catches it"
