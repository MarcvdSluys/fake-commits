#!/bin/env python
# PYTHON_ARGCOMPLETE_OK
# -*- coding: utf-8 -*-

""" create-commits.py:  Create fake git commits, e.g. to mislead the GitHub Contributions Calendar.
    2023-12-01, MvdS: initial version.
"""


import colored_traceback
colored_traceback.add_hook()

import argparse
import argcomplete

from pathlib import Path
import datetime as dt
import pytz as tz
from git import Repo  # Pip install GitPython
import subprocess


def main():
    """Main function."""
    
    # Get command-line arguments:
    get_cli_arguments()
    
    path = '.'
    repo = Repo.init(path).git
    index = Repo.init(path).index
    
    file1 = Path('file1')
    file2 = Path('file2')
    filet = Path('filet')
    
    for commit in range(100):  # ~1-1.5s for 100 commits
        # Swap file1 and file2:
        file1.rename(filet)
        file2.rename(file1)
        filet.rename(file2)
        
        # Commit changes
        now = dt.datetime.utcnow().astimezone(tz.utc)
        repo.add('file1')
        repo.add('file2')
        index.commit(message='Commit', author_date=now, commit_date=now, skip_hooks=True)
    
    # Collect garbage in git repo (gc is not in GitPython):
    subprocess.run(['git', 'gc', '--aggressive', '--prune=now'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    exit(0)
    
    
def get_cli_arguments():
    """Get the command-line arguments.
    
    Returns:
      (struct):  Struct containing command-line arguments.
    """
    
    # Parse command-line arguments:
    parser = argparse.ArgumentParser(description='Create fake git commits, e.g. to mislead the GitHub Contributions Calendar.',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)  # Use capital, period, add default values
    
    argcomplete.autocomplete(parser)
    args = parser.parse_args()
    
    return args


if __name__ == '__main__':
    main()

