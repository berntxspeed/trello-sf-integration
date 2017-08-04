import time
import schedule
from server import refresh_trello, clear_trigger_log_table

def run_schedule():
    while 1:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    schedule.every(4).hours.do(refresh_trello)
    schedule.every(8).hours.do(clear_trigger_log_table)
    print('starting thread for updating trello')
    run_schedule()
