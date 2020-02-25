import h5py
from io import StringIO
import numpy as np
import pandas as pd
import datetime
from dateutil import parser as dtpars
from dateutil import relativedelta
import time
import requests
import argparse
from pathlib import Path
from bs4 import BeautifulSoup
import sqlite3

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

#Output file needs a meaningful name and location
abspath = Path().absolute()
current_dir = abspath
if outdir == '':
    outdir = str(current_dir) + '/'

if draftdir == '':
    draftdir = str(current_dir) + '/'

draftfilename = draftdir+'/TimelineEventData_'+unixtimestr+'_'+starttime+'_to_'+stopptime+'.h5'
outfilename   =   outdir+'/TimelineEventData_'+unixtimestr+'_'+starttime+'_to_'+stopptime+'.h5'


# get Supercycle_length
def get_supercycle_length(debug=False):
    SClenURL = 'https://www-bd.fnal.gov/cgi-bin/acl.pl?acl=read/no_name/no_units/setting%20G:SCTIME'
    response = requests.get(SClenURL)
    if response is None:
        if debug: print (SClenURL+"\n begat no reponse.")
        return
    soup = BeautifulSoup(response.text, "html.parser")
    strSClen = soup.get_text()
    strSClen = float(strSClen.strip().lstrip())
    return strSClen

# get_current_SC_time
def get_current_SC_time(debug=False):
    SCtimeURL = 'https://www-bd.fnal.gov/cgi-bin/acl.pl?acl=read/no_name/no_units%20G:SCTIME'
    response = requests.get(SCtimeURL)
    if response is None:
        if debug: print (SCtimeURL+"\n begat no reponse.")
        return
    soup = BeautifulSoup(response.text, "html.parser")
    strSCtime = float(soup.get_text().strip().lstrip())
    return strSCtime

 
# Retrieve the timestamps of broadcasting for every TCLK event over this time span.
def get_timeline(debug=False):
    thisURL = "http://www-ad.fnal.gov/cgi-bin/acl.pl?acl=tlg_info/all_event_info"
    if debug: print (thisURL)
    response = requests.get(thisURL)
    ## Did we get anything?
    if response is None:
        if debug: print (thisURL+"\n begat no reponse.")
        return
    ## Parse response as fixed-width fields
    soup = BeautifulSoup(response.text, "html.parser")
    str1 = soup.get_text()
    if debug: print (str1)
    df = pd.read_fwf(StringIO(str1), skiprows=1, header=None, usecols=[3,10])
    df.rename(columns={3:'Event',10:'SCTimeOffset'}, inplace=True)
    if debug: print (df)
    return df

min_execution_time = 5 #How long is too little to finish?
safety_after_00 = 0.001
while True:
    strSClen = get_supercycle_length()
    strSCtime = get_current_SC_time()

    # datetime at start of this supercyle
    now = datetime.datetime.now()
    SCstart = now - relativedelta.relativedelta(seconds=strSCtime)
    
    # Remaining time in SuperCycle:
    TimeLeft = strSClen - strSCtime
    print (TimeLeft, ' seconds left in super cycle. ')

    # Get the timeline, assuming there's time to do so
    if TimeLeft > min_execution_time:
        df = get_timeline()
        starttime = pd.DataFrame(index=range(len(df)),columns=['SCstart'])
        starttime['SCstart'] = SCstart
        df = pd.concat([starttime, df], axis=1)
        # Dataframe headers:  SCstart Event SCTimeOffset
        df['SCentry_index'] = df.index
        df.rename(columns={'SCstart':'SC_StartTime', 
                           'Event':'eventHex', 
                           'SCTimeOffset':'SC_EventTime'}, errors='raise', inplace=True)
        if debug: print (df.to_csv(sep=' '))
        if debug: print (list(df))
        # Database table columns: 
        #               SC_StartTime       SCentry_index      eventHex       SC_EventTime 
        # TimeLineLogs (SC_StartTime TEXT, SCentry_index INT, eventHex TEXT, SC_EventTime, PRIMARY KEY (SC_StartTime, SCentry_index));
        dbname = 'GMPSAI.db'
        conn = sqlite3.connect(dbname)
        df.to_sql('TimeLineLogs', conn, if_exists ='append', index=False)
        conn.commit()
        conn.close()
    # Snooze until the next SuperCycle is safely underway.
    time.sleep(TimeLeft + safety_after_00)
    
