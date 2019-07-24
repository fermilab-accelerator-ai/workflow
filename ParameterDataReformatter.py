import argparse
from pathlib import Path
import pandas as pd
import h5py

### Make a parser
parser = argparse.ArgumentParser(description="usage: %prog [options] <input file.ROOT> \n")
### Add options
parser.add_argument ('infilename')
parser.add_argument ('-v', dest='debug', action="store_true", default=False,
                   help="Turn on verbose debugging.")
parser.add_argument ('--outfilename',  dest='outfilename', default='',
                   help="Output filename.")
parser.add_argument ('--outdir',  dest='outdir', default='',
                   help="Directory to write final output file.")
parser.add_argument ('--draftdir',  dest='draftdir', default='',
                   help="Directory to write draft output file.")

### Get the options and argument values from the parser....
options = parser.parse_args()
### ...and assign them to variables. (No declaration needed, just like bash!)
infilename    = options.infilename
outfilename   = options.outfilename
debug         = options.debug
outdir        = options.outdir
draftdir      = options.draftdir

# Extract absolute path to input file, and file name.
infilepath = str(Path(infilename).parent)
if infilepath.count('/')>0: infilepath = infilepath+"/"

if debug: print ("infilepath:  "+infilepath)
infilename = str(Path(infilename).name)
if debug: print ("infilename:  "+infilename)

#Output file needs a meaningful name and location
abspath = Path().absolute()
current_dir = abspath
if outdir == '':
    outdir = str(current_dir)
outdir = outdir + '/'
if draftdir == '':
    draftdir = str(current_dir)
draftdir = draftdir + '/'

if debug: print ("Drafting output file in "+draftdir+" then moving to "+outdir)
# Default is to use a reworked version of the input filename
if outfilename == '':
    outfilename = infilename.replace('MLData', 'MLParamData')
    if debug: print ('Outfile will be '+outfilename)

draftfilename = draftdir   + outfilename
outfilename   =   outdir   + outfilename
infilename    = infilepath +  infilename    

# Open the file
if debug: print ('Ready to open '+infilename)
infile = h5py.File(infilename, 'r')
if not 'x' in infile.keys():
    exit("Cannot find key 'x' in file "+infilename)

# Extract the one huge pandas dataframe in there under key 'x'
df = pd.read_hdf(infilename,'x')
# Fastest way to get the column names
cols = df.columns.values.tolist()

for col in cols:
    # Skip the time series columns for now, for simplicity
    if col.count('utc_seconds') >0: continue
    timecol = 'utc_seconds'+col
    if timecol not in cols:
        print (timecol+' not found!')
        continue
    tempdf = df.filter([timecol, col], axis=1)
    # Save this dataframe to the file under its own key
    if debug: print ('Writing for '+col+' into '+draftfilename)
    tempdf.to_hdf(draftfilename, col, append=True)

import subprocess
if not outfilename == draftfilename:
    if debug: print ("Moving from "+draftfilename+" to "+outfilename+".")
    subprocess.run(["mv "+draftfilename+" "+outfilename,], shell=True, check=True)
