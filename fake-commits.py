#!/bin/env python
# PYTHON_ARGCOMPLETE_OK
# -*- coding: utf-8 -*-

""" fake-commits.py:  Create fake git commits, e.g. to mislead the GitHub Contributions Calendar.
    2023-12-01, MvdS: initial version.
"""


import colored_traceback
colored_traceback.add_hook()

import argparse
import argcomplete

import numpy as np
from pathlib import Path
import datetime as dt
import pytz as tz
from git import Repo  # Pip install GitPython
import subprocess

import sluyspy.numerics as snum     # Pip install sluyspy
import astrotool.date_time as asdt  # Pip install astrotool


def main():
    """Main function."""
    
    # Get command-line arguments:
    args = get_cli_arguments()
    
    if args.number<1: exit(1)
    if args.random:
        ncommits = snum.nint(max(np.random.normal(args.number,2*np.sqrt(args.number),1)[0],1))
    else:
        ncommits = args.number
    if args.verbosity > 0: print('Creating %i fake commits per day.' % ncommits)
    
    path = '.'
    repo = Repo.init(path).git
    index = Repo.init(path).index
    
    file1 = Path('file1')
    file2 = Path('file2')
    filet = Path('filet')
    
    
    date = dt.date.today()
    times = np.sort(np.random.uniform(0,24,ncommits))
    
    for time in times:  # ~1-1.5s for 100 commits
        # Swap file1 and file2:
        file1.rename(filet)
        file2.rename(file1)
        filet.rename(file2)
        
        timestr = asdt.hms_str_from_time(time)
        dtm = dt.datetime.strptime(date.strftime('%Y-%0m-%0d '+timestr), '%Y-%m-%d %H:%M:%S').astimezone()
        if args.verbosity>1: print('Commit time: ', dtm)
        
        # Commit changes:
        repo.add('file1')
        repo.add('file2')
        index.commit(message='Commit', author_date=dtm, commit_date=dtm, skip_hooks=True)
    
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
    
    parser.add_argument('-n', '--number',      type=int, default=10,      help='number of daily commits to create')
    parser.add_argument('-r', '--random',      action='store_false',      help='do NOT use a random number around the specified number of commits')  # Default = True
    
    parser.add_argument('-f', '--first-date',  type=str, default='today', help='first date to create commits for')
    parser.add_argument('-l', '--last-date',   type=str, default='today', help='last date to create commits for')
    
    parser.add_argument('-v', '--verbosity', action='count', default=0, help='increase output verbosity')  # Counts number of occurrences
    
    argcomplete.autocomplete(parser)
    args = parser.parse_args()
    
    return args


if __name__ == '__main__':
    main()

