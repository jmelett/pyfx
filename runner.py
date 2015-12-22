import datetime
from dateutil import parser
import subprocess
import time

def run_that_show(start, end):
    print  start, end
    subprocess.Popen(["nohup", "envdir", "./.env_sandbox",
                      "python", "_cmd.py",
                      "-s", str(start),
                      "-e", str(end),
                      "-i", "EUR_USD",
                      ])


# Ideally start on Sundays
# START = "2015-W47"
# END = "2015-W48"
#START = "2015.06.07"
#END = "2015.12.20"
START = '2015.01.03'
END = '2015.06.07'
MAX_DAYS = 28

start_dt = parser.parse(START)
end_dt = parser.parse(END)

is_done = False
start_ = start_dt
end_ = None
while not is_done:
    end_ = start_dt + datetime.timedelta(days=MAX_DAYS)
    #print start_dt, end_
    run_that_show(start_dt, end_)
    if not (end_dt - start_dt).days > MAX_DAYS:
        is_done = True
    start_dt = end_
    time.sleep(60)

    # print start_dt, end_dt, (end_dt - start_dt).days
