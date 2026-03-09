"""Тест запускает flake8"""

import subprocess


def test_flake8():
    """Тест запускает flake8"""
    result = subprocess.run(
        ["flake8", "./src", "./tests"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert (
        result.returncode == 0
    ), f"Flake8 errors:\n{result.stdout}\n{result.stderr}"
