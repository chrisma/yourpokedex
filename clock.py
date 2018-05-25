from apscheduler.schedulers.blocking import BlockingScheduler
from pokedex_bot import run

sched = BlockingScheduler()

@sched.scheduled_job('interval', minutes=10)
def timed_job():
    run()

sched.start()
