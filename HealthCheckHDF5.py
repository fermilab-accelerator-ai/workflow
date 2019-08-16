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
justthefile = infilename.split('/')[infilename.count('/')]
outfilename = 'QualityChecks'+justthefile+'.pdf'

# Open the file
infile = h5py.File(infilename, 'r')
filekeys = list (infile.keys())
infile.close()
keycount = len (filekeys)
plotnum = 1
timedel = 1./30.
bincount = 500
with PdfPages(outfilename) as pdf:
    # Loop over ACNET devices (hdf5 top set of keys)
    for key in  filekeys:
        f = h5py.File(infilename, 'r')
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
        plt.figure(figsize=(8, 6))
        binheights, binctrs, _ = plt.hist(timedeltas, bins=bincount, log=True, 
                                          range = (1.1*timedeltas.min(), 1.1*timedeltas.max()) )
        #fig = timedeltas.plot.hist(log=True, bins=bincount)
        if debug: print(type(timedeltas[1]))
        mode = timedeltas.mode()[0]
        if debug: print (str(mode))
        modestr = '{:.3f}'.format(timedeltas.mode()[0] )
        textstr = "Mode: "+modestr
        maxstr = '{:.3f}'.format(timedeltas.max())
        minstr = '{:.3f}'.format(timedeltas.min())
        textstr += '\nRange: ('+ minstr +', '+ maxstr+')'
        stdstr = '{:.3f}'.format(timedeltas.std())
        textstr += "\nStdDev: "+ stdstr
        plt.text( 0.70, 0.85, textstr, transform=plt.gca().transAxes) #Plot relative to bottom left at 0,0 
        plt.xlabel('Consecutive time deltas [seconds]')
        daterangestr = justthefile.split('From_MLrn_')[1].rstrip('.h5.pdf')
        plt.title(valcolname + '\n' + daterangestr)
        pdf.savefig()
        if quick and plotnum >= maxplots: break
        plotnum += 1
        

