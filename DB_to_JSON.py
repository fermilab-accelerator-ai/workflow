# Better with https://metricsgraphicsjs.org/examples.htm ?
# or maybe https://square.github.io/cubism/ ?
import argparse
import os
import sqlite3
import json
import numpy as np
from shutil import copy2 as cp

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
parser = argparse.ArgumentParser(description='Loop over list of ACNET parameters, extracting history of their stats from a database into JSON.',
                                 formatter_class=make_wide(argparse.ArgumentDefaultsHelpFormatter))
parser.add_argument ('--dbpath', dest='dbpath', default="GMPSAI.db",
                     help="Path to database file. (default=GMPSAI.db)")
parser.add_argument ('-p',  dest='paramfilename', default='ParamList.txt',
                     help="File listing parameter names to retrieve. (default: ParamList.txt)")
parser.add_argument ('-v', dest='debug', action="store_true", default=False,
                     help="Turn on verbose debugging. (default: F)")
parser.add_argument ('-q','--quick', dest='quick', action="store_true", default=False,
                     help="Stop after maxparams plots are rendered. (default: F)")
parser.add_argument ('--maxparams',  dest='maxparams', default=2,
                     help="Max parameters to loop if -q. (default: 2).")
parser.add_argument ('--maxrows',  dest='maxrows', default=1E2,
                     help="Max rows to process if -q. (default: 1E2).")
parser.add_argument ('--outdir',  dest='outdir', default='',
                     help="Directory to write final output file, /web/sites/g/gmps-ai.fnal.gov/htdocs/ (default: pwd)")
parser.add_argument ('-o',  dest='outfilename', default='StatsHistoryBoringHolyMoly.json',
                     help="Final output file name. (default: StatsHistoryBoringHolyMoly.json)")
### Get the options and argument values from the parser....                                                                                                                      
options = parser.parse_args()
dbpath  = options.dbpath

## Do some basic checks for inputs we need
if not os.path.isfile(dbpath): exit ('File not found: '+dbpath)
paramfilename  = options.paramfilename
if not os.path.isfile(paramfilename): exit ('File not found: '+paramfilename)

debug       = options.debug
quick       = options.quick
maxparams   = int(options.maxparams)
maxrows     = int(options.maxrows)
outdir      = options.outdir # Such as /web/sites/g/gmps-ai.fnal.gov/htdocs
outfilename = options.outfilename

# Get all (or some) of the parameter names to look for
paramlist = []
with open(paramfilename, 'r') as f:
    for line in f.readlines():
        if quick and len(paramlist) >= maxparams: break
        paramlist.append(line.strip())
if debug: print (paramlist)

# In case we're only doing a few rows, like for dev testing
LIMITSTR = ';'
if quick:
    LIMITSTR = 'LIMIT '+str(maxrows)+';'
# Open a connection to the db
conn = sqlite3.connect(dbpath)
dbcurs = conn.cursor()

# Open an output file
outf = open(outfilename, 'w')

statnames = ['max','plus_sigma','mode','minus_sigma','min']
statnames = ['max','mode','std','min']
jstuff = {}
jstuff['data'] = []  # A list of dictionaries, one for each trace we want to plot
jstuff['layout'] = {} # The layout object for the plots we want these traces on.
jstuff['layout']['grid'] = {"rows": 0, "columns": 1,"pattern": "independent"}
jstuff['layout']['height'] = 200*len(paramlist)
jstuff['layout']['showlegend'] = False

