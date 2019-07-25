import argparse
import pandas as pd
import h5py


### Make a parser
parser = argparse.ArgumentParser(description="usage: %prog [options] <input file.ROOT> \n")
### Add options
parser.add_argument ('infilename')
parser.add_argument ('-v', dest='debug', action="store_true", default=False,
                   help="Turn on verbose debugging.")
parser.add_argument ('--infilename',  dest='infilename', default='',
                   help="Input filename.")
parser.add_argument ('--outdir',  dest='outdir', default='',
                   help="Directory to write final output file.")

### Get the options and argument values from the parser....
options = parser.parse_args()
### ...and assign them to variables. (No declaration needed, just like bash!)
infilename = options.infilename
debug      = options.debug
outdir     = options.outdir

# Open the file
infile = h5py.File(infilename, 'r+')
for key in infile.keys():
    #print (key+'  '+str(len(pd.read_hdf(infilename,key))))
    dataset = infile[key]
    tempdf = pd.read_hdf(infilename, key)
    print ("  "+key)
    print (tempdf.shape)
    cols = tempdf.columns.to_list()
    print (cols)
    # Get the two column names of interest:
    timecol = ''
    valcol = ''
    for col in cols:
        if col.count('utc_seconds') > 0:
            timecol = col
        else:
            valcol = col
    timedeltas = tempdf[timecol].diff()
    print (timedeltas.describe())
    
