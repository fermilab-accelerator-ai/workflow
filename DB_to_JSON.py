# Better with https://metricsgraphicsjs.org/examples.htm ?
# or maybe https://square.github.io/cubism/ ?
import argparse
import os
import sqlite3
import json

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
parser = argparse.ArgumentParser(description='Loop over list of ACNET parameters, extracting history of their stats from a database.',
                                 formatter_class=make_wide(argparse.ArgumentDefaultsHelpFormatter))
#
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
                     help="Directory to write final output file. (default: pwd)")
parser.add_argument ('-o',  dest='outfilename', default='StatsHistoryBoringHolyMoly.json',
                     help="Final output file name. (default: StatsHistoryBoringHolyMoly.json)")
### Get the options and argument values from the parser....                                                                                                                      
options = parser.parse_args()
dbpath  = options.dbpath
if not os.path.isfile(dbpath): exit ('File not found: '+dbpath)
paramfilename  = options.paramfilename
if not os.path.isfile(paramfilename): exit ('File not found: '+paramfilename)

debug       = options.debug
quick       = options.quick
maxparams   = int(options.maxparams)
maxrows     = int(options.maxrows)
outdir      = options.outdir
outfilename = options.outfilename

paramlist = []
with open(paramfilename, 'r') as f:
    for line in f.readlines():
        if quick and len(paramlist) >= maxparams: break
        paramlist.append(line.strip())

if debug: print (paramlist)

LIMITSTR = ';'
if quick:
    LIMITSTR = 'LIMIT '+str(maxrows)+';'
# Open a connection to the db
conn = sqlite3.connect(dbpath)
dbcurs = conn.cursor()

# Open an output file
outf = open(outfilename, 'w')

statnames = ['max','plus_sigma','mode','minus_sigma','min']
jstuff = {}
jstuff['data'] = {} # Ugly but necessary to be used.  Dicts must be named. 
for paramname in paramlist:
    jstuff['data'][paramname] = {}

    querystr = 'SELECT statname, epochUTCsec, statval FROM ACNETparameterStats '
    querystr+= 'WHERE paramname == "'+paramname+'" ORDER BY statname, epochUTCsec '+LIMITSTR
    if debug: print (querystr)
    ret = dbcurs.execute(querystr)
    # Refresh these dicts for each param.  They'll index by statname.
    statvalsdict = {}
    stattimedict = {}

    # Fill the dictionaries with lists of values for each stat's timestamps and recorded values
    laststatname = ''
    for line in ret:
        statname, timestamp, statval = line
        if statname != laststatname: # Starting a new stat
            statvalsdict[statname] = []
            stattimedict[statname] = []
            laststatname = statname
        statvalsdict[statname].append(statval)
        stattimedict[statname].append(timestamp)
    # Now append to the overall dictionary
    firststat = True
    for stat in statvalsdict.keys():
        jstuff['data'][paramname][stat] = [statvalsdict[statname], stattimedict[statname]]

# Now use the dictionary to write to the JSON file for this param. 
json.dump(jstuff, outf, indent=4)    
