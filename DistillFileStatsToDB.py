import argparse
import os
import pandas as pd
import math
import datetime
import numpy as np
import h5py
import matplotlib.pyplot as plt
import sqlite3
import re

def make_wide(formatter, w=150, h=36):
    """Return a wider HelpFormatter, if possible."""
    try:
        # https://stackoverflow.com/a/5464440
        # beware: "Only the name of this class is considered a public API."
        kwargs = {'width': w, 'max_help_position': h}
        formatter(None, **kwargs)
        return lambda prog: formatter(prog, **kwargs)
    except TypeError:
        warnings.warn("argparse help formatter failed, falling back.")
        return formatter


### Make a parser
parser = argparse.ArgumentParser(description='Loops over keys of an HDF5 file, derives stats for values and time, saves into a database.',
                                 formatter_class=make_wide(argparse.ArgumentDefaultsHelpFormatter))
### Add options
parser.add_argument ('infilename')
parser.add_argument ('-v', dest='debug', action="store_true", default=False,
                     help="Turn on verbose debugging. (default: F)")
parser.add_argument ('-q','--quick', dest='quick', action="store_true", default=False,
                     help="Stop after maxparams plots are rendered. (default: F)")
parser.add_argument ('--maxparams',  dest='maxparams', default=2,
                     help="Max parameters to loop if -q. (default: 2).")
parser.add_argument ('--maxrows',  dest='maxrows', default=1E2,
                     help="Max rows to process if -q. (default: 1E2).")
parser.add_argument ('--db',  dest='dbname', default='GMPSAI.db',
                     help="Name of sqlite3 database file to save caculated stats into. (default: GMPSAI.db)")


### Get the options and argument values from the parser....
options = parser.parse_args()
### ...and assign them to variables. (No declaration needed, just like bash!)
infilename  = options.infilename
if not os.path.isfile(infilename): exit ('File not found: '+infilename)
debug       = options.debug
quick       = options.quick
maxparams   = int(options.maxparams)
maxrows     = int(options.maxrows)
dbname      = options.dbname

# Open the file
infile = h5py.File(infilename, 'r')
filekeys = list (infile.keys())
infile.close()
keycount = len (filekeys)
keynum = 1
conn = sqlite3.connect(dbname)
dbcurs = conn.cursor()

# Some fiddly work to extract the start and end datetime for this file.
justthefile = infilename.split('/')[infilename.count('/')]
StartTime = re.findall(r"\d\d\d\d-\d\d-\d\d\+\d\d:\d\d:\d\d",justthefile)[0]
if debug: print ('StartTime:')
if debug: print (StartTime)
# Convert to epoch
utc_time = datetime.datetime.strptime(StartTime, '%Y-%m-%d+%H:%M:%S')
epoch_time = (utc_time - datetime.datetime(1970, 1, 1)).total_seconds()
if debug: print (epoch_time)

timedflist = []
            
# Loop over ACNET devices (hdf5 top set of keys)
for key in  filekeys:
    if quick and keynum > maxparams: break
    keynum += 1

    # Temporary: Dataframe of two columns:  values and timestamps for this param ('key')
    tempdf = pd.read_hdf(infilename, key)
    if debug: print ("  "+key+"  shape:", tempdf.shape)

    # Get the two column names of interest, the values and the times:
    cols = list (tempdf.columns)
    if debug: print (cols)
    timecolname = ''
    valcolname = ''
    for colname in cols:
        if colname.count('utc_seconds') > 0:
            timecolname = colname
        else:
            valcolname = colname
    if debug: print ('timecol = ',timecolname,'  &   valcol = ',valcolname)

    # Append timestamps column to a separate dataframe of them, for analysis outside this loop. 
    newcol = tempdf[timecolname].rename('utc_'+key, axis=1)
    timedflist.append(newcol)

    # A temporary dataframe of just the values for this parameter, for stats calulation
    valdf = tempdf[valcolname]
    if debug: print (valdf.describe())

    # Get some stats to make plots, and store for long-term time trends
    statnames = ['mode','std','min','max']
    valstatsdict = {}
    valstatsdict['mode'] = valdf.mode()[0] # Zeroth mode only
    valstatsdict['mean'] = valdf.mean()
    valstatsdict['std' ] = valdf.std()
    valstatsdict['min' ] = valdf.min()
    valstatsdict['max' ] = valdf.max()
    if debug: print (valstatsdict)

    upsertstr = 'REPLACE INTO ACNETparameterStats (epochUTCsec, paramname, statname, statval) VALUES ('
    upsertstr += str(epoch_time) +', "'+key +'", '
    for statname in statnames: 
        cmdstr = upsertstr +'"'+statname +'", '+str(valstatsdict[statname])+');'
        if debug: print (cmdstr)
        dbcurs.execute(cmdstr)
        conn.commit()
    # Done with loop over statnames.

    # Calculate sample-to-sample time deltas (units of timedel)
    timelist = tempdf[timecolname]#.sort_values() # Force to be non-negative
    timedeltas = timelist.diff() #/ timedel
    if debug: print (timedeltas.describe())
    if debug: print(type(timedeltas[1]))

    # Get some stats on the sample-to-sample time intervals (deltas)
    tdelstatsdict = {}
    tdelstatsdict['mode'] = timedeltas.mode()[0] # Zeroth mode only
    tdelstatsdict['std' ] = timedeltas.std()
    tdelstatsdict['min' ] = timedeltas.min()
    tdelstatsdict['max' ] = timedeltas.max()
    if debug: print (tdelstatsdict)

    # Also database entries for the time deltas
    # Now the paramname is like Interval_B:IMIN
    upsertstr = upsertstr.replace(key,'Interval_'+key)
    for statname in statnames: # Same stats but on consecutive entry time deltas
        cmdstr = upsertstr +'"'+statname +'", '+str(tdelstatsdict[statname])+');'
        if debug: print (cmdstr)
        dbcurs.execute(cmdstr)
        conn.commit()


# Possible that we should be using recorded values of b:LINEFRQ to correct the expected range of time deltas.

# inliermin = list(refsub_timedf.min(numeric_only=True, axis=0))
# del inliermin[-1] # Drop the final entry, which is from the line frequency
# inliermin = min(inliermin)
# inliermax = list(refsub_timedf.max(numeric_only=True, axis=0))
# del inliermax[-1] # Drop the final entry, which is from the line frequency
# inliermax = max(inliermax)
