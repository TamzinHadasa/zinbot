"""Runs 'zinbot."""
__author__ = "Tamzin Hadasa Kelly"
__copyright__ = "Copyright 2021-2024, Tamzin Hadasa Kelly"
__license__ = "The MIT License"
__email__ = "coding@tamz.in"
__version__ = "1.5.0-bugfix-0"

import api
import pagetriage.newpages


def run() -> None:
    """Run the bot's tasks."""
    pagetriage.newpages.checkqueue()


if __name__ == "__main__":
    print(f"RUNNING (version {__version__})")
    print(f"{api.site_time()}: Starting run.")
    run()
    print(f"{api.site_time()}: Run done.")
