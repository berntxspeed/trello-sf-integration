import os
import sys
import logging
from flask import Flask
import requests
import dataset

try:
    config = {
        'sfapi_consumer_key': os.environ.get('SFAPI_CONSUMER_KEY'),
        'sfapi_consumer_secret': os.environ.get('SFAPI_CONSUMER_SECRET'),
        'enable_verbose_logging': os.environ.get('ENABLE_VERBOSE_LOGGING', None),
        'database_url': os.environ.get('DATABASE_URL'),
        'trello_api_key': os.environ.get('TRELLO_API_KEY'),
        'trello_api_token': os.environ.get('TRELLO_API_TOKEN'),
        'trello_api_username': os.environ.get('TRELLO_API_USERNAME'),
        'trello_base_api': os.environ.get('TRELLO_API_BASE_API')
    }
    if config['enable_verbose_logging'] is not None:
        logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
except Exception as e:
    print('missing an environment variable: ' + repr(e))
    raise

app = Flask(__name__)

@app.route('/')
def hello():
    with dataset.connect(config['database_url'], schema='salesforce') as db:
        acct_table = db['account']
        task_table = db['task']
        record_type_table = db['recordtype']

        trello_record_type = record_type_table.find_one(name='Trello')
        if trello_record_type is None:
            raise ValueError('missing Trello record type for Task. check SF and add if not there already.')

        # get boards from trello
        endpoint = '/members/'+config['trello_api_username']+'/boards'
        payload = {'key': config['trello_api_key'], 'token': config['trello_api_token']}
        r = requests.get(config['trello_base_api'] + endpoint, params=payload)
        if r.status_code != 200:
            raise ValueError('trello boards request errored')
        boards = r.json()
        # loop thru boards
        for board in boards:
            print('processing board: ' + board['name'])
            # search for acct matching board
            acct = acct_table.find_one(name=board['name'])
            if acct is not None:
                endpoint = '/board/' + board['id'] + '/cards'
                r = requests.get(config['trello_base_api'] + endpoint, params=payload)
                cards = r.json()
                if r.status_code != 200:
                    raise ValueError('trello cards request for board id: ' + board['id'] + ' errored')
                endpoint = '/board/' + board['id'] + '/actions'
                r = requests.get(config['trello_base_api'] + endpoint, params=payload)
                card_actions = r.json()
                # organize card_actions into dict by card id, and select for only comment type
                card_comments = dict()
                for card_action in card_actions:
                    if card_action['type'] == 'commentCard':
                        card_id = card_action['data']['card']['id']
                        temp = card_comments.get(card_id, [])
                        temp.append(card_action)
                        card_comments[card_id] = temp
                if r.status_code != 200:
                    raise ValueError('trello card actions request for board id: ' + board['id'] + ' errrored')
                # loop thru board's cards
                for card in cards:
                    # calculate card status from checkItems status
                    task_status = 'Not Started'
                    check_items = card['badges']['checkItems']
                    check_items_checked = card['badges']['checkItemsChecked']
                    if check_items == 0 or check_items_checked == 0:
                        task_status = 'Not Started'
                    elif check_items_checked > 0 and check_items_checked < check_items:
                        task_status = 'In Progress'
                    elif check_items_checked == check_items:
                        task_status = 'Completed'
                    else:
                        task_status = 'Open'

                    task_desc = '----------Card Description:\n' + card['desc'] + '\n\n'
                    task_desc = task_desc + '----------Card Progress:\n' + str(check_items_checked) + ' checked out of ' + str(check_items) + '\n\n'

                    if card['id'] in card_comments:
                        task_desc = task_desc + '----------Most recent Comments (3):\n\n'
                        for comment in card_comments.get(card['id'])[:3]:
                            task_desc = task_desc + comment['date'] + ' by user: ' + comment['memberCreator']['fullName'] + '\n'
                            task_desc = task_desc + comment['data']['text'] + '\n\n'

                    # search for task with matching Trello_Card_ID__c
                    task = task_table.find_one(trello_card_id__c=card['id'], recordtypeid=trello_record_type['sfid'])
                    if task is not None:
                        # *** update task with new card info
                        task['activitydate'] = card['due']
                        task['status'] = task_status
                        task['subject'] = card['name']
                        task['description'] = task_desc

                        task_table.update(task, ['id'])
                        print('updating task with subject: ' + task['subject'] + ' on board: ' + board['name'])
                    else:
                        # *** create new task with card info
                        task = dict(whatid=acct['sfid'],
                                    recordtypeid=trello_record_type['sfid'],
                                    trello_card_id__c=card['id'],
                                    activitydate=card['due'],
                                    status=task_status,
                                    subject=card['name'],
                                    description=task_desc)
                        task_table.insert(task)
                        print('creating new task with subject: ' + task['subject'] + ' on board: ' + board['name'])

    return 'completed update'
