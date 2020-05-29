# workflow
Machinery to pull data from DataLogger, wrangle data, inspect data, keep it all running

Special user gmpsai-prod on accelaigpvm01 runs these scripts, mostly through cron jobs.  If you'd like to be able to log in as the special user, contact Jason St. John or others on this list, and we can add your kerberos principal to the .k5login file.  Your ktickets will then let you log in.

Data File Generation:
Cron jobs: (check with crontab -l)
    At 01:00, run ParamDataGrabber.py with default (24h) window, default (most recent midnight) end-time.
    At 02:01, run EventDataGrabber.py with default (24h) window, default (most recent midnight) end-time.
    
0 1 * * * source /accelai/app/production/py3/bin/activate;  cd /accelai/app/production/workflow/ ; python3 ParamDataGrabber.py --days 1 --outdir /pnfs/ldrd/accelai/tape/
1 2 * * * source /accelai/app/production/py3/bin/activate;  cd /accelai/app/production/workflow/ ; python3 EventDataGrabber.py --days 1 --outdir /pnfs/ldrd/accelai/tape/

Usage details and defaults for these scripts:

python3 ParamDataGrabber.py --help
usage: ParamDataGrabber.py [-h] [-v] [--stopat STOPAT] [--days DAYS]
                           [--hours HOURS] [--minutes MINUTES]
                           [--seconds SECONDS] [--draftdir DRAFTDIR]
                           [--outdir OUTDIR]

usage: %prog [options] <input file.ROOT>

optional arguments:
  -h, --help           show this help message and exit
  -v                   Turn on verbose debugging. (default: False)
  --stopat STOPAT      YYYY-MM-DD hh:mm:ss (default: last midnight)
  --days DAYS          Days before start time to request data? (default: 0).
  --hours HOURS        Hours before start time to request data? (default: 0)
  --minutes MINUTES    Minutes before start time to request data? (default: 0)
  --seconds SECONDS    Seconds before start time to request data? (default: 0
                       unless all are zero, then 1).
  --draftdir DRAFTDIR  Directory to draft output file while appending.
                       (default: pwd)
  --outdir OUTDIR      Directory to write final output file. (default: pwd)

python3 EventDataGrabber.py --help 
usage: EventDataGrabber.py [-h] [-v] [--stopat STOPAT] [--days DAYS]
                           [--hours HOURS] [--minutes MINUTES]
                           [--seconds SECONDS] [--outdir OUTDIR]
                           [--draftdir DRAFTDIR] [--maxEvt MAXEVT] [-o]

usage: %prog [options] <input file.ROOT>

optional arguments:
  -h, --help           show this help message and exit
  -v                   Turn on verbose debugging.
  --stopat STOPAT      YYYY-MM-DD hh:mm:ss
  --days DAYS          Days before start time to request data? Default zero.
  --hours HOURS        Hours before start time to request data? Default zero.
  --minutes MINUTES    Minutes before start time to request data? Default
                       zero.
  --seconds SECONDS    Seconds before start time to request data? Default
                       zero.
  --outdir OUTDIR      Directory to write final output file.
  --draftdir DRAFTDIR  Directory to draft output file.
  --maxEvt MAXEVT      Highest hex code to loop over.
  -o                   Stop after a single TCLK event yields data.


On the horizon/Present work:
- Continuously running Timeline_Logger.py, saving the events and time offsets into the SuperCycle from TimeLineGenerator.  And a supervisory cron job to ensure this script is re-started in case it fails.
- After data file is closed (or better when it's generated?), script such as DistillFileStatsToDB.py, generates statistical summary of each data file, every parameter for which it contains time series data. Stats are stored in database (current default: local sqlite file GMPSAI.db).
- Regularly and when prompted, script such as DB_to_JSON.py derives a JSON file from the stats db, pushes it to javascript plot-display-and-inspection site: http://gmps-ai.fnal.gov/ (internal and VPN access only)
- Improved scalability for data file storage management (Rucio), and improved metadata management (as-yet-to-be-named Metadata Database, whose main customer is DUNE)
