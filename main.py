"""Runs 'zinbot."""
__author__ = "Tamzin Hadasa Kelly"
__copyright__ = "Copyright 2021, Tamzin Hadasa Kelly"
__license__ = "The MIT License"
__email__ = "coding@tamz.in"
__version__ = "1.4.2"

import sys
import time

import api
import antivandalism.massrollback
import pagetriage.newpages


def run() -> None:
    """Run the bot's tasks that are currently approved / in trial."""
    pagetriage.newpages.checkqueue()  # trial


if __name__ == "__main__":
    print(f"RUNNING (version {__version__})")
    try:
        if sys.argv[1] == "run":
            while True:
                run()
       	        print("Run done. Sleeping.")
                time.sleep(1800)
        elif sys.argv[1] == "rollback":
            print(api.rollback(sys.argv[2]))
        elif sys.argv[1] == "massrollback":
            antivandalism.massrollback.main(file_name=sys.argv[2],
                                           summary=sys.argv[3],
                                           markbot=sys.argv[4] == 'markbot')
    except IndexError:
       sys.exit()
