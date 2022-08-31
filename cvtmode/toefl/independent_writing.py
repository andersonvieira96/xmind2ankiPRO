from typing import List

from xmind_parser import ParsedNodeFromXmind

deck_name = 'Padrão'


def transform_node_to_note(node: ParsedNodeFromXmind):
    phrase_model_name = '托福-主题-表达'
    outline_model_name = '托福-主题-思路'
    outline_and_phrase_model_name = "托福-主题-词组-思路"  # advanced_mode
    tags = ['xmind']
    children = node['children']
    en_children = []
    cn_children = []

    for child in children:
        if not __is_chinese(child):
            en_children.append(child)
        else:
            cn_children.append(child)

    message_shown_when_questioning = node['title']

    for ancestor in reversed(node['ancestors']):
        message_shown_when_questioning = ancestor + ' -> ' + message_shown_when_questioning
    message_shown_when_questioning = __decorate_string(message_shown_when_questioning)

    if len(cn_children) != 0 and len(en_children) != 0:
        phrase = ''
        des_ideas = ''
        for en_child in en_children:
            phrase = phrase + __decorate_string(en_child)
        for cn_child in cn_children:
            des_ideas = des_ideas + __decorate_string(cn_child)

        return __note_add_detail(__note_type_for_writing_outline(message_shown_when_questioning, phrase, des_ideas),
                                 deck_name, model_name=outline_and_phrase_model_name, tags=tags)

    elif len(cn_children) != 0 and len(en_children) == 0:
        back = ''
        for cn_child in cn_children:
            back = back + __decorate_string(cn_child)
        return __note_add_detail(__common_note(front=message_shown_when_questioning, back=back),
                                 deck_name, model_name=outline_model_name, tags=tags)
    elif len(cn_children) == 0 and len(en_children) != 0:
        back = ''
        for en_child in en_children:
            back = back + __decorate_string(en_child)
        return __note_add_detail(__common_note(front=message_shown_when_questioning, back=back),
                                 deck_name, model_name=phrase_model_name, tags=tags)
    else:
        pass


def __is_chinese(string):
    for _char in string:
        if '\u4e00' <= _char <= '\u9fa5':
            return True
    return False


def __note_type_for_writing_outline(title, phrases, des_ideas):
    return {
        "正面": title,
        "背面": phrases,
        "思路": des_ideas
    }


def __common_note(front, back):
    return {
        "正面": front,
        "背面": back
    }


def __note_add_detail(nt, deck_name: str, model_name: str, tags: List):
    return {
        "deckName": deck_name,
        "modelName": model_name,
        "tags": tags,
        "fields": nt
    }


def __decorate_string(string: str):
    return '<div>' + string + '</div>'
