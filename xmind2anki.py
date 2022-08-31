import json
from os import sep, mkdir
from os.path import exists, dirname
from typing import List, Tuple

from anki_connect import AnkiConnector, warn_print
from cvtmode.knowledge_for_hunting_jobs import JobInterviewKnowledgeMode
from xmind_parser import XmindParser, ParsedNodeFromXmind


class Courier:
    xmind_parser: XmindParser
    anki_connect: AnkiConnector

    parsed_nodes_from_new_xmind: List[ParsedNodeFromXmind]

    transform_function = None
    deck_name: str

    increased_nodes: List[ParsedNodeFromXmind]
    ids_of_deleted_nodes: List[str]
    altered_nodes: List[ParsedNodeFromXmind]

    id_dictionary_path: str
    dict_for_node_id_and_note_id: dict

    backup_dir = dirname(__file__).replace("library.zip","") + sep + 'backup'

    def __init__(self, xmind_file_path):

        filename = xmind_file_path.split(sep)[-1].split('.')[0]
        self.set_note_type(filename)
        if exists(self.backup_dir) is False:
            mkdir(self.backup_dir)
        self.backup_dir = self.backup_dir + sep + filename
        if exists(self.backup_dir) is False:
            mkdir(self.backup_dir)

        self.xmind_parser = XmindParser(xmind_file_path, back_up_path=self.backup_dir)
        self.anki_connect = AnkiConnector()
        if self.anki_connect.check_connection() is False:
            print('anki is not connecting.')
            exit(-1)
        self.parsed_nodes_from_new_xmind = self.xmind_parser.parsed_nodes

        self.id_dictionary_path = self.backup_dir + sep + 'id_dictionary'

        if exists(self.id_dictionary_path) is False:

            with open(self.id_dictionary_path, 'w') as f:
                json.dump(dict(), f)
                self.dict_for_node_id_and_note_id = {}
        else:
            with open(self.id_dictionary_path, 'r') as f:
                self.dict_for_node_id_and_note_id = json.load(f)

    def transform_parsed_nodes_into_notes(self, nodes):
        if self.transform_function is None:
            raise Exception('Note type is not set yet.')
        notes_transformed_from_parsed_nodes = [self.transform_function(node) for node in nodes]
        return notes_transformed_from_parsed_nodes

    def set_note_type(self, deck_name: str):
        self.transform_function = JobInterviewKnowledgeMode.transform_node_to_note
        self.deck_name = deck_name
        JobInterviewKnowledgeMode.deck_name = deck_name

    def update_changes_from_xmind(self):
        changes_from_xmind: Tuple[
            str, ParsedNodeFromXmind, ParsedNodeFromXmind] = self.xmind_parser.load_and_classify_changes_in_xmind()
        self.ids_of_deleted_nodes, self.increased_nodes, self.altered_nodes = changes_from_xmind
        return changes_from_xmind

    def upload_new_notes_to_anki(self):
        new_notes = self.transform_parsed_nodes_into_notes(self.increased_nodes)
        note_id_list = self.anki_connect.add_notes(new_notes)

        failed_nodes = []
        for node, note_id in zip(self.increased_nodes, note_id_list):
            if note_id is None:
                failed_nodes.append(node)
                warn_print('Fail to import {} into anki'.format(str(node)))
            if self.dict_for_node_id_and_note_id.get(node['id']) is not None:
                raise Exception('There is an identical id in the id dictionary.')
            self.dict_for_node_id_and_note_id[node['id']] = note_id
        with open(self.id_dictionary_path, 'w') as f:
            json.dump(self.dict_for_node_id_and_note_id, f)
        return failed_nodes

    def upload_changed_notes_to_anki(self):
        altered_notes = self.transform_parsed_nodes_into_notes(self.altered_nodes)
        for note, node in zip(altered_notes, self.altered_nodes):
            note_id = self.dict_for_node_id_and_note_id[node['id']]
            if note_id is None:
                raise Exception('There is no specific note id of node {}'.format(node['id']))
            self.anki_connect.update_note(note_id=note_id, note=note)

    def delete_notes_in_anki(self):

        ids_of_notes_to_delete_in_anki = []
        for node_id in self.ids_of_deleted_nodes:
            id_of_notes_to_delete_in_anki = self.dict_for_node_id_and_note_id.get(node_id)
            if id_of_notes_to_delete_in_anki is None:
                raise Exception('The node to delete does not exist.')
            ids_of_notes_to_delete_in_anki.append(id_of_notes_to_delete_in_anki)
            self.dict_for_node_id_and_note_id.pop(node_id)
        self.anki_connect.delete_notes(ids_of_notes_to_delete_in_anki)


    def back_up_anki(self):
        anki_back_up_dir = self.backup_dir + sep + 'anki'
        if exists(anki_back_up_dir) is False:
            mkdir(anki_back_up_dir)
        self.anki_connect.backup_deck(deck_name=self.deck_name, backup_dir=anki_back_up_dir)

    def create_deck_anki(self):
        self.anki_connect.create_deck(deck_name=self.deck_name)

    def upload_all_changes_to_anki(self):
        self.create_deck_anki()

        self.update_changes_from_xmind()
        self.back_up_anki()

        self.delete_notes_in_anki()
        self.upload_new_notes_to_anki()
        self.upload_changed_notes_to_anki()
        self.xmind_parser.create_backup_xmind_file()


if __name__ == '__main__':
    test_xmind_file_path: str = r'E:\MyLibrary\Hunt4job\找工altered - Copy.xmind'
    courier = Courier(test_xmind_file_path)
    courier.set_note_type('tiw')
    courier.upload_all_changes_to_anki()
