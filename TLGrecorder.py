#import h5py
import numpy as np
#import pandas as pd
import datetime
#from dateutil import parser as dtpars
import time
from time import sleep
import requests
import argparse
from pathlib import Path
from bs4 import BeautifulSoup
import shutil

### Make a commadline option parser
parser = argparse.ArgumentParser(description="usage: %prog [options] <input file.ROOT> \n")
### Add options
parser.add_argument ('-v', dest='debug', action="store_true", default=False,
                   help="Turn on verbose debugging.")
### Get the options and argument values from the parser....
options = parser.parse_args()
### ...and assign them to variables. (No declaration needed, just like bash!)
debug    = options.debug

# Cutoff times in seconds
too_late = 1.
safe_now = 1.

while True:
    TimeLeft = 0.
    #Poll for the time remaining in the present super cycle
    # https://www-bd.fnal.gov/cgi-bin/acl.pl?acl=tlg_info/supercycleLength
    # or https://www-bd.fnal.gov/cgi-bin/acl.pl?acl=read/no_name/no_units%20G:SCTIME
    # https://www-bd.fnal.gov/cgi-bin/acl.pl?acl=val=G:SCTIME.setting-G:SCTIME;print+val
    # Supercycle length : 60.066666
    thisURL = 'https://www-bd.fnal.gov/cgi-bin/acl.pl?acl=val=G:SCTIME.setting-G:SCTIME;print+val'
    response = requests.get(thisURL)
    ## Did we get anything?
    if response is None:
        if debug: print (thisURL+"\n begat no reponse.")
        continue
    else:
        soup = BeautifulSoup(response.text, "html.parser")
        TimeLeftStr = soup.get_text()
        TimeLeft = float(TimeLeftStr )
        if debug: print (TimeLeft)

    if TimeLeft < too_late:
        sleep(TimeLeft+safe_now)
    else:        
        #If it's not too late, 
        # 
        #http://www-ad.fnal.gov/cgi-bin/acl.pl?acl=tlg_info/all_event_info
        #Event information :
        #  1) Event : 17  State ID :   5  Time :  0      Machine : Booster
        #  2) Event : E3  State ID :  30  Time :  0      Machine : Recycler
        #  3) Event : 32  State ID :   1  Time :  0      Machine : Switchyard
        #  4) Event : 1D  State ID :   4  Time :  .0667  Machine : Booster
        #  5) Event : 1D  State ID :   4  Time :  .1333  Machine : Booster
        SC_URL = 'http://www-ad.fnal.gov/cgi-bin/acl.pl?acl=tlg_info/all_event_info'
        SC_response = requests.get(SC_URL)
        if SC_response is None:
            if debug: print (SC_URL+"\n begat no reponse.")
            continue
        else:
            soup = BeautifulSoup(SC_response.text, "html.parser")
            SC_Str = soup.get_text()
            print ('-------------------------')
            print (SC_Str)
            print ('Sleeping for '+str(TimeLeft+safe_now))
        sleep(TimeLeft+safe_now)
