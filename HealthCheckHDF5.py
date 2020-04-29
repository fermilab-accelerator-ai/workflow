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
import seaborn as sns

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
parser = argparse.ArgumentParser(formatter_class=make_wide(argparse.ArgumentDefaultsHelpFormatter))
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
parser.add_argument ('--noplots', dest='noplots', action="store_true", default=False,
                     help="Skip plot making, save no plot file. (default: F)")
parser.add_argument ('--nodb', dest='nodb', action="store_true", default=False,
                     help="Skip database entry making. (default: F)")
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
maxparams   = int(options.maxparams)
maxrows     = int(options.maxrows)
justthefile = infilename.split('/')[infilename.count('/')]
outfilename = 'QualityChecks'+justthefile+'.pdf'
dbname      = options.dbname
checkfor    = options.checkfor
plotrowlen  = 5
reasonablejump = 20.0*0.003333

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
        tempdf = pd.read_hdf(infilename, checkfor)
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
        modelist = tempdf[valcolname].mode()
        uniques = list (tempdf[valcolname].unique() )
        print(tempdf[valcolname].value_counts())
        #for uniq in uniques:
            
        # print (len(uniques), ' unique values found among ',len(tempdf[valcolname]),' entries.')
    else: print (infilename+' -- No matching keys.')

    exit()

# Some fiddly work to extract the start and end datetime for this file.
plottitle = infilename.split('_')
betweentimes = plottitle.index('to')
dt_start = plottitle[betweentimes-1]
dt_enddd = plottitle[betweentimes+1].replace('.h5','')

StartTime = re.findall(r"\d\d\d\d-\d\d-\d\d\+\d\d:\d\d:\d\d",justthefile)[0]
if debug: print ('StartTime:')
if debug: print (StartTime)
# Convert to epoch
utc_time = datetime.datetime.strptime(StartTime, '%Y-%m-%d+%H:%M:%S')
epoch_time = (utc_time - datetime.datetime(1970, 1, 1)).total_seconds()
if debug: print (epoch_time)

timedflist = []
if not noplots: 
    # pdf = PdfPages('junk.pdf')
    fig, axs = plt.subplots(ncols = plotrowlen, nrows= int(len(filekeys)/plotrowlen))
            
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

    if not nodb:
        upsertstr = 'REPLACE INTO ACNETparameterStats (epochUTCsec, paramname, statname, statval) VALUES ('
        upsertstr += str(epoch_time) +', "'+key +'", '
        for statname in statnames: 
            cmdstr = upsertstr +'"'+statname +'", '+str(valstatsdict[statname])+');'
            if debug: print (cmdstr)
            dbcurs.execute(cmdstr)
            conn.commit()
    
    # Calculate sample-to-sample time deltas (units of timedel)
    timelist = tempdf[timecolname]#.sort_values() # Force to be non-negative
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
        #plt.figure(figsize=(8, 6))
        # nrows, ncols, and index in order
        plt.subplot
        binheights, binctrs, _ = plt.hist(timedeltas, bins=bincount, log=True, 
                                          range = (1.1*timedeltas.min(), 1.1*timedeltas.max()) )
        plt.text( 0.70, 0.85, textstr, transform=plt.gca().transAxes) #Plot relative to bottom left at 0,0 
        plt.xlabel('Consecutive time deltas [seconds]')
        daterangestr = justthefile.split('From_MLrn_')[1].rstrip('.h5.pdf')
        plt.title(valcolname + '\n' + daterangestr)
        pdf.savefig()
        
# What have we got in the list of time stamps?  Convert to a dataframe to start analysis.
timedf = pd.concat(timedflist, axis=1)
# Calculate average of all entries in the first row
init_t = timedf.mean(axis=1)[0]
# Generate a new column, a naive reference tick whose entries are init_t + index* (1/freqHz) seconds
freqHz = 15.0
naiveref = [init_t+(i/freqHz) for i in list(timedf.index) ]
timedf['naiveref'] = naiveref
# Subtract the reference from all columns
refsub_timedf = timedf.subtract(naiveref, axis=0)
# And drop that naive reference column, having used it.
refsub_timedf.drop(refsub_timedf.columns[[len(refsub_timedf.columns)-1]], axis=1, inplace=True)

