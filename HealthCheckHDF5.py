import argparse
import os
import pandas as pd
import math
import datetime
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
import h5py
import matplotlib.pyplot as plt
import sqlite3
import re

### Make a parser
parser = argparse.ArgumentParser()
### Add options
parser.add_argument ('infilename')
parser.add_argument ('-v', dest='debug', action="store_true", default=False,
                     help="Turn on verbose debugging. (default: F)")
parser.add_argument ('-q','--quick', dest='quick', action="store_true", default=False,
                     help="Stop after maxparams plots are rendered. (default: F)")
parser.add_argument ('--noplots', dest='noplots', action="store_true", default=False,
                     help="Skip plot making, save no plot file. (default: F)")
parser.add_argument ('--nodb', dest='nodb', action="store_true", default=False,
                     help="Skip database entry making. (default: F)")
parser.add_argument ('--maxparams',  dest='maxparams', default=2,
                     help="Max parameters to loop if -q. (default: 2).")
parser.add_argument ('--outdir',  dest='outdir', default='',
                     help="Directory to write final output file. (default: pwd)")
parser.add_argument ('--db',  dest='dbname', default='GMPSAI.db',
                     help="Name of sqlite3 database file to save caculated stats into. (default: GMPSAI.db)")
parser.add_argument ('--find',  dest='checkfor', default='',
                     help="String to check for among the hdf5 file's top layer keys.")


### Get the options and argument values from the parser....
options = parser.parse_args()
### ...and assign them to variables. (No declaration needed, just like bash!)
infilename  = options.infilename
if not os.path.isfile(infilename): exit ('File not found: '+infilename)
debug       = options.debug
noplots     = options.noplots
nodb        = options.nodb
outdir      = options.outdir
quick       = options.quick
maxparams    = options.maxparams
justthefile = infilename.split('/')[infilename.count('/')]
outfilename = 'QualityChecks'+justthefile+'.pdf'
dbname      = options.dbname
checkfor    = options.checkfor

# Open the file
infile = h5py.File(infilename, 'r')
filekeys = list (infile.keys())
infile.close()
keycount = len (filekeys)
keynum = 1
timedel = 1./30.
bincount = 500
if not nodb:
    conn = sqlite3.connect(dbname)
    dbcurs = conn.cursor()

# Are we just checking for a certain substring in the keys? 
if checkfor != '':
    foundkeys = []
    for key in filekeys:
        if key.count(checkfor) >0: foundkeys.append(key)
    if len(foundkeys) >0: 
        print (infilename+'\n  contained matching keys:',foundkeys)
    else: print (infilename+' -- No matching keys.')
    exit()

StartTime = re.findall(r"\d\d\d\d-\d\d-\d\d\+\d\d:\d\d:\d\d",justthefile)[0]
if debug: print ('StartTime:')
if debug: print (StartTime)
# Convert to epoch
utc_time = datetime.datetime.strptime(StartTime, '%Y-%m-%d+%H:%M:%S')
epoch_time = (utc_time - datetime.datetime(1970, 1, 1)).total_seconds()
if debug: print (epoch_time)

if not noplots: pdf = PdfPages(outdir+outfilename)
# Loop over ACNET devices (hdf5 top set of keys)
for key in  filekeys:
    if quick and keynum > maxparams: break
    keynum += 1
    tempdf = pd.read_hdf(infilename, key)
    print ("  "+key)
    if debug: print (tempdf.shape)
    cols = list (tempdf.columns)
    if debug: print (cols)
    # Get the two column names of interest:
    timecolname = ''
    valcolname = ''
    for colname in cols:
        if colname.count('utc_seconds') > 0:
            timecolname = colname
        else:
            valcolname = colname
    if debug: print ('timecol = ',timecolname,'  &   valcol = ',valcolname)
    
    valdf = tempdf[valcolname]
    if debug: print (valdf.describe())

    # Get some stats to make plots, and store for long-term time trends
    statnames = ['mode','std','min','max']
    valstatsdict = {}
    valstatsdict['mode'] = valdf.mode()[0] # Zeroth mode only
    valstatsdict['std' ] = valdf.std()
    valstatsdict['min' ] = valdf.min()
    valstatsdict['max' ] = valdf.max()
    if debug: print (valstatsdict)

    if not nodb:
        upsertstr = 'REPLACE INTO ACNETparameterStats (epochUTCsec, paramname, statname, statval) VALUES ('
        upsertstr += str(epoch_time) +', "'+key +'", '
        for statname in statnames: 
            cmdstr = upsertstr +'"'+statname +'", '+str(valstatsdict[statname])+');'
            if debug: print (cmdstr)
            dbcurs.execute(cmdstr)
            conn.commit()
    
    # Calculate sample-to-sample time deltas (units of timedel)
    timelist = tempdf[timecolname]#.sort_values()
    timedeltas = timelist.diff() #/ timedel
    if debug: print (timedeltas.describe())
    if debug: print(type(timedeltas[1]))

    # Get some stats to make plots, and store for long-term time trends
    tdelstatsdict = {}
    tdelstatsdict['mode'] = timedeltas.mode()[0] # Zeroth mode only
    tdelstatsdict['std' ] = timedeltas.std()
    tdelstatsdict['min' ] = timedeltas.min()
    tdelstatsdict['max' ] = timedeltas.max()
    if debug: print (tdelstatsdict)

    if not nodb: 
        # Also database entries for the time deltas
        # Now the paramname is like Interval_B:IMIN
        upsertstr = upsertstr.replace(key,'Interval_'+key)
        for statname in statnames: # Same stats but on consecutive entry time deltas
            cmdstr = upsertstr +'"'+statname +'", '+str(tdelstatsdict[statname])+');'
            if debug: print (cmdstr)
            dbcurs.execute(cmdstr)
            conn.commit()

    # Nicely formatted strings for human-friendly display
    modstr = '{:.3f}'.format(tdelstatsdict['mode'] )
    stdstr = '{:.3f}'.format(tdelstatsdict['std' ] )
    minstr = '{:.3f}'.format(tdelstatsdict['min' ] )
    maxstr = '{:.3f}'.format(tdelstatsdict['max' ] )

    textstr = "Mode: "+modstr
    textstr += '\nRange: ('+ minstr +', '+ maxstr+')'
    textstr += "\nStdDev: "+ stdstr
    if debug: print (textstr)
    if not noplots:
        plt.figure(figsize=(8, 6))
        binheights, binctrs, _ = plt.hist(timedeltas, bins=bincount, log=True, 
                                          range = (1.1*timedeltas.min(), 1.1*timedeltas.max()) )
        plt.text( 0.70, 0.85, textstr, transform=plt.gca().transAxes) #Plot relative to bottom left at 0,0 
        plt.xlabel('Consecutive time deltas [seconds]')
        daterangestr = justthefile.split('From_MLrn_')[1].rstrip('.h5.pdf')
        plt.title(valcolname + '\n' + daterangestr)
        pdf.savefig()
        

