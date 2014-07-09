#!/usr/bin/python
# This file is: /usr/share/cacti/site/scripts/degree_days_since.py

import os, glob, sys, datetime

def main():
    if len(sys.argv) < 4:
        sys.stderr.write("usage: python degree_days_since.py <temp> <ambient or probe> ")
        sys.stderr.write("<start_date_time_string> [end_date_time_string]\n")
        sys.exit()

    ## PARSE THEM ARGS ##
    # Temperature
    try:
        temp = float(sys.argv[1])
    except ValueError:
        sys.stderr.write("Error parsing temperature: " + sys.argv[1] + "\n")
        sys.exit()

    # Ambient or Probe
    if sys.argv[2] == "ambient":
        ambient = True
    elif sys.argv[2] == "probe":
        ambient = False
    else:
        sys.stderr.write("Error parsing arguments. Second argument should be 'ambient' or 'probe'.\n")
        sys.exit()
    
    # Start date/time
    start_date_time_string = sys.argv[3]
        
    # End date/time (optional)
    if len(sys.argv) > 4:
        end_date_time_string = sys.argv[4]
    else:
        end_date_time_string = ""
    
    ## CALCULATE AND PRINT ##
    print(degree_days_since(temp, ambient, start_date_time_string, end_date_time_string))
    return degree_days_since(temp, ambient, start_date_time_string, end_date_time_string)


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

def temp_and_date_time_from_line(line, ambient):
    datetime = date_time_from_entry(line)
    if ambient:
        temp = float(line.strip().split(",")[2])
    else:
        temp = float(line.strip().split(",")[3])
    return temp, datetime

def datestring_from_filename(filename):
    return filename.split("/")[-1].split(".")[0]

## CALCULATING STUFF FUNCTIONS ##
#################################

def degree_days_since(temp, ambient, startstring, endstring):
    """Reach into Data/ folder, calculate degree days from start to end, return

    Args:
        temp: base temperature for calculating degree days
        ambient: a boolean; if True, use ambient temp, if False use probe
        startstring: start time in YYYY_MM_DD_HH_MM format
        end: optional end time in same format
    
    Data in files looks like this:
    Epoch,Date-Time,T1_C,T2_C,H_pct
    1403121302.3,2014_06_18_09_55,26.7,23.500,43.8

    Returns an error string if something goes wrong.
    """
    start = parse_date_time_string(startstring)
    if not start:
        return "Error parsing start date string: " + startstring
    if endstring:
        end = parse_date_time_string(endstring)
        if not end:
            return "Error parsing end date string: " + endstring
    else:
        end = datetime.datetime.now()

    # Get all files from start date to end date
    relevant_files = get_files_from_start_to_end("Data", start, end)

    # Make sure that first file matches start and last file matches end
    if not filename_matches_date(relevant_files[0], start):
        return "Error retrieving files. Your start date was " + startstring +\
                " and the earliest file found was " + relevant_files[0]
    if not filename_matches_date(relevant_files[-1], end):
        if not endstring:
            endstring = str(end.year) + "_" + str(end.month) + "_" + str(end.day)
        return "Error retrieving files. Your end date was " + endstring +\
                " and the latest file found was " + relevant_files[0]


    # Make sure there are no gaps in relevant files
    if not no_missing_files(relevant_files):
        return "Error with Data files: missing a file in " + str(relevant_files)

    # Open each file, increment degree days for each line that falls within range
    # TODO make sure no gaps in readings!!!
    degree_days = 0.0
    previous_date_time = None
    for tempfile in relevant_files:
        with open(tempfile, "r") as tfile:
            for line in tfile:
                if "Epoch" in line:
                    # Header line
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
                        degree_days += calculate_degree_days(line, previous_date_time, temp, ambient)
                        previous_date_time = date_time_from_entry(line)
    return degree_days

def filename_matches_date(filename, date):
    """Returns True if year/month/day of filename matches datetime object."""
    # Filename looks like 'Data/2014_06_18.csv'
    file_datestring = filename.split("/")[-1].split(".")[0] # now it's '2014_06_18'
    file_date = parse_date_time_string(file_datestring)
    if date.year != file_date.year:
        return False
    elif date.month != file_date.month:
        return False 
    elif date.day != file_date.day:
        return False
    else:
        return True

def no_missing_files(files):
    """Assumes files are already sorted."""
    if len(files) == 1:
        return True
    first_datestring = files[0].split("/")[-1].split(".")[0]
    current_date = parse_date_time_string(first_datestring)
    for filename in files[1:]:
        this_datestring = filename.split("/")[-1].split(".")[0]
        this_date = parse_date_time_string(this_datestring)
        diff = this_date - current_date
        if diff.days != 1:
            return False
        current_date = this_date
    return True


def line_comes_before_start(line, start):
    # lines look like:
    # 1403121302.3,2014_06_18_09_55,26.7,23.500,43.8
    date = line.strip().split(",")[1]
    linedate = parse_date_time_string(date)
    if linedate < start:
        return True
    else:
        return False

def line_comes_after_end(line, end):
    # lines look like:
    # 1403121302.3,2014_06_18_09_55,26.7,23.500,43.8
    date = line.strip().split(",")[1]
    linedate = parse_date_time_string(date)
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

def calculate_degree_days(line, previous_date_time, basetemp, ambient):
    newtemp, new_date_time = temp_and_date_time_from_line(line, ambient)
    tempdiff = newtemp - basetemp
    if tempdiff <= 0:
        return 0.0
    else:
        timediff = difference_in_days(previous_date_time, new_date_time)
        return timediff * tempdiff

## FILE STUFF FUNCTIONS ##
##########################

def get_files_from_start_to_end(path, start, end):
    all_files = sorted(glob.glob(path + '/*')) # should give files in order?
    relevant_files = keep_files_in_range(all_files, start, end)
    return relevant_files

def get_file_closest_to_datetime(path, date):
    # TODO set a reasonable minimum -- this will give you a file
    # from weeks ago ...
    MINIMUM_TIMEDELTA = datetime.timedelta.max
    all_files = sorted(glob.glob(path + '/*')) # should give files in order?
    smallest_timedelta = datetime.timedelta.max
    closest_file = None
    for filename in all_files:
        file_datestring = filename.split("/")[-1].split(".")[0]
        file_datetime = parse_date_time_string(file_datestring)
        diff = abs(file_datetime - date)
        if diff < smallest_timedelta:
            smallest_timedelta = diff
            closest_file = filename
    # Make sure closest file is close enough
    closest_datestring = datestring_from_filename(closest_file)
    closest_datetime = parse_date_time_string(closest_datestring)
    diff = abs(date - closest_datetime)
    if diff < MINIMUM_TIMEDELTA:
        return closest_file
    else:
        return "Sorry, couldn't find any files close enough to the date provided."

def keep_files_in_range(files, start, end):
    keepers = []
    for filename in files:
        if filename_within_range(filename, start, end):
            keepers.append(filename)
    return keepers

def filename_within_range(filename, start, end):
    """Return bool for whether file falls between start and end days (inclusive).

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
