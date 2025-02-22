#!/bin/env python
# PYTHON_ARGCOMPLETE_OK
# -*- coding: utf-8 -*-
# 
# SPDX-License-Identifier: EUPL-1.2
#  
#  Copyright (c) 2023-2025  Marc van der Sluys - Nikhef/Utrecht University - marc.vandersluys.nl
#   
#  Create fake git commits, e.g. to mislead the GitHub Contributions Calendar.
#  See: https://github.com/MarcvdSluys/fake-commits
#   
#  This is free software: you can redistribute it and/or modify it under the terms of the European Union
#  Public Licence 1.2 (EUPL 1.2).  This software is distributed in the hope that it will be useful, but
#  WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
#  PURPOSE.  See the EU Public Licence for more details.  You should have received a copy of the European
#  Union Public Licence along with this code.  If not, see <https://www.eupl.eu/1.2/en/>.


""" fake-commits.py:  Create fake git commits, e.g. to mislead the GitHub Contributions Calendar.
    2023-12-01, MvdS: initial version.
    2025-02-22, MvdS: help me remember how to use this.
"""


import colored_traceback            # pip install colored_traceback
colored_traceback.add_hook()

import argparse
import argcomplete                  # pip install argcomplete

import numpy as np                  # pip install numpy
from pathlib import Path
import datetime as dt
from dateutil import rrule          # pip install dateutil
from git import Repo                # pip install GitPython
import subprocess

import sluyspy.cli as scli          # pip install sluyspy
import sluyspy.numerics as snum
import astrotool.date_time as asdt  # pip install astrotool


# Define your git repo:
path  = '.'
repo  = Repo.init(path).git
index = Repo.init(path).index


# Specify two tiny files, and a temporary file.
# You need to create file1 and file2 yourself with minimal but different content.
# I use nearly empty files with only '1' and '2' in them.
file1 = Path('file1')  # e.g. echo 1 > file1
file2 = Path('file2')  # e.g. echo 2 > file2
filet = Path('filet')



