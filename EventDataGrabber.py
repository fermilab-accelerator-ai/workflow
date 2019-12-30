import h5py
from io import StringIO
import numpy as np
import pandas as pd
import datetime
from dateutil import parser as dtpars
import time
import requests
import argparse
from pathlib import Path
from bs4 import BeautifulSoup

# ArgParse is outstanding, handling many types and
# generating a --help very easily.  Typical Python module with named, optional arguments
# For instance:
### Make a parser
parser = argparse.ArgumentParser(description="usage: %prog [options] <input file.ROOT> \n")
### Add options
parser.add_argument ('-v', dest='debug', action="store_true", default=False,
                   help="Turn on verbose debugging.")
# Maybe just a string formatted in UTC datetime.
parser.add_argument ('--stopat',  dest='stopat', default='',
                   help="YYYY-MM-DD hh:mm:ss")
parser.add_argument ('--days', dest='days', type=float, default=0,
                   help="Days before start time to request data? Default zero.")
parser.add_argument ('--hours', dest='hours', type=float, default=0,
                   help="Hours before start time to request data? Default zero.")
parser.add_argument ('--minutes', dest='minutes', type=float, default=0,
                   help="Minutes before start time to request data? Default zero.")
parser.add_argument ('--seconds', dest='seconds', type=float, default=0,
                   help="Seconds before start time to request data? Default zero.")
parser.add_argument ('--outdir',  dest='outdir', default='',
                   help="Directory to write final output file.")
parser.add_argument ('--draftdir',  dest='draftdir', default='',
                   help="Directory to draft output file.")
parser.add_argument ('--maxEvt',  dest='maxEvt', default=0xFF,
                   help="Highest hex code to loop over.")
parser.add_argument ('-o',  dest='oneAndDone',  action="store_true", default=False,
                   help="Stop after a single TCLK event yields data.")
### Get the options and argument values from the parser....
options = parser.parse_args()
### ...and assign them to variables. (No declaration needed, just like bash!)
debug    = options.debug
stopat   = options.stopat
days     = options.days    
hours    = options.hours   
minutes  = options.minutes 
seconds  = options.seconds 
outdir   = options.outdir
draftdir = options.draftdir
if isinstance(options.maxEvt, str):
    maxEvt = int(options.maxEvt, 16)
else: maxEvt = options.maxEvt
oneAndDone = options.oneAndDone

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

if debug or True:
    print ('Data request start time:' + starttime)
    print ('Data request stop time:' + stopptime)

D43DataLoggerNode = 'EventC'
#Output file needs a meaningful name and location
abspath = Path().absolute()
current_dir = abspath
if outdir == '':
    outdir = str(current_dir) + '/'

if draftdir == '':
    draftdir = str(current_dir) + '/'

draftfilename = draftdir+'/MLEventData_'+unixtimestr+'_From_'+D43DataLoggerNode+'_'+starttime+'_to_'+stopptime+'.h5'
outfilename   =   outdir+'/MLEventData_'+unixtimestr+'_From_'+D43DataLoggerNode+'_'+starttime+'_to_'+stopptime+'.h5'


if debug or True:
    print ("Data will be saved into "+draftfilename+"\n initiallly, then moved to \n"+outfilename)
    
# Retrieve the timestamps of broadcasting for every TCLK event over this time span.
URL = "http://www-ad.fnal.gov/cgi-bin/acl.pl?acl=event_log/start_time=\""+starttime+"\"/stop_time=\""+stopptime+"\"/event="
nodata = True
maxEvtstr = str(hex(maxEvt)).upper()
if debug or True: print ("Highest event number to check will be: "+maxEvtstr)
for eventdec in range(0, maxEvt+1):
    TCLKevent ='{:02x}'.format(eventdec)
    thisURL = URL + TCLKevent
    if debug: print (thisURL)
    response = requests.get(thisURL)
    ## Did we get anything?
    if response is None:
        if debug: print (thisURL+"\n begat no reponse.")
        continue
    soup = BeautifulSoup(response.text, "html.parser")
    str1 = soup.get_text()
    if debug: print (str1)
    nodata = False # First time we get a nontrivial response.
    if str1.count('No occurrences of event') > 0: continue
    ## Easy to make a dataframe from the results. And add them to an appropriately keyed group in the hdf5?
    df = pd.read_csv(StringIO(str1), header=None, delim_whitespace=True)
    #if len(df) < 1: continue #..,Skip event if no data for it.
    # Set the column names
    df.columns = ['date','time','SCmicrosec']
    # Merge date and time to make datetime. Then drop original columns.
    df['datetime'] = df['date'] + ' ' + df['time'] 
    # Convert to UNIX epoch seconds
    df['epoch'] = pd.to_datetime(df['datetime']).astype('int64')/1.0E9
    # Clean up these columns
    dropthese = ['date','time']
    df.drop(dropthese, inplace=True, axis=1)

    if debug: print (df)
    # Save df to file.
    df.to_hdf(draftfilename,'Event'+TCLKevent, append=True)
    if oneAndDone and not nodata:
        print ("'One and done' option -o: Stopped after getting and saving data for $"+TCLKevent)
        break

import subprocess
if nodata: print ("\n\n    No data returned for any event.\n\n")
if not outfilename == draftfilename:
    if debug: print ("Moving from "+draftfilename+" to "+outfilename+".")
    subprocess.run(["mv "+draftfilename+" "+outfilename,], shell=True, check=True)
