"""Tweet regularly"""
print('***', 'started!')

# Allow running functions periodically
# http://apscheduler.readthedocs.io/en/3.3.1/
import sys
from apscheduler.schedulers.blocking import BlockingScheduler
from pokedex_bot import run

INTERVAL = 10

sched = BlockingScheduler()

@sched.scheduled_job('interval', minutes=INTERVAL)
def timed_job():
	run()

try:
	print('Info: {name} running.'.format(name=sys.argv[0]))
	print('Info: Will tweet every {min} minutes and reply to tweets. Stop with Ctrl+c'.format(min=INTERVAL))
	sched.start()
# a KeyboardInterrupt exception is generated when the user presses Ctrl+c
except KeyboardInterrupt:
	print('\nInfo: Shutting down. Bye!')
