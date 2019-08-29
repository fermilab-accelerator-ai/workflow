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
parser.add_argument ('--maxparams',  dest='maxparams', default=2,
                     help="Max parameters to loop if -q. (default: 2).")
parser.add_argument ('--outdir',  dest='outdir', default='',
                     help="Directory to write final output file. (default: pwd)")
parser.add_argument ('--db',  dest='dbname', default='GMPSAI.db',
                     help="Name of sqlite3 database file to save caculated stats into. (default: GMPSAI.db)")


### Get the options and argument values from the parser....
options = parser.parse_args()
### ...and assign them to variables. (No declaration needed, just like bash!)
infilename  = options.infilename
if not os.path.isfile(infilename): exit ('File not found: '+infilename)
debug       = options.debug
noplots     = options.noplots
outdir      = options.outdir
quick       = options.quick
maxparams    = options.maxparams
justthefile = infilename.split('/')[infilename.count('/')]
outfilename = 'QualityChecks'+justthefile+'.pdf'
dbname      = options.dbname

# Open the file
infile = h5py.File(infilename, 'r')
filekeys = list (infile.keys())
infile.close()
keycount = len (filekeys)
keynum = 1
timedel = 1./30.
bincount = 500
conn = sqlite3.connect(dbname)
dbcurs = conn.cursor()

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
    #need this? jmsj 2019.08.29# f = h5py.File(infilename, 'r')
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
    # Calculate sample-to-sample time deltas (units of timedel)
    timelist = tempdf[timecolname]#.sort_values()
    timedeltas = timelist.diff() #/ timedel
    if debug: print (timedeltas.describe())
    if debug: print(type(timedeltas[1]))

    # Nicely formatted strings for human-friendly display
    modstr = '{:.3f}'.format(statsdict['mode'] )
    stdstr = '{:.3f}'.format(statsdict['std' ] )
    minstr = '{:.3f}'.format(statsdict['min' ] )
    maxstr = '{:.3f}'.format(statsdict['max' ] )

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
        

