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

### Make a parser
parser = argparse.ArgumentParser(description='Makes terrible, uninformative plot.png files from an SQLite3 database.')
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
                     help="Filename to write final output file. (default: TimeTrendsPlots.pdf)")
parser.add_argument ('--db',  dest='dbname', default='GMPSAI.db',
                     help="Name of sqlite3 database file to grab caculated stats from. (default: GMPSAI.db)")


### Get the options and argument values from the parser....
options = parser.parse_args()
### ...and assign them to variables. (No declaration needed, just like bash!)
debug       = options.debug
nopdf     = options.nopdf
outdir      = options.outdir
quick       = options.quick
maxparams    = int(options.maxparams)
paramcount = 0
outfilename = options.outfilename
dbname      = options.dbname

bincount = 500
conn = sqlite3.connect(dbname)
dbcurs = conn.cursor()

def suplabel(axis,label,label_prop=None,
             labelpad=5,
             ha='center',va='center'):
    ''' Add super ylabel or xlabel to the figure
    Similar to matplotlib.suptitle
    axis       - string: "x" or "y"
    label      - string
    label_prop - keyword dictionary for Text
    labelpad   - padding from the axis (default: 5)
    ha         - horizontal alignment (default: "center")
    va         - vertical alignment (default: "center")
    '''
    fig = pylab.gcf()
    xmin = []
    ymin = []
    for ax in fig.axes:
        xmin.append(ax.get_position().xmin)
        ymin.append(ax.get_position().ymin)
    xmin,ymin = min(xmin),min(ymin)
    dpi = fig.dpi
    if axis.lower() == "y":
        rotation=90.
        x = xmin-float(labelpad)/dpi
        y = 0.5
    elif axis.lower() == 'x':
        rotation = 0.
        x = 0.5
        y = ymin - float(labelpad)/dpi
    else:
        raise Exception("Unexpected axis: x or y")
    if label_prop is None: 
        label_prop = dict()
    pylab.text(x,y,label,rotation=rotation,
               transform=fig.transFigure,
               ha=ha,va=va,
               **label_prop)


if not nopdf: pdf = PdfPages(outdir+outfilename)
paramsresults = dbcurs.execute("SELECT DISTINCT paramname from ACNETparameterStats;")
paramnames = []
for paramresult in paramsresults:
    if debug: print (paramresult)
    param = paramresult[0]
    paramnames.append(param)
    paramcount += 1
    if paramcount > maxparams: break

paramcount = 0
# Carve out a subplot for each param's stats
fig, axs = plt.subplots(len(paramnames)+1)
fig.set_size_inches(9.0, 5.*len(paramnames))
plt.tight_layout(h_pad=10.0, pad=1.0)

# Loop over params and their statistics from the database. Save into handy dictionaries as lists for plotting ease.
datadict = {}
paramyoffset = 0.
for param in paramnames:
    if quick and paramcount+1 > maxparams: break
    paramcount += 1
    statsresults = dbcurs.execute('SELECT DISTINCT statname FROM ACNETparameterStats WHERE paramname LIKE "{}";'.format(param))
    datadict[param] = {} # Subdictionary for this param
    paramyoffset += 1
    for statresult in statsresults:
        if debug: print (statresult)
        stat = statresult[0]
        # Skip the std for now
        if stat == 'std': continue 
        if debug: print (param, stat)
        # Make a dataframe for the time series of values
        slctstr = 'SELECT statval, epochUTCsec FROM ACNETparameterStats WHERE paramname LIKE "{}" AND statname LIKE "{}"'.format(param,stat)
        slctstr += ' ORDER BY epochUTCsec;'
        if debug: print (slctstr)
        # Create a dataframe from the results for this statistic for this parameter
        df = pd.read_sql_query(slctstr, conn)
        datadict[param][stat] = {} # subsubdictionary for param and stat
        datadict[param][stat]['X'] = df['epochUTCsec'].tolist()
        datadict[param][stat]['Y'] = df['statval'].tolist()
        # Want the ends of the y-axis range
        if stat == 'min': datadict[param]['minmin'] = min(df['statval'])
        elif stat == 'max': datadict[param]['maxmax'] = max(df['statval'])
        
        if debug: print ('Dataframe for '+stat+':\n',df)
        # Add data to this subplot for this stat
        #axs[paramcount-1].plot('epochUTCsec', 'statval', data=df)
        offsetlist = np.ones(len(datadict[param][stat]['Y'])) * paramyoffset
        print ('paramyoffset: ',paramyoffset)
        axs[paramcount-1].plot( datadict[param][stat]['X'], 
                                datadict[param][stat]['Y'] + offsetlist)
        axs[paramcount-1].patch.set_visible(False)
        axs[paramcount-1].spines['left'].set_visible(True)
        axs[paramcount-1].spines['right'].set_visible(False)
        axs[paramcount-1].spines['top'].set_visible(False)
        axs[paramcount-1].spines['bottom'].set_visible(False)
        axs[paramcount-1].set_ylabel(param)
        #axs[paramcount-1].axis('off')


#yticklabels = []
#
#for i, (name, linestyle) in enumerate(linestyles):
#        ax.plot(X, Y+i, linestyle=linestyle, linewidth=1.5, color='black')
#        yticklabels.append(name)
#
#    ax.set(xticks=[], ylim=(-0.5, len(linestyles)-0.5),
#           yticks=np.arange(len(linestyles)), yticklabels=yticklabels)
#
#    # For each line style, add a text annotation with a small offset from
#    # the reference point (0 in Axes coords, y tick value in Data coords).
#    for i, (name, linestyle) in enumerate(linestyles):
#        ax.annotate(repr(linestyle),
#                    xy=(0.0, i), xycoords=ax.get_yaxis_transform(),
#                    xytext=(-6, -12), textcoords='offset points',
#                    color="blue", fontsize=8, ha="right", family="monospace")

#sns.lmplot(x=list(datadict.keys()), 

plt.savefig("test.png")


    #axdict = {}
    #main = 'mode'
    ##ax = datadict[main].plot(kind='scatter', x='epochUTCsec', y='statval', label=main, style='-o')
    #ax = datadict[main].plot.line(x='epochUTCsec', y='statval', label=main, style='-')

    #datadict['max'].plot.line(x='epochUTCsec', y='statval', label='max', ax=ax, style='-')

    #for key in datadict.keys():
    #    if key == main or key =='std': continue
    #    axdict[key] = datadict[key].plot.line(x='epochUTCsec', y='statval', label=key, ax=ax, style='-')

    #plt.text( 0.70, 0.85, textstr, transform=plt.gca().transAxes) #Plot relative to bottom left at 0,0 
    #plt.xlabel('Consecutive time deltas [seconds]')
    #daterangestr = justthefile.split('From_MLrn_')[1].rstrip('.h5.pdf')
    #plt.title(valcolname + '\n' + daterangestr)
    
        

