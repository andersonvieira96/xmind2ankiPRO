import json
import zipfile
from os import sep, mkdir, listdir
from os.path import exists, getctime
from shutil import copyfile
from time import strftime, localtime
from typing import List, TypedDict
from warnings import warn


class ParsedNodeFromXmind(TypedDict):
    id: str
    title: str
    children: List[str]
    ancestors: List[str]


class NodeStatus:
    unsaved = 'unsaved'
    saved = 'saved'
    updated = 'updated'


class XmindParser:
    xmind_file_path: str = None
    xmind_json = None

    root = None
    hrefs = None
    parsed_nodes: List[ParsedNodeFromXmind] = None

    back_up_dir_path: str = 'backup'
    latest_backup_xmind_json = None

    def __init__(self, xmind_file_path, back_up_path):

        self.xmind_file_path = xmind_file_path
        if self.xmind_file_path.split('.')[-1] != 'xmind':
            raise Exception('not xmind file')

        self.xmind_json = XmindParser.load_xmind_to_xmind_json(self.xmind_file_path, back_up_path)

        self.back_up_dir_path = back_up_path
        if exists(self.back_up_dir_path) is False:
            mkdir(self.back_up_dir_path)

        self.back_up_dir_path = self.back_up_dir_path + sep + 'xmind'
        if exists(self.back_up_dir_path) is False:
            mkdir(self.back_up_dir_path)
        self.root = XmindParser.get_root(self.xmind_json)
        self.hrefs = self.get_hrefs(self.xmind_json)
        # print(self.hrefs)
        self.parsed_nodes = self.parse_xmind_into_nodes(self.root, self.hrefs, back_up_path)

    @staticmethod
    def load_xmind_to_xmind_json(xmind_file_path, back_up_dir_path):
        with zipfile.ZipFile(xmind_file_path) as zip_out:
            with zip_out.open('content.json') as zip_file:
                xmind_json = zip_file.read()
                for file in zip_out.namelist():
                    if file.startswith('resources/'):
                        zip_out.extract(file, back_up_dir_path)
        xmind_json = json.loads(xmind_json)
        return xmind_json

    @staticmethod
    def get_root(xmind_json):
        return xmind_json[0]['rootTopic']

    @staticmethod
    def get_hrefs(xmind_json):
        return [href['rootTopic'] for href in xmind_json[1:]]

    @staticmethod
    def get_title_from_xmind_node(xmind_node):
        return xmind_node["title"]

    @staticmethod
    def get_image_from_xmind_node(xmind_node, back_up_dir_path):
        try:
            image = xmind_node["image"]
            image = image["src"].replace("xap:", back_up_dir_path + "/")
            return image.replace("/", "\\")
        except:
            return None

    @staticmethod
    def get_id_from_xmind_node(xmind_node):
        return xmind_node["id"]

    @staticmethod
    def get_children_nodes_from_xmind_node(xmind_node, hrefs):
        if "children" not in xmind_node and 'href' not in xmind_node:
            raise Exception('There is no child in {}'.format(XmindParser.get_title_from_xmind_node(xmind_node)))
        elif "children" in xmind_node and 'href' in xmind_node:
            warn('There are both href and children in {}'.format(str(xmind_node)))
            href_node = XmindParser.get_href_of_node_in_new_sheet(xmind_node, hrefs)
            return href_node['children']['attached'] + xmind_node['children']['attached']
        elif "children" not in xmind_node and 'href' in xmind_node:
            href_node = XmindParser.get_href_of_node_in_new_sheet(xmind_node, hrefs)
            return href_node['children']['attached']
        else:
            return xmind_node['children']['attached']

    @staticmethod
    def get_href_of_node_in_new_sheet(current_raw_node: dict, hrefs):
        if 'href' not in current_raw_node:
            raise Exception('There is no href in this node {}'.format(str(current_raw_node)))
        href_id = current_raw_node['href'].split('#')[-1]
        for node in hrefs:
            if node['id'] == href_id:
                return node
        raise Exception('There is no specific id:{} node in hrefs of node {}'.format(href_id, str(current_raw_node)))

    @staticmethod
    def get_children_titles(node, hrefs):
        if "children" not in node and 'href' not in node:
            raise Exception('There is no child in {}'.format(
                XmindParser.get_title_from_xmind_node(node)))
        if 'href' in node:
            return [XmindParser.get_title_from_xmind_node(child) for child in
                    XmindParser.get_children_nodes_from_xmind_node(node, hrefs)]
        return [XmindParser.get_title_from_xmind_node(child) for child in
                XmindParser.get_children_nodes_from_xmind_node(node, hrefs)]

    @staticmethod
    def get_children_images(node, hrefs, back_up_dir_path):
        if "children" not in node and 'href' not in node:
            raise Exception('There is no child in {}'.format(
                XmindParser.get_title_from_xmind_node(node)))
        if 'href' in node:
            return [XmindParser.get_image_from_xmind_node(child, back_up_dir_path) for child in
                    XmindParser.get_children_nodes_from_xmind_node(node, hrefs)]
        return [XmindParser.get_image_from_xmind_node(child, back_up_dir_path) for child in
                XmindParser.get_children_nodes_from_xmind_node(node, hrefs)]

    @staticmethod
    def transform_xmind_node_to_processed_note(node, ancestors, hrefs, back_up_dir_path):
        return {'id': XmindParser.get_id_from_xmind_node(node),
                'title': XmindParser.get_title_from_xmind_node(node),
                'image': XmindParser.get_image_from_xmind_node(node, back_up_dir_path),
                'children': XmindParser.get_children_titles(node, hrefs),
                'children_image': XmindParser.get_children_images(node, hrefs, back_up_dir_path),
                'ancestors': ancestors}

    @staticmethod
    def parse_xmind_into_nodes(root, hrefs, back_up_dir_path):
        ancestor_list_stack = [[]]
        raw_node_stack = [root]
        parsed_nodes = []

        while len(raw_node_stack) != 0:
            node = raw_node_stack.pop()
            current_title = XmindParser.get_title_from_xmind_node(node)
            ancestors = ancestor_list_stack.pop()

            if "children" in node or 'href' in node:
                if "children" in node and len(node['children']) == 0:
                    if 'href' not in node:
                        continue
                parsed_nodes.append(
                    XmindParser.transform_xmind_node_to_processed_note(node, ancestors, hrefs, back_up_dir_path))

                children = XmindParser.get_children_nodes_from_xmind_node(node, hrefs)
                raw_node_stack.extend(reversed(children))
                children_ancestors = ancestors.copy()
                children_ancestors.append(current_title)
                ancestor_list_stack.extend(
                    [children_ancestors for _ in range(len(children))])
            else:
                pass
        return parsed_nodes

    def create_backup_xmind_file(self):
        filename = self.xmind_file_path.split(sep)[-1].split('.')[0]
        dst_path_to_file = self.back_up_dir_path + sep + filename + strftime("%Y%m%d%H%M%S", localtime())
        copyfile(self.xmind_file_path, dst_path_to_file)
        return dst_path_to_file

    def load_and_classify_changes_in_xmind(self):
        current_xmind_nodes = self.parsed_nodes
        last_version_xmind_nodes = self.load_nodes_latest_backup_xmind()
        deleted_nodes_id = set(map(lambda node: node['id'], last_version_xmind_nodes)) - set(
            map(lambda node: node['id'], current_xmind_nodes))
        notes_to_add = set(map(lambda node: node['id'], current_xmind_nodes)) - set(
            map(lambda node: node['id'], last_version_xmind_nodes))
        notes_to_add = [node for node in current_xmind_nodes if node['id'] in notes_to_add]
        id_identical = set(map(lambda node: node['id'], current_xmind_nodes)) & set(
            map(lambda node: node['id'], last_version_xmind_nodes))
        current_xmind_nodes_with_identical_id_in_backup_xmind = list(
            filter(lambda node: node['id'] in id_identical, current_xmind_nodes))

        last_version_xmind_nodes = {node['id']: node for node in last_version_xmind_nodes}
        altered_nodes = [node for node in current_xmind_nodes_with_identical_id_in_backup_xmind if
                         last_version_xmind_nodes[node['id']] != node]

        return list(deleted_nodes_id), notes_to_add, altered_nodes

    def load_nodes_latest_backup_xmind(self):
        backup_files = listdir(self.back_up_dir_path)
        if len(backup_files) == 0:
            return []
        latest_back_up_file = self.back_up_dir_path + sep + max(backup_files, key=lambda filename: getctime(
            self.back_up_dir_path + sep + filename))
        with zipfile.ZipFile(latest_back_up_file) as zip_out:
            with zip_out.open('content.json') as zip_file:
                xmind_json = zip_file.read()
        latest_backup_xmind_json = json.loads(xmind_json)
        backup_xmind_root = XmindParser.get_root(latest_backup_xmind_json)
        backup_xmind_href = XmindParser.get_hrefs(latest_backup_xmind_json)

        return XmindParser.parse_xmind_into_nodes(backup_xmind_root, backup_xmind_href, self.back_up_dir_path)

    def save_xmind_to_file(self):
        back_up_file_path = self.create_backup_xmind_file()

        with zipfile.ZipFile(back_up_file_path, mode='r') as zip_in:
            with zipfile.ZipFile(self.xmind_file_path, mode='w') as zip_out:
                for item in zip_in.infolist():
                    if item.is_dir():
                        continue
                    if item.filename == 'content.json':
                        continue
                    buffer = zip_in.read(item)

                    with zip_out.open(item, mode='w') as zip_file:
                        zip_file.write(buffer)
                with zip_out.open('content.json', mode='w') as zip_file:
                    zip_file.write(bytes(json.dumps(self.xmind_json, ensure_ascii=False), 'utf-8'))
