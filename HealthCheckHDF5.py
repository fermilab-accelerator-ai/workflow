import argparse
import pandas as pd
import math
import datetime
import numpy as np
from matplotlib.backends.backend_pdf import PdfPages
import h5py
import matplotlib.pyplot as plt

### Make a parser
parser = argparse.ArgumentParser(description="usage: %prog [options] <input file.ROOT> \n")
### Add options
parser.add_argument ('infilename')
parser.add_argument ('-v', dest='debug', action="store_true", default=False,
                     help="Turn on verbose debugging.")
parser.add_argument ('-q', dest='quick', action="store_true", default=False,
                     help="Stop after maxplots plots are rendered.")
parser.add_argument ('--infilename',  dest='infilename', default='',
                     help="Input filename.")
parser.add_argument ('--outdir',  dest='outdir', default='',
                     help="Directory to write final output file.")
parser.add_argument ('--maxplots',  dest='maxplots', default=2,
                     help="Maximimum number of parameters to loop over.")

### Get the options and argument values from the parser....
options = parser.parse_args()
### ...and assign them to variables. (No declaration needed, just like bash!)
infilename  = options.infilename
debug       = options.debug
outdir      = options.outdir
quick       = options.quick
maxplots    = options.maxplots
outfilename = 'QualityChecks.pdf'

# Open the file
infile = h5py.File(infilename, 'r+')
colcount = len(infile.keys())
plotnum = 1
timedel = 1./30.
bincount = 500
with PdfPages(outfilename) as pdf:
    # Loop over ACNET devices (hdf5 top set of keys)
    for key in infile.keys():
        tempdf = pd.read_hdf(infilename, key)
        if debug: print ("  "+key)
        if debug: print (tempdf.shape)
        cols = tempdf.columns.to_list()
        if debug: print (cols)
        # Get the two column names of interest:
        timecol = ''
        valcol = ''
        for col in cols:
            if col.count('utc_seconds') > 0:
                timecol = col
            else:
                valcol = col
        # Calculate sample-to-sample time deltas (units of timedel)
        timedeltas = tempdf[timecol].diff() #/ timedel
        if debug: print (timedeltas.describe())
        plt.figure(figsize=(8, 6))
        binheights, binctrs, _ = plt.hist(timedeltas, bins=bincount, log=True,
                                          range = (1.1*timedeltas.min(), 1.1*timedeltas.max()) )
        #fig = timedeltas.plot.hist(log=True, bins=bincount)
        print(type(timedeltas[1]))
        mode = timedeltas.mode()
        #print (str(binheights.max())+", ",str(mode))
        print (str(mode))
        plt.text(mode, binheights.max(), "Mode: "+str(mode))
        plt.xlabel('Consecutive time deltas (1 s ticks)')
        plt.title(col)
        pdf.savefig()
        #plt.close()
        if quick and plotnum >= maxplots: break
        plotnum += 1
        

