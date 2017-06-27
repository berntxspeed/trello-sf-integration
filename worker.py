import time
import schedule
from server import refresh_trello

def run_schedule():
    while 1:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    schedule.every(1).hour.do(refresh_trello)
    print('starting thread for updating trello')
    run_schedule()
