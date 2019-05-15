import h5py
import matplotlib
matplotlib.use('agg')  #Workaround for missing tkinter
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import urllib
import time
import datetime
import timeit
import requests

debug = False

def read_URL_to_file (URL, filename):
    with urllib.request.urlopen(URL) as url_returns:
        data = url_returns.read().decode('utf-8').split('\n')
        with open(filename, 'w') as f:
            for datum in data:
                f.write("%s\n" % datum)
                
    return 
one_day = datetime.timedelta(days=1)
one_sec = datetime.timedelta(seconds=1)

now = datetime.datetime.now()
starttime = '{0:%Y-%m-%d+%H:%M:%S}'.format(now - one_sec)
stopptime = '{0:%Y-%m-%d+%H:%M:%S}'.format(now )

##starttime = '{0:%Y-%m-%d}'.format(now - one_day)
##stopptime = '{0:%Y-%m-%d}'.format(now )
##
# logger_get ACL command documentation: https://www-bd.fnal.gov/issues/wiki/ACLCommandLogger_get
URL = "http://www-ad.fnal.gov/cgi-bin/acl.pl?acl=logger_get/date_format='utc_seconds'/ignore_db_format/start=\""+starttime+"\"/end=\""+stopptime+"\"/node="

D43DataLoggerNode = 'MLrn'
URL = URL + D43DataLoggerNode + '+'
deviceNames = ('B:VIMIN', 'B_VIMIN', 'B:VIMAX', 'B_VIMAX', 'B:IMINER', 'B:NGMPS')
tempfilename = 'temp_file.txt'


dfdict = {} #Need a place to keep each dataframe
for deviceName in deviceNames:
    tempfilename = 'tempfile'+deviceName+'.txt'
    tempURL = URL + deviceName
    if debug: print (tempURL)

    # Download device data to local ASCII file
    with open(tempfilename, "wb") as file:
        # Column headers
        headers = 'utc_seconds'+deviceName+' \t '+deviceName+'\n'
        # Write headers encoded
        file.write(headers.encode('utf-8'))
        # Get request
        response = requests.get(tempURL)
        # Write data to file
        file.write(response.content)
    # Dump the file into a pandas DataFrame 
    columns = ('utc_seconds'+deviceName, deviceName) # Will get these set up higher.
    dfdict[deviceName] = pd.read_csv(tempfilename, delim_whitespace=True, names=columns)
    if debug: print (dfdict[deviceName])

df = pd.concat(dfdict.values(), axis=1)
print (df)
h5key = 'x' #str(time.time())
print (h5key)
#Fun with hdf5
df.to_hdf('moar.h5', key=h5key, mode='w')
