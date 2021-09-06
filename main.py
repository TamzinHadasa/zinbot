"""Runs 'zinbot."""
__author__ = "Tamzin Hadasa Kelly"
__copyright__ = "Copyright 2021, Tamzin Hadasa Kelly"
__license__ = "The MIT License"
__email__ = "coding@tamz.in"

import pagetriage.newpages


def run() -> None:
    """Run the bot's tasks that are currently approved / in trial."""
    pagetriage.newpages.checkqueue()  # pre-trial


if __name__ == "__main__":
    print("RUNNING")
    run()
