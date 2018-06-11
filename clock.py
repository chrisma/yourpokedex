"""Tweet regularly"""

# Allow running functions periodically
# http://apscheduler.readthedocs.io/en/3.3.1/
import sys
import logging
import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from pokedex_bot import run

INTERVAL = 30

log = logging.getLogger('clock')

sched = BlockingScheduler()

@sched.scheduled_job('interval', minutes=INTERVAL, next_run_time=datetime.datetime.now())
def timed_job():
	run(dry_run=True)

if __name__ == '__main__':
	logging.basicConfig(level=logging.DEBUG)
	logging.getLogger('requests').setLevel(logging.WARN)
	logging.getLogger('requests_oauthlib').setLevel(logging.WARN)
	logging.getLogger('oauthlib').setLevel(logging.WARN)

	try:
		log.info('{name} running.'.format(name=sys.argv[0]))
		log.info('Will tweet every {min} minutes and reply to tweets. Stop with Ctrl+c'.format(min=INTERVAL))
		sched.start()
	# a KeyboardInterrupt exception is generated when the user presses Ctrl+c
	except KeyboardInterrupt:
		print('\nShutting down. Bye!')
