from typing import List

from xmind_parser import ParsedNodeFromXmind


class CvtMode:
    deck_name: str
    tags: List = ['xmind']
    models: List = ['Básico']

    @classmethod
    def transform_node_to_note(cls, node: ParsedNodeFromXmind):
        image : List = []
        front = node['title']
        image.append({"node": node["image"], "side": "Frente"})
        for ancestor in reversed(node['ancestors']):
            front = ancestor + ' -> ' + front
        front = cls.__decorate_string(front)
        back = ''
        for child in node['children']:
            back = back + cls.__decorate_string(child)
        for child in node['children_image']:
            image.append({"node": child, "side": "Verso"})

        return cls.__make_note(fields=cls.__transform_to_common_note_fields(front, back),
                               deck_name=cls.deck_name, model_name=cls.models[0], tags=cls.tags,
                               picture=cls.__make_picture(image))

    @staticmethod
    def __decorate_string(string: str):
        return '<div>' + string + '</div>'

    @staticmethod
    def __transform_to_common_note_fields(front, back):
        return {
            "Frente": front,
            "Verso": back
        }

    def __make_picture(image : List):
        src : List = []
        for img in image:
            if img["node"] is not None:
                src.append({
                    "data": img["node"],
                    "filename": img["node"][0:5],
                    "fields": [img["side"]]
                })
        return src

    @staticmethod
    def __make_note(fields, deck_name: str, model_name: str, tags: List, picture: List):
        return {
            "deckName": deck_name,
            "modelName": model_name,
            "tags": tags,
            "fields": fields,
            "picture" : picture
        }