def main():
    """Main function."""
    
    # Get command-line arguments:
    args = get_cli_arguments()
    
    # Sort out the date range from the cli arguments:
    first_date, last_date = get_date_range(args)
    
    
    # Loop over date range:
    for date in rrule.rrule(rrule.DAILY, dtstart=first_date, until=last_date):
        
        # Create the number of fake commits specified in the cli arguments for the given date:
        create_fake_commits(date, args)
    
    
    # Collect garbage in git repo (gc is not in GitPython):
    if args.verbosity>0:
        print()
        print('Tidying up...')
    if args.live:
        subprocess.run(['git', 'gc', '--aggressive', '--prune=now'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
    # Push to remote:
    if not args.no_push:
        if args.verbosity>0: print('Pushing to remote...')
        if args.live: subprocess.run(['git', 'push'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
    # Report a dry run:
    if not args.live:
        if args.verbosity>0: print()
        # Even warn with --quiet, since no-one will want to run a cron job with that option:
        print('NOTE: This was a dry run; I did not commit anything.  Specify -L or --live to go LIVE once you are satisfied.')
        if args.verbosity>0: print()
        
    exit(0)
    
    
def get_cli_arguments():
    """Get the command-line arguments.
    
    Returns:
      (struct):  Struct containing command-line arguments.
    """
    
    # Parse command-line arguments:
    parser = argparse.ArgumentParser(description='Create fake git commits, e.g. to mislead the GitHub Contributions Calendar.',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)  # Use capital, period, add default values
    
    # Required argument:
    parser.add_argument('number', type=float, help='number of daily commits to create (e.g. 4)')
    
    # Optional arguments:
    parser.add_argument('-r', '--random',      type=float, default=1,     help='amount of randomisation ("number of standard deviations) around the specified number of commits (0=no randomisation)')
    
    parser.add_argument('-f', '--first-date',  type=str, default='today', help='first date to create commits for (YYYY-MM-DD)')
    parser.add_argument('-l', '--last-date',   type=str, default=None,    help='last date to create commits for (YYYY-MM-DD, defaults to first date)')
    
    parser.add_argument('-L', '--live',        action='store_true', help='go LIVE: perform the actual COMMITS')  # Default = False
    parser.add_argument('-p', '--no-push',     action='store_true', help='do NOT push after committing')     # Default = False
    
    # Mutually exclusive arguments:
    verb  = parser.add_mutually_exclusive_group()
    verb.add_argument('-v', '--verbosity',   action='count', default=1, help='increase output verbosity')  # Counts number of occurrences
    verb.add_argument('-q', '--quiet',       action='store_true', help='no output')     # Default = False
    
    argcomplete.autocomplete(parser)
    args = parser.parse_args()
    
    # Check and sort out CLI options:
    if args.quiet: args.verbosity = 0
    if args.number<=0: scli.error('The number of commits must be positive')
    if args.random<=0: scli.error('The randomisation must be positive')
    
    if args.verbosity>0:
        print('Settings:')
        print('- mean number of commits per day:        %0.2f' % (args.number))
        print('- randomisation in standard deviations:  %0.2f' % (args.random))
        
    return args


def get_date_range(args):
    """Sort out the date range from the command-line arguments.
    
    Parameters:
      args (struct):  Argparse struct with command-line arguments.
    
    Returns:
      (tuple):  tuple containing two datetime.dates with the first and last date.
    """
    
    if args.first_date == 'today':
        first_date = dt.date.today()
    else:
        try:
            first_date = dt.datetime.strptime(args.first_date, '%Y-%m-%d').date()
        except Exception as e:
            scli.error('First date should be a string with the format YYYY-MM-DD: '+args.first_date+': '+str(e))
    if args.last_date is None:
        last_date = first_date
    else:
        try:
            last_date = dt.datetime.strptime(args.last_date, '%Y-%m-%d').date()
        except Exception as e:
            scli.error('Last date should be a string with the format YYYY-MM-DD: '+args.last_date+': '+str(e))
    
    # Print date range (part of Settings block):
    if args.verbosity>0:
        if first_date == last_date:
            print('- date for commits:                      %s' % (first_date.strftime('%A %Y-%m-%d')))
        else:
            print('- date range for commits:                %s - %s' % (first_date.strftime('%A %Y-%m-%d'), last_date.strftime('%A %Y-%m-%d')))
        print()
        
    if first_date > last_date: scli.error('The first date must be before the last date')
    
    return first_date, last_date


def create_fake_commits(date, args):
    """Create the number of fake commits specified in the cli arguments for the given date.
    
    Parameters:
      date (datetime.date):  Date to create commits for.
      args (struct):  Argparse struct with cli arguments, a.o. the number of commits.
    """
    
    # Draw a single (1) random number from a Gaussian distribution with mean and width specified by the cli
    # arguments:
    mean       = args.number
    sqrt_mean  = np.sqrt(mean)
    width      = args.random*sqrt_mean
    ncommits   = np.random.normal(mean, width, 1)[0]  # Make it a scalar
    ncommits   = max(snum.nint(ncommits),0)  # Make it an integer
    # ncommits   = snum.nint(max(round(ncommits,0), sqrt_mean))  # Make it an integer, not too small
    
    # Report the number of commits for this date:
    if args.verbosity > 0:
        if args.verbosity > 1: print()
        print('Creating %i fake commits for %s' % (ncommits, date.strftime('%A %Y-%m-%d')), end='')
        if args.verbosity > 1:
            print(':')
        else:
            print('.')
    
    # Create random times, sort them and swap files and commit the result for each time:
    times = np.sort(np.random.uniform(0,24,ncommits))
    for time in times:  # ~1-1.5s for 100 commits
        # Swap file1 and file2:
        file1.rename(filet)
        file2.rename(file1)
        filet.rename(file2)
        
        timestr = asdt.hms_str_from_time(time)
        dtm = dt.datetime.strptime(date.strftime('%Y-%0m-%0d '+timestr), '%Y-%m-%d %H:%M:%S').astimezone()
        if args.verbosity>1: print('  commit time:', dtm)
        
        if args.live:  # Go LIVE and perform the actual COMMIT:
            repo.add('file1')
            repo.add('file2')
            index.commit(message='Commit', author_date=dtm, commit_date=dtm, skip_hooks=True)
    
    return


if __name__ == '__main__':
    main()

