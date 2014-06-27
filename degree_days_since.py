#!/usr/bin/python
# This file is: /usr/share/cacti/site/scripts/degree_days_since.py

import os, glob, sys, datetime

def main():
    if len(sys.argv) < 3:
        sys.stderr.write("usage: python degree_days_since.py <temp> ")
        sys.stderr.write("<start_date_time_string> [end_date_time_string]\n")
        sys.exit()

    ## PARSE THEM ARGS ##
    # Temperature
    try:
        temp = float(sys.argv[1])
    except ValueError:
        sys.stderr.write("Error parsing temperature: " + sys.argv[1] + "\n")
        sys.exit()
    
    # Start date/time
    start_date_time = parse_date_time_string(sys.argv[2])
    if not start_date_time:
        sys.exit()
        
    # End date/time (optional)
    if len(sys.argv) > 3:
        end_date_time = parse_date_time_string(sys.argv[3])
        if not end_date_time:
            sys.exit()
    else:
        end_date_time = datetime.datetime.now()
    
    ## CALCULATE AND PRINT ##
    print(degree_days_since(temp, start_date_time, end_date_time))


## PARSING FUNCTIONS ##
#######################

def parse_date_time_string(date_time_string):
    """Takes a string like 2014_12_31 and returns a datetime object.

    String may include hours and minutes, e.g. 2014_12_31_09_55
    Returns None if string cannot be parsed.
    I know I know, should probably throw an exception or something.
    """
    fields = date_time_string.split("_")
    if len(fields) < 3:
        sys.stderr.write("Error at parse_date_time_string: " +\
                date_time_string + " doesn't have enough fields.\n")
        return None
    year = int(fields[0])
    month = int(fields[1])
    day = int(fields[2])
    hour = 0
    minute = 0
    if len(fields) > 3:
        hour = int(fields[3])
    if len(fields) > 4:
        minute = int(fields[4])
    date_time = datetime.datetime(year, month, day, hour, minute)
    return date_time

def date_time_from_entry(line):
    """Returns date_time object from a line in temp log file.
    
    Data in files looks like this:
    Epoch,Date-Time,T1_C,T2_C,H_pct
    1403121302.3,2014_06_18_09_55,26.7,23.500,43.8
    """
    fields = line.strip().split(",")
    datestring = fields[1]
    return parse_date_time_string(datestring)

def temp_and_date_time_from_line(line):
    datetime = date_time_from_entry(line)
    temp = float(line.strip().split(",")[3])
    # TODO which temp now?
    return temp, datetime


## CALCULATING STUFF FUNCTIONS ##
#################################

def degree_days_since(temp, start, end):
    """Reach into Data/ folder, calculate degree days from start to end, return

    Args:
        start: a datetime object
        end: another datetime object
    
    Data in files looks like this:
    Epoch,Date-Time,T1_C,T2_C,H_pct
    1403121302.3,2014_06_18_09_55,26.7,23.500,43.8
    """
    # Get all files from start date to end date
    all_files = sorted(glob.glob('Data/*')) # should give files in order?
    relevant_files = keep_files_in_range(all_files, start, end)

    # Open each file, increment degree days for each line that falls within range
    degree_days = 0.0
    previous_date_time = None
    for tempfile in relevant_files:
        with open(tempfile, "r") as tfile:
            for line in tfile:
                if "Epoch" in line:
                    continue
                elif line_comes_before_start(line, start):
                    continue
                elif line_comes_after_end(line, end):
                    # We've reached the end
                    break
                else:
                    if not previous_date_time:
                        # (First entry)
                        previous_date_time = date_time_from_entry(line)
                        continue
                    else:
                        degree_days += calculate_degree_days(line, previous_date_time, temp)
                        previous_date_time = date_time_from_entry(line)
    return degree_days

def line_comes_before_start(line, start):
    # lines look like:
    # 1403121302.3,2014_06_18_09_55,26.7,23.500,43.8
    date = line.strip().split(",")[1]
    splitdate = date.split("_")
    year = int(splitdate[0])
    month = int(splitdate[1])
    day = int(splitdate[2])
    hour = int(splitdate[3])
    minute = int(splitdate[4])
    linedate = datetime.datetime(year, month, day, hour, minute)
    if linedate < start:
        return True
    else:
        return False

def line_comes_after_end(line, end):
    # lines look like:
    # 1403121302.3,2014_06_18_09_55,26.7,23.500,43.8
    date = line.strip().split(",")[1]
    splitdate = date.split("_")
    year = int(splitdate[0])
    month = int(splitdate[1])
    day = int(splitdate[2])
    hour = int(splitdate[3])
    minute = int(splitdate[4])
    linedate = datetime.datetime(year, month, day, hour, minute)
    if linedate > end:
        return True
    else:
        return False

def difference_in_days(old_time, new_time):
    timedelta = new_time - old_time
    difference = 0.0
    difference += timedelta.days
    difference += timedelta.seconds / 86400.0
    return difference

def calculate_degree_days(line, previous_date_time, basetemp):
    newtemp, new_date_time = temp_and_date_time_from_line(line)
    tempdiff = newtemp - basetemp
    if tempdiff <= 0:
        return 0.0
    else:
        timediff = difference_in_days(previous_date_time, new_date_time)
        return timediff * tempdiff

## FILE STUFF FUNCTIONS ##
##########################

def keep_files_in_range(files, start, end):
    keepers = []
    for filename in files:
        if filename_within_range(filename, start, end):
            keepers.append(filename)
    return keepers

def filename_within_range(filename, start, end):
    """Return bool for whether file falls between start and end (inclusive).

    Filename formats should be 'Data/2014_06_19.csv'
    """
    date = filename.split("/")[1].split(".")[0]
    splitdate = date.split("_")
    year = int(splitdate[0])
    month = int(splitdate[1])
    day = int(splitdate[2])
    filedate = datetime.datetime(year, month, day)
    startday = datetime.datetime(start.year, start.month, start.day)
    endday = datetime.datetime(end.year, end.month, end.day)
    if filedate < startday or filedate > endday:
        return False
    else:
        return True


####################################################################################

if __name__ == '__main__':
    main()