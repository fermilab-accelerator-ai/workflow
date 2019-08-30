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
parser.add_argument ('-v', dest='debug', action="store_true", default=False,
                     help="Turn on verbose debugging. (default: F)")
parser.add_argument ('-q','--quick', dest='quick', action="store_true", default=False,
                     help="Stop after maxparams plots are rendered. (default: F)")
parser.add_argument ('--maxparams',  dest='maxparams', default=2,
                     help="Max parameters to loop if -q. (default: 2).")
parser.add_argument ('--nopdf', dest='nopdf', action="store_true", default=False,
                     help="Skip plot making, save no plot file. (default: F)")
parser.add_argument ('--outdir',  dest='outdir', default='',
                     help="Directory to write final output file. (default: pwd)")
parser.add_argument ('-o', '--out',  dest='outfilename', default='TimeTrendsPlots.pdf',
                     help="Filename to write final output file. (default: )")
parser.add_argument ('--db',  dest='dbname', default='GMPSAI.db',
                     help="Name of sqlite3 database file to save caculated stats into. (default: GMPSAI.db)")


### Get the options and argument values from the parser....
options = parser.parse_args()
### ...and assign them to variables. (No declaration needed, just like bash!)
debug       = options.debug
nopdf     = options.nopdf
outdir      = options.outdir
quick       = options.quick
maxparams    = int(options.maxparams)
paramcount = 1
outfilename = options.outfilename
dbname      = options.dbname

bincount = 500
conn = sqlite3.connect(dbname)
dbcurs = conn.cursor()

if not nopdf: pdf = PdfPages(outdir+outfilename)
paramsresults = dbcurs.execute("SELECT DISTINCT paramname from ACNETparameterStats;")
paramnames = []
for paramresult in paramsresults:
    if debug: print (paramresult)
    param = paramresult[0]
    paramnames.append(param)
    if debug: print(param)

# Which stats have we got entries for, for each param?
for param in paramnames:
    if quick and paramcount > maxparams: break
    paramcount += 1
    statsresults = dbcurs.execute('SELECT DISTINCT statname FROM ACNETparameterStats WHERE paramname LIKE "{}";'.format(param))
    datadict = {}
    for statresult in statsresults:
        if debug: print (statresult)
        stat = statresult[0]
        if debug: print (param, stat)
        # Make a dataframe for the time series of values
        slctstr = 'SELECT statval, epochUTCsec FROM ACNETparameterStats WHERE paramname LIKE "{}" AND statname LIKE "{}"'.format(param,stat)
        slctstr += ' ORDER BY epochUTCsec;'
        df = pd.read_sql_query(slctstr, conn)
        datadict[stat] = df
        if debug: print (df)

    plt.figure(figsize=(8, 6))
    axdict = {}
    main = 'mode'
    #ax = datadict[main].plot(kind='scatter', x='epochUTCsec', y='statval', label=main, style='-o')
    ax = datadict[main].plot.line(x='epochUTCsec', y='statval', label=main, style='-')
    datadict['min'].plot.line(x='epochUTCsec', y='statval', label='min', ax=ax, style='-o')
    datadict['max'].plot.line(x='epochUTCsec', y='statval', label='max', ax=ax, style='-')

    #for key in datadict.keys():
    #    if key == main or key =='std': continue
    #    axdict[key] = datadict[key].plot.line(x='epochUTCsec', y='statval', label=key, ax=ax, style='-')

    plt.savefig(param+".png")

    #plt.text( 0.70, 0.85, textstr, transform=plt.gca().transAxes) #Plot relative to bottom left at 0,0 
    #plt.xlabel('Consecutive time deltas [seconds]')
    #daterangestr = justthefile.split('From_MLrn_')[1].rstrip('.h5.pdf')
    #plt.title(valcolname + '\n' + daterangestr)
    
        

