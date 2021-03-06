import os
import sys
import logging
from flask import Flask
import requests
import dataset
import time

try:
    # trello mode should be either personal or org (depending on if Organizations are enabled in the account)
    config = {
        'enable_verbose_logging': os.environ.get('ENABLE_VERBOSE_LOGGING', None),
        'database_url': os.environ.get('DATABASE_URL'),
        'trello_api_key': os.environ.get('TRELLO_API_KEY'),
        'trello_api_token': os.environ.get('TRELLO_API_TOKEN'),
        'trello_api_username': os.environ.get('TRELLO_API_USERNAME', None),
        'trello_base_api': os.environ.get('TRELLO_API_BASE_API'),
        'trello_org_id': os.environ.get('TRELLO_ORG_ID', None),
        'trello_mode': os.environ.get('TRELLO_MODE')
    }
    if config['enable_verbose_logging'] is not None:
        logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
except Exception as e:
    print('missing an environment variable: ' + repr(e))
    raise

app = Flask(__name__)

@app.route('/')
def hello():
    return 'Hello World'

def refresh_trello():
    with dataset.connect(config['database_url'], schema='salesforce') as db:
        acct_table = db['account']
        card_table = db['trello_card__c']

        #IDEA: clear out any tasks that have SF errors and thus don't have sfid values (sfid=None)
        #task_table.delete(sfid=None, recordtypeid=trello_record_type['sfid'])

        # get boards from trello
        if config['trello_mode'] == 'org':
            if config['trello_org_id'] is None:
                raise ValueError('must supply a value for TRELLO_ORG_ID')
            endpoint = '/organizations/' + config['trello_org_id'] + '/boards'
        elif config['trello_mode'] == 'personal':
            if config['trello_api_username'] is None:
                raise ValueError('must supply a value for TRELLO_API_USERNAME')
            endpoint = '/members/' + config['trello_api_username'] + '/boards'
        else:
            raise ValueError('invalid setting for TRELLO_MODE.  must be either org or personal')
        payload = {'key': config['trello_api_key'], 'token': config['trello_api_token']}
        r = requests.get(config['trello_base_api'] + endpoint, params=payload)
        if r.status_code != 200:
            raise ValueError('trello boards request errored')
        boards = r.json()
        # loop thru boards
        for board in boards:
            time.sleep(1)
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

                    task_desc = '---Card Progress:\n' + str(check_items_checked) + ' checked out of ' + str(check_items) + '\n\n'
                    task_desc = task_desc + '---Card Description:\n' + card['desc'] + '\n\n'

                    if card['id'] in card_comments:
                        task_desc = task_desc + '---Most recent Comments (3):\n\n'
                        for comment in card_comments.get(card['id'])[:3]:
                            task_desc = task_desc + comment['date'] + ' by user: ' + comment['memberCreator']['fullName'] + '\n'
                            task_desc = task_desc + comment['data']['text'] + '\n\n'

                    # search for task with matching Trello_Card_ID__c
                    task = card_table.find_one(trello_card_id__c=card['id'])
                    if task is not None:
                        # *** update task with new card info
                        task['due__c'] = card['due']
                        task['status__c'] = task_status
                        task['name'] = card['name'][:80]
                        task['description__c'] = task_desc

                        card_table.update(task, ['id'])
                        print('updating task with subject: ' + task['name'] + ' on board: ' + board['name'])
                    else:
                        # *** create new task with card info

                        #IDEA: set createdDate on sf task to card created date?
                        task = dict(account__c=acct['sfid'],
                                    trello_card_id__c=card['id'],
                                    due__c=card['due'],
                                    status__c=task_status,
                                    name=card['name'][:80],
                                    description__c=task_desc)
                        card_table.insert(task)
                        print('creating new task with subject: ' + task['name'] + ' on board: ' + board['name'])

    print('completed update')

def clear_trigger_log_table():
    print('starting periodic process to delete SF _trigger_log records')

    with dataset.connect(config['database_url'], schema='salesforce') as db:

        trigger_log_table = db['_trigger_log']
        if trigger_log_table.delete():
            print('successfully deleted all SF _trigger_log records')
        else:
            print('failed to delete SF _trigger_log records')

        trigger_log_archive_table = db['_trigger_log_archive']
        if trigger_log_archive_table.delete():
            print('successfully deleted all SF _trigger_log_archive records')
        else:
            print('failed to delete SF _trigger_log_archive records')
