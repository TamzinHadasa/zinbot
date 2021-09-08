"""Runs 'zinbot."""
__author__ = "Tamzin Hadasa Kelly"
__copyright__ = "Copyright 2021, Tamzin Hadasa Kelly"
__license__ = "The MIT License"
__email__ = "coding@tamz.in"
__version__ = "1.2.1"

import pagetriage.newpages


def run() -> None:
    """Run the bot's tasks that are currently approved / in trial."""
    pagetriage.newpages.checkqueue()  # trial (log-only)


if __name__ == "__main__":
    print("RUNNING")
    run()