# Look for any columns with large jumps wrt naive reference
outliers = []
inliers = []
for i, maxjump in enumerate(list(refsub_timedf.diff().max())):
    if maxjump > reasonablejump: outliers.append(i)
    else: inliers.append(i)

# Make a new dataframe of just the outliers, then drop them from the orignial dataframe
refsub_timedf_crazy = refsub_timedf.drop(refsub_timedf.columns[inliers], axis=1, inplace=False)
refsub_timedf.drop(refsub_timedf.columns[outliers], axis=1, inplace=True)

# Add the line frequency measurements
freqvals = pd.read_hdf(infilename, 'B:LINFRQ')
freqvals.rename(columns={'value':'B:LINFRQ'}, inplace=True)
freqvals.drop('utc_seconds', inplace=True, axis=1)
#refsub_timedf = pd.concat([refsub_timedf, freqvals], axis=1)


# ...and truncate rows if we're doing that.
if quick: refsub_timedf       = refsub_timedf.truncate(after=maxrows)
if quick: refsub_timedf_crazy = refsub_timedf_crazy.truncate(after=maxrows)
if quick: freqvals            = freqvals.truncate(after=maxrows)

# FINALLY rescale the line frequency values to within the resulting min/max for other columns
inliermin = list(refsub_timedf.min(numeric_only=True, axis=0))
del inliermin[-1] # Drop the final entry, which is from the line frequency
inliermin = min(inliermin)
inliermax = list(refsub_timedf.max(numeric_only=True, axis=0))
del inliermax[-1] # Drop the final entry, which is from the line frequency
inliermax = max(inliermax)

## # Plot the discrepancies as a heatmap
## plt.figure(1)
## ax = sns.heatmap(refsub_timedf.T, annot=False, yticklabels=True, cbar_kws={'label':'Cumulative Difference wrt 15 Hz [seconds]'})
## ax.figure.tight_layout()
## plt.xlabel('Ticks since midnight') 
## plt.suptitle('From '+dt_start+' to '+dt_enddd) 
## figure = ax.get_figure()
## figure.set_size_inches(6, 6)
## ax.figure.subplots_adjust(top = 0.90)
## figure.savefig("heatmap"+str(utc_time).replace(' 00:00:00','')+".png")
## 
## # ...and as a lineplot
## plt.figure(2)
## # So lineplot() seems to be a memory- and computation-intensive process! Try Without confidence intervals (ci) to some expensive (and unnecessary) df.groupby calls.
## ax2 = sns.lineplot(data=refsub_timedf, dashes=False, ci=False) # Should it be ci=None, per documentation? 
## gray = 'tab:gray'
## ax3 = sns.lineplot(data=freqvals['B:LINFRQ'], ax=ax2.twinx(), dashes=False, ci=False, legend=False, color=gray) # Should it be ci=None, per documentation? 
## ax3.set_ylabel('Line Freq Offset [mHz]', color=gray)
## ax3.tick_params(axis='y', labelcolor=gray)
## figure2 = ax2.get_figure()   
## figure2.set_size_inches(9, 6)
## # Shrink current axis by 20%
## box = ax2.get_position()
## ax2.set_position([box.x0*0.9, box.y0, box.width * 0.80, box.height])
## ax2.legend(bbox_to_anchor= (1.35, 1.1), loc='upper right', fontsize='small', fancybox=True, ncol=1, labelspacing=0.1)
## ax2.get_xaxis().get_major_formatter().set_scientific(True)
## ax2.set_ylabel('Cumulative Difference wrt 15 Hz [seconds]')
## plt.xlabel('Ticks since midnight')
## plt.suptitle('From '+dt_start+' to '+dt_enddd)
## figure2.savefig("lineplot.png")

# A scatterplot for the well-behaved?
plt.figure(3)
timediffs = pd.concat([refsub_timedf.diff(), freqvals], axis=1).rolling(15).mean()
ax4 = sns.relplot(x='B:LINFRQ', y='utc_B:ACMNIG', data=timediffs)
ax4.savefig("scatterplot.png")