for param_i, paramname in enumerate(paramlist):
    if debug: print ("Now on param #"+ str(param_i))
    
    jstuff['layout']['grid']['rows'] += 1 # A row for this param's plot to go on
    plotno = str(param_i+1)
    xax = "x"+plotno
    yax = "y"+plotno
    if param_i == 0: # Javascript is so hacky-looking.  Even for plotly.
        xax="x"
        yax="y"
    # Oh, xaxisN is connected to the yaxisN, and the yaxisN is connected to the xaxisN...
    jstuff['layout']["xaxis"+plotno] = {"anchor":"yaxis"+plotno}
    jstuff['layout']["yaxis"+plotno] = {"anchor":"xaxis"+plotno,
                                        "title":{
                                             "text":paramname
                                             }
                                        }

    paramdict = {} # Temporary holding place to accumulate data for this param's stats
    for statname in statnames:
        # Dictionaries of dictionaries of lists
        paramdict[statname] = {'epochUTCsec':[], 'statval':[]} 
        querystr = 'SELECT epochUTCsec, statval FROM ACNETparameterStats '                                                                                     
        querystr+= 'WHERE paramname == "'+paramname+'" AND statname == "'+statname+'" '
        querystr+= 'ORDER BY epochUTCsec '+LIMITSTR 
        if debug: print (querystr)
        ret = dbcurs.execute(querystr)
        for line in ret:
            timestamp, statval = line
            paramdict[statname]['epochUTCsec'].append(timestamp)
            paramdict[statname]['statval'].append(statval)

        if debug: print(paramdict[statname])
    
    # Now transform into the stats we want to plot
    paramdict['plus_sigma'] = {}
    paramdict['plus_sigma']['epochUTCsec'] = paramdict['std']['epochUTCsec']
    pluss = np.array(paramdict['mode']['statval']) + np.array(paramdict['std']['statval']) 
    paramdict['plus_sigma']['statval'] = pluss.tolist()

    paramdict['minus_sigma'] = {}
    paramdict['minus_sigma']['epochUTCsec'] = paramdict['std']['epochUTCsec']
    minus = np.array(paramdict['mode']['statval']) - np.array(paramdict['std']['statval']) 
    paramdict['minus_sigma']['statval'] = minus.tolist()

    jstuff['data'].append({'x':paramdict['max']['epochUTCsec'], 
                           'y':paramdict['max']['statval'], 
                           "xaxis":xax,
                           "yaxis":yax,
                           "type": "scatter",
                           "line": {"color": "rgba(0,100,50,0.2)"},
                           "name":paramname+" max"})
    jstuff['data'].append({'x':paramdict['plus_sigma']['epochUTCsec'], 
                           'y':paramdict['plus_sigma']['statval'], 
                           "xaxis":xax,
                           "yaxis":yax,
                           "type": "scatter",
                           "line": {"color": "rgba(0,100,50,0.2)"},
                           "name":paramname+" +1sigma"})
    jstuff['data'].append({'x':paramdict['mode']['epochUTCsec'], 
                           'y':paramdict['mode']['statval'], 
                           "xaxis":xax,
                           "yaxis":yax,
                           "type": "scatter",
                           "fill": "tonexty",
                           "line": {"color": "rgba(0,100,50,0.2)"},
                           "name":paramname+" mode"})
    jstuff['data'].append({'x':paramdict['minus_sigma']['epochUTCsec'], 
                           'y':paramdict['minus_sigma']['statval'], 
                           "xaxis":xax,
                           "yaxis":yax,
                           "type": "scatter",
                           "fill": "tonexty",
                           "line": {"color": "rgba(0,100,50,0.2)"},
                           "name":paramname+" -1sigma"})
    jstuff['data'].append({'x':paramdict['min']['epochUTCsec'], 
                           'y':paramdict['min']['statval'],     
                           "xaxis":xax,
                           "yaxis":yax,
                           "type": "scatter",
                           "line": {"color": "rgba(0,100,50,0.2)"},
                           "name":paramname+" min"})

# Now use the dictionary to write to the JSON file for this param. 
json.dump(jstuff, outf, indent=4)    

outf.close()
if outdir != '':
    if not os.path.isdir(outdir): exit("Unable to copy output to supplied output directory called "+outdir)
    cp(outfilename, outdir+"/"+outfilename)
