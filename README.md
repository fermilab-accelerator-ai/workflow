# workflow
Machinery to pull data from DataLogger, wrangle data, inspect data, keep it all running

# Resources
Events in TCLK and what they mean: https://www-bd.fnal.gov/controls/hardware_vogel/tclk.htm

# Data Production
Special user gmpsai-prod on accelaigpvm01 runs these scripts, mostly through cron jobs.  If you'd like to be able to log in as the special user, contact Jason St. John or others on this list, and we can add your kerberos principal to the .k5login file.  Your ktickets will then let you log in.

Data File Generation:<br>
Cron jobs: (check with crontab -l)<br>
    At 01:00, run ParamDataGrabber.py with default (24h) window, default (most recent midnight) end-time. <br>
    At 02:01, run EventDataGrabber.py with default (24h) window, default (most recent midnight) end-time. <br>
    
0 1 * * * source /accelai/app/production/py3/bin/activate;  cd /accelai/app/production/workflow/ ; python3 ParamDataGrabber.py --days 1 --outdir /pnfs/ldrd/accelai/tape/<br>
1 2 * * * source /accelai/app/production/py3/bin/activate;  cd /accelai/app/production/workflow/ ; python3 EventDataGrabber.py --days 1 --outdir /pnfs/ldrd/accelai/tape/<br>

Usage details and defaults for these scripts:<br>

python3 ParamDataGrabber.py --help<br>
usage: ParamDataGrabber.py [-h] [-v] [--stopat STOPAT] [--days DAYS]<br>
                           [--hours HOURS] [--minutes MINUTES]<br>
                           [--seconds SECONDS] [--draftdir DRAFTDIR]<br>
                           [--outdir OUTDIR]<br>
<br>
usage: %prog [options] <input file.ROOT><br>

optional arguments:<br>
  -h, --help           show this help message and exit<br>
  -v                   Turn on verbose debugging. (default: False)<br>
  --stopat STOPAT      YYYY-MM-DD hh:mm:ss (default: last midnight)<br>
  --days DAYS          Days before start time to request data? (default: 0).<br>
  --hours HOURS        Hours before start time to request data? (default: 0)<br>
  --minutes MINUTES    Minutes before start time to request data? (default: 0)<br>
  --seconds SECONDS    Seconds before start time to request data? (default: 0
                       unless all are zero, then 1).<br>
  --draftdir DRAFTDIR  Directory to draft output file while appending.
                       (default: pwd)<br>
  --outdir OUTDIR      Directory to write final output file. (default: pwd)<br>
<br>
python3 EventDataGrabber.py --help <br>
usage: EventDataGrabber.py [-h] [-v] [--stopat STOPAT] [--days DAYS]<br>
                           [--hours HOURS] [--minutes MINUTES]<br>
                           [--seconds SECONDS] [--outdir OUTDIR]<br>
                           [--draftdir DRAFTDIR] [--maxEvt MAXEVT] [-o]<br>

usage: %prog [options] <input file.ROOT><br>

optional arguments:<br>
  -h, --help           show this help message and exit<br>
  -v                   Turn on verbose debugging.<br>
  --stopat STOPAT      YYYY-MM-DD hh:mm:ss<br>
  --days DAYS          Days before start time to request data? Default zero.<br>
  --hours HOURS        Hours before start time to request data? Default zero.<br>
  --minutes MINUTES    Minutes before start time to request data? Default
                       zero.<br>
  --seconds SECONDS    Seconds before start time to request data? Default
                       zero.<br>
  --outdir OUTDIR      Directory to write final output file.<br>
  --draftdir DRAFTDIR  Directory to draft output file.<br>
  --maxEvt MAXEVT      Highest hex code to loop over.<br>
  -o                   Stop after a single TCLK event yields data.<br>


On the horizon/Present work:<br>
<list>
<li>- Continuously running Timeline_Logger.py, saving the events and time offsets into the SuperCycle from TimeLineGenerator.  And a supervisory cron job to ensure this script is re-started in case it fails.</li>
<li>- After data file is closed (or better when it's generated?), script such as DistillFileStatsToDB.py, generates statistical summary of each data file, every parameter for which it contains time series data. Stats are stored in database (current default: local sqlite file GMPSAI.db).</li>
<li>- Regularly and when prompted, script such as DB_to_JSON.py derives a JSON file from the stats db, pushes it to javascript plot-display-and-inspection site: http://gmps-ai.fnal.gov/ (internal and VPN access only)</li>
<li>- Improved scalability for data file storage management (Rucio), and improved metadata management (as-yet-to-be-named Metadata Database, whose main customer is DUNE)</li>
    </list>
