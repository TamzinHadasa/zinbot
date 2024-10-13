"""Runs 'zinbot."""
__author__ = "Tamzin Hadasa Kelly"
__copyright__ = "Copyright 2021-2024, Tamzin Hadasa Kelly"
__license__ = "The MIT License"
__email__ = "coding@tamz.in"

import datetime as dt

import constants
import pagetriage.newpages

__version__ = constants.VERSION


def run() -> None:
    """Run the bot's tasks."""
    pagetriage.newpages.checkqueue()


if __name__ == "__main__":
    print(f"RUNNING (version {__version__})")
    print(f"{dt.datetime.now()}: Starting run.")
    run()
    print(f"{dt.datetime.now()}: Run done.")
