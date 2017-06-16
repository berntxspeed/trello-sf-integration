from threading import Thread
import time
import schedule
from server import refresh_trello

def run_schedule():
    while 1:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    schedule.every(5).minutes.do(refresh_trello)
    t = Thread(target=run_schedule)
    t.start()
    print('starting thread for updating trello')
