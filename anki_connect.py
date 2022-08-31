import datetime
import json
import urllib.error
import urllib.request
import warnings
from os import sep
from time import strftime, localtime
from typing import Dict, List


def singleton(cls):
    _instance = {}

    def inner(**params):
        if cls not in _instance:
            _instance[cls] = cls(**params)
        return _instance[cls]

    return inner


def get_model_fields(model_name):
    result = invoke("modelFieldNames", modelName=model_name)
    return result


def get_deck_name():
    return invoke("deckNames")["result"]



def record_failed_data(params):
    data_time = datetime.datetime
    with open('FailedData/failed_data' + data_time.now().strftime("%Y%m%d%H%m") + '.json', 'a+', encoding='utf8') as f:
        json.dump(params, f, ensure_ascii=False)


def warn_print(string):
    class TerminalColors:
        HEADER = '\033[95m'
        OKBLUE = '\033[94m'
        OKCYAN = '\033[96m'
        OKGREEN = '\033[92m'
        WARNING = '\033[93m'
        FAIL = '\033[91m'
        ENDC = '\033[0m'
        BOLD = '\033[1m'
        UNDERLINE = '\033[4m'

    print(TerminalColors.FAIL + string + TerminalColors.ENDC)


class AnkiConnector:

    @staticmethod
    def request(action, **params):
        return {'action': action, 'params': params, 'version': 6}

    @staticmethod
    def invoke(action, **params):
        request_json = json.dumps(AnkiConnector.request(action, **params), ensure_ascii=False).encode('utf-8')
        response = json.load(urllib.request.urlopen(urllib.request.Request('http://localhost:8765', request_json)))
        warnings.simplefilter("always")
        failed_data = []
        if len(response) != 2:
            print(params)
            params['message'] = "One conversion failed due to an unexpected number of fields"
            failed_data.append(params)
            warn_print("One conversion failed due to an unexpected number of fields")
        if 'error' not in response:
            print(params)
            params['message'] = "One conversion failed due to missing required error field"
            failed_data.append(params)
            warn_print("One conversion failed due to missing required error field")
        if 'result' not in response:
            print(params)
            params['message'] = "One conversion failed due to missing required error field"
            failed_data.append(params)
            warn_print("One conversion failed due to missing required error field")
        if response['error'] is not None:
            print(params)
            params['message'] = response['error']
            failed_data.append(params)
            warn_print(response['error'])
#        record_failed_data(failed_data)
        return response

    @staticmethod
    def find_notes(model=None, deck_name=None, fields: Dict = None):
        model: str = model
        query = []
        if deck_name is not None:
            query.append('note:\'' + deck_name + '\'')
        if model is not None:
            query.append('note:\'' + model + '\'')
        if fields is not None:
            for field_name, field in fields.items():
                query.append(field_name + ':' + field)
        return AnkiConnector.invoke(action="findNotes", params={
            'query': ' '.join(query)
        })

    @staticmethod
    def check_connection():
        try:
            urllib.request.urlopen("http://localhost:8765")
        except WindowsError:
            return False
        return True

    @staticmethod
    def add_note(note):
        anki_note_id = AnkiConnector.invoke("addNote", note=note)['result']
        return anki_note_id

    @staticmethod
    def add_notes(notes: List):
        anki_notes_id = AnkiConnector.invoke("addNotes", notes=notes)['result']
        return anki_notes_id

    @staticmethod
    def delete_notes(ids_of_notes_to_delete: List):
        AnkiConnector.invoke('deleteNotes', notes=ids_of_notes_to_delete)

    @staticmethod
    def update_note(note_id, note):
        note['id'] = note_id
        AnkiConnector.invoke("updateNoteFields", note=note)

    @staticmethod
    def backup_deck(deck_name, backup_dir):
        backup_path = backup_dir + sep + deck_name + '_' + strftime("%Y%m%d%H%M%S", localtime()) + '.apkg'
        AnkiConnector.invoke('exportPackage', deck=deck_name, path=backup_path, includeSched=True)

    @staticmethod
    def create_deck(deck_name: str):
        existing_deck = AnkiConnector.invoke('deckNames')
        if deck_name in existing_deck:
            raise Exception('Deck {} has already existed.')
        else:
            AnkiConnector.invoke('createDeck', deck=deck_name)
