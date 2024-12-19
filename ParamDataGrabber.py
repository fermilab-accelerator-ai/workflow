import h5py
import matplotlib
matplotlib.use('agg')  #Workaround for missing tkinter
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import urllib
import time
import datetime
from dateutil import parser as dtpars
import timeit
import requests
from urllib.request import urlopen
import argparse
from pathlib import Path
from io import StringIO
from bs4 import BeautifulSoup
import subprocess

def read_URL_to_file (URL, filename):
    with urllib.request.urlopen(URL) as url_returns:
        data = url_returns.read().decode('utf-8').split('\n')
        with open(filename, 'w') as f:
            for datum in data:
                f.write("%s\n" % datum)                
    return 


# optparse is outstanding, handling many types and
# generating a --help very easily.  Typical Python module with named, optional arguments
# For instance:
### Make a parser
parser = argparse.ArgumentParser(description="usage: %prog [options] <input file.ROOT> \n")
### Add options
parser.add_argument ('-v', dest='debug', action="store_true", default=False,
                     help="Turn on verbose debugging. (default: False)")
parser.add_argument ('--dryrun', dest='dryrun', action="store_true", default=False,
                     help="Save no output file. (default: False)")
# Maybe just a string formatted in UTC datetime.
parser.add_argument ('--stopat',  dest='stopat', default='',
                     help="YYYY-MM-DD hh:mm:ss (default: last midnight)")
parser.add_argument ('--startat',  dest='startat', default='',
                     help="YYYY-MM-DD hh:mm:ss (default: '')")
parser.add_argument ('--maxcount',  dest='maxcount', default=-1,
                     help="Number of devices in list to process. (default: -1 = all)")
parser.add_argument ('--days', dest='days', type=float, default=0,
                     help="Days before stop time to request data? (default: %(default)s).")
parser.add_argument ('--hours', dest='hours', type=float, default=0,
                     help="Hours before stop time to request data? (default: %(default)s)")
parser.add_argument ('--minutes', dest='minutes', type=float, default=0,
                     help="Minutes before stop time to request data? (default: %(default)s)")
parser.add_argument ('--seconds', dest='seconds', type=float, default=0,
                     help="Seconds before stop time to request data? (default: %(default)s unless all are zero, then 1).")
parser.add_argument ('--draftdir',  dest='draftdir', default='',
                     help="Directory to draft output file while appending. (default: pwd)")
parser.add_argument ('--outdir',  dest='outdir', default='',
                     help="Directory to write final output file. (default: pwd)")
parser.add_argument ('--logger',  dest='loggernode', default='MLrn',
                     help="D43 Data Logger Node name. (default: MLrn)")
parser.add_argument ('--paramfile',  dest='paramlistfile', default='ParamList.txt',
                     help="Parameter list file name. (default: ParamList.txt)")

### Get the options and argument values from the parser....
options = parser.parse_args()
### ...and assign them to variables. (No declaration needed, just like bash!)
debug     = options.debug
dryrun    = options.dryrun
stopat    = options.stopat
startat   = options.startat
maxcount  = int(options.maxcount)
days      = options.days    
hours     = options.hours   
minutes   = options.minutes 
seconds   = options.seconds 
outdir    = options.outdir
draftdir  = options.draftdir
loggernode= options.loggernode
paramlistfile = options.paramlistfile

# Get the current directory of execution
abspath = Path().absolute()
current_dir = str(abspath)

if outdir == '': outdir = current_dir
if draftdir == '': draftdir = current_dir


unixtimestr = str(time.time())
# Datetime for when to stop the reading
today = datetime.datetime.today()

stopptime = ''
if stopat == '': #Default: Midnight at the start of today
    stopptime = '{0:%Y-%m-%d+00:00:00}'.format(today )
else:            # or attempt to use the string passed in by user
    stopdt =  dtpars.parse(stopat)
    stopptime = '{0:%Y-%m-%d+%H:%M:%S}'.format(stopdt)

if debug: print ("Stop time: "+stopptime)

starttime_datetime = None
if startat != '':
    if debug: print(f'--startat="{startat}"')
    try: starttime_datetime = dtpars.parse(startat)
    except Exception as e:
        exit (f'Error parsing --start argument: {e}')
    starttime = '{0:%Y-%m-%d+%H:%M:%S}'.format(starttime_datetime)

else: # No --startat argument Maybe we can use d/h/m/s units?
    # If no time interval set, default to 1 second
    if days == 0 and hours == 0 and minutes == 0 and seconds == 0: seconds = 1

    if debug:
        print ("Time interval: days = "+str(days)+
               ", hours = "  +str(hours  )+
               ", minutes = "+str(minutes)+
               ", seconds = "+str(seconds)+".")

    # Build a datetime interval to offset starttime before stopptime. 
    interval = datetime.timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)

    # Set the time to start the data-series request window
    starttime = '{0:%Y-%m-%d+%H:%M:%S}'.format(dtpars.parse(stopptime.replace('+',' ')) - interval)

if debug:
    print ('Data request start time:' + starttime)
    print ('Data request stop time:' + stopptime)
# logger_get ACL command documentation: https://www-bd.fnal.gov/issues/wiki/ACLCommandLogger_get
URL = "http://www-ad.fnal.gov/cgi-bin/acl.pl?acl=logger_get/date_format='utc_seconds'/ignore_db_format/start=\""+starttime+"\"/end=\""+stopptime+"\"/node="

# Get the list of parameter names 
import GMPSAIutilities as gmpsutils
deviceNames = gmpsutils.getParamListFromTextFile(textfilename = paramlistfile, debug=debug)

URL = URL + loggernode + '+'
if debug: print (URL)
draftfilename = draftdir+'/MLParamData_'+unixtimestr+'_From_'+loggernode+'_'+starttime+'_to_'+stopptime+'.h5'
outfilename   =   outdir+'/MLParamData_'+unixtimestr+'_From_'+loggernode+'_'+starttime+'_to_'+stopptime+'.h5'

# Loop over device names, retrieving data from the specified logger node
if maxcount < 0: maxcount = len(deviceNames)
devicecount = 0
for node, deviceName in deviceNames:
    # Allows early stopping for development dolphins
    devicecount += 1
    if devicecount > maxcount: break

    # URL for getting this device's data
    tempURL = URL + deviceName
    if debug: print (tempURL)

    # Download device data to a string
    response = urlopen(tempURL)
    if response is None:
        if debug: print (tempURL+"\n begat no reponse.")
        continue
    soup = BeautifulSoup(response.read(), "html.parser")
    str1 = soup.get_text()
    if debug: print (str1)
    if str1.count('No values'): 
        if debug: print (tempURL+"\n "+str1)
        continue
    ## Easy to make a dataframe from the results. And add them to an appropriately keyed group in the hdf5?
    df = pd.read_csv(StringIO(str1), header=None, delim_whitespace=True)
    if len(df) < 1: 
        if debug: print ('Dataframe length < 1.')
        continue #..,Skip event if no data for it.
    # Set the column names
    df.columns = ['utc_seconds', 'value']
    # Save df to file.
    if not dryrun: df.to_hdf(draftfilename, deviceName, append=True)

if not outfilename == draftfilename and not dryrun:
    if debug: print ("Moving from "+draftfilename+" to "+outfilename+".")
    subprocess.run(["mv "+draftfilename+" "+outfilename,], shell=True, check=True)

