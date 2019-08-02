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
import argparse
from pathlib import Path
from io import StringIO
from bs4 import BeautifulSoup
import subprocess

# optparse is outstanding, handling many types and
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
                     help="Seconds before start time to request data? Default zero unless all are zero, then 1 second.")
parser.add_argument ('--draftdir',  dest='draftdir', default='',
                     help="Directory to write output file.")
parser.add_argument ('--outdir',  dest='outdir', default='',
                     help="Directory to write output file.")
### Get the options and argument values from the parser....
options = parser.parse_args()
### ...and assign them to variables. (No declaration needed, just like bash!)
debug     = options.debug
stopat    = options.stopat
days      = options.days    
hours     = options.hours   
minutes   = options.minutes 
seconds   = options.seconds 
outdir    = options.outdir
draftdir  = options.draftdir

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
    
# If no time interval set, default to 1 second
if days == 0 and hours == 0 and minutes == 0 and seconds == 0: seconds = 1

if debug:
    print ("Time interval: days = "+str(days)+
           ", hours = "  +str(hours  )+
           ", minutes = "+str(minutes)+
           ", seconds = "+str(seconds)+".")

def read_URL_to_file (URL, filename):
    with urllib.request.urlopen(URL) as url_returns:
        data = url_returns.read().decode('utf-8').split('\n')
        with open(filename, 'w') as f:
            for datum in data:
                f.write("%s\n" % datum)                
    return 
# Build a datetime interval to offset starttime before stopptime. 
interval = datetime.timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)

# Set the time to start the data-series request window
starttime = '{0:%Y-%m-%d+%H:%M:%S}'.format(dtpars.parse(stopptime.replace('+',' ')) - interval)

if debug:
    print ('Data request start time:' + starttime)
    print ('Data request stop time:' + stopptime)
# logger_get ACL command documentation: https://www-bd.fnal.gov/issues/wiki/ACLCommandLogger_get
URL = "http://www-ad.fnal.gov/cgi-bin/acl.pl?acl=logger_get/date_format='utc_seconds'/ignore_db_format/start=\""+starttime+"\"/end=\""+stopptime+"\"/node="

D43DataLoggerNode = 'MLrn'
URL = URL + D43DataLoggerNode + '+'
deviceNames = ['B:VIMIN', 'B_VIMIN', 'B:VIMAX', 'B_VIMAX', 'B:IMINER', 'B:NGMPS', 'B:VINHBT', 'B:GMPSFF', 'B:GMPSBT',
               'B:IMINST', 'B:IPHSTC', 'B:IMINXG', 'B:IMINXO', 'B:IMAXXG', 'B:IMAXXO', 'B_VINHBT', 'B_GMPSFF', 'B_GMPSBT',
               'B_IMINST', 'B_IPHSTC', 'B_IMINXG', 'B_IMINXO', 'B_IMAXXG', 'B_IMAXXO',
               'B:ACMNPG', 'B:ACMNIG', 'B:ACMXPG', 'B:ACMXIG', 'B:DCPG' , 'B:DCIG', 'B:VIPHAS',
               'B_ACMNPG', 'B_ACMNIG', 'B_ACMXPG', 'B_ACMXIG', 'B_DCPG' , 'B_DCIG', 'B_VIPHAS',
               'B:PS1VGP', 'B:PS1VGM', 'B:GMPS1V', 'B:PS2VGP', 'B:PS2VGM', 'B:GMPS2V', 'B:PS3VGP', 'B:PS3VGM', 'B:GMPS3V', 'B:PS4VGP', 'B:PS4VGM', 'B:GMPS4V',
               'I:MXIB',   'I:IB'    , 'I:MDAT40']


draftfilename = draftdir+'/MLParamData_'+unixtimestr+'_From_'+D43DataLoggerNode+'_'+starttime+'_to_'+stopptime+'.h5'
outfilename   =   outdir+'/MLParamData_'+unixtimestr+'_From_'+D43DataLoggerNode+'_'+starttime+'_to_'+stopptime+'.h5'

tempfilename = 'temp_file.txt'
timestamps = np.zeros(shape=(1,1))

dfdict = {} #Need a place to keep each dataframe
for deviceName in deviceNames:
    tempfilename = 'tempfile'+deviceName+'.txt'
    tempURL = URL + deviceName
    if debug: print (tempURL)

    # Download device data to a string
    response = requests.get(tempURL)
    if response is None:
        if debug: print (tempURL+"\n begat no reponse.")
        continue
    soup = BeautifulSoup(response.text, "html.parser")
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
    df.to_hdf(draftfilename, deviceName, append=True)

if not outfilename == draftfilename:
    if debug: print ("Moving from "+draftfilename+" to "+outfilename+".")
    subprocess.run(["mv "+draftfilename+" "+outfilename,], shell=True, check=True)

