"""Runs 'zinbot."""
__author__ = "Tamzin Hadasa Kelly"
__copyright__ = "Copyright 2021, Tamzin Hadasa Kelly"
__license__ = "The MIT License"
__email__ = "coding@tamz.in"

import patrol.newpages

def run():
    """Run the bot's tasks that are currently approved / in trial."""
    patrol.newpages.checkqueue()  # pre-trial

if __name__ == "__main__":
    print("RUNNING")
    run()
