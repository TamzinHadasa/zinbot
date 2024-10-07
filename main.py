"""Runs 'zinbot."""
__author__ = "Tamzin Hadasa Kelly"
__copyright__ = "Copyright 2021-2024, Tamzin Hadasa Kelly"
__license__ = "The MIT License"
__email__ = "coding@tamz.in"
__version__ = "1.4.4"

import time

import api
import pagetriage.newpages


def run() -> None:
    """Run the bot's tasks."""
    print(f"Site time is {api.site_time()}")
    pagetriage.newpages.checkqueue()


if __name__ == "__main__":
    print(f"RUNNING (version {__version__})")
    while True:
        run()
        print(f"{api.site_time()}: Run done. Sleeping.")
        time.sleep(1800)
