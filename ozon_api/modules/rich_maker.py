import json
import logging

import app

try:
    import requests
except ModuleNotFoundError:
    import pip
    pip.main(['install', 'requests'])
    import requests
try:
    from json import dumps
except ModuleNotFoundError:
    import pip
    pip.main(['install', 'json'])
    from json import dumps
try:
    import cv2
except ModuleNotFoundError:
    import pip
    pip.main(['install', 'opencv-python'])
    import cv2
import numpy as np
try:
    import bs4
except ModuleNotFoundError:
    pass
import time


def start(auth_list):
    print(f'Начали процедуру :: {time.asctime()}')
    for head in auth_list[1:2]:
        print(f'Начали кабинет {head["Client-Id"]} :: {time.asctime()}')
        check_rich(head)


def check_rich(auth, offers: [list, None] = None):
    session = requests.session()
    session.headers = auth
    url = 'https://api-seller.ozon.ru/v3/products/info/attributes'
    if offers is None:
        body = {
            "filter": {
                "visibility": "ALL"
            },
            "limit": 1000,
            "last_id": "",
            "sort_dir": "ASC"
        }
    else:
        body = {
            "filter": {
                'offer_id': offers,
                "visibility": "ALL"
            },
            "limit": 1000,
            "last_id": "",
            "sort_dir": "ASC"
        }

    pack_count = 1
    attributes_list = []
    # print(f'Начинаем загрузку атрибутов {time.asctime()}')
    while True:
        # print(f'Отправляем пакет :: {pack_count} - {time.asctime()}')
        resp = session.post(url=url, data=dumps(body))
        if resp.status_code == 404:
            # print(f'Закончили получение атрибутов по кабинету {auth["Client-Id"]} - {time.asctime()}')
            break
        elif resp.status_code != 200:
            # print(f'Словили ошибку ответа. Время - {time.asctime()}')
            logging.error(f'Запрос\n{body}\n\n\nОтвет\n{resp.text}\n\n\nХидеры\n{resp.headers}')
            break
        data = resp.json()
        if not data:
            return 'Ни один из представленных артикулов не найден в кабинете'
        attributes_list.extend(data['result'])
        body['last_id'] = data['last_id']
        pack_count += 1
    target_cards = [c for c in attributes_list[:1000] if (c['images']) and (11254 not in [f['attribute_id'] for f in c['attributes']])]
    pack = 500
    cards_to_import = []
    if not target_cards:
        return 'Не найдено ни одной карточки без рич контента'
    while target_cards:
        base_data = []
        for c in range(pack):
            try:
                base_data.append(target_cards.pop())
            except IndexError:
                break
        resp_prices = session.post(url='https://api-seller.ozon.ru/v2/product/info/list',
                                   data=dumps({'offer_id': [c['offer_id'] for c in base_data]})).json()['result']['items']
        for data in base_data:
            resp_price = [c for c in resp_prices if c['offer_id'] == data['offer_id']][0]
            attrs = [{'id': c['attribute_id'], 'complex_id': c['complex_id'], 'values': c['values']} for c
                                   in data['attributes']]
            annotation_attr = [c for c in data['attributes'] if c['attribute_id'] == 4191]
            annotation = annotation_attr[0]['values'][0]['value'] if annotation_attr else None
            rich = form_rich(data['name'], data['images'][0]['file_name'], annotation)
            attrs.append(rich)
            cards_to_import.append(
                {
                    "attributes": attrs,
                    "barcode": data.setdefault('barcode', ''),
                    "category_id": data.setdefault('category_id', ''),
                    "color_image": data.setdefault("color_image", ''),
                    "complex_attributes": [c for c in data["complex_attributes"]],
                    "depth": data.setdefault("depth", ''),
                    "dimension_unit": data.setdefault("dimension_unit", ''),
                    "height": data.setdefault("height", ''),
                    "images360": [c['file_name'] for c in data['images360']],
                    "name": data["name"],
                    "offer_id": data["offer_id"],
                    "old_price": resp_price.setdefault("old_price", ''),
                    "pdf_list": data["pdf_list"],
                    "premium_price": resp_price.setdefault("premium_price", ''),
                    "price": resp_price.setdefault("price"),
                    "primary_image": [c for c in data['images'] if (c['index'] == 0) or (c['default'])][0]['file_name'],
                    "images": [c['file_name'] for c in data["images"]],
                    "vat": resp_price.setdefault("vat", '0.2'),
                    "weight": data["weight"],
                    "weight_unit": data["weight_unit"],
                    "width": data["width"]
                }
            )
    pack = 1
    errors = []
    while cards_to_import:
        data = []
        for c in range(pack):
            try:
                data.append(cards_to_import.pop())
            except IndexError:
                break
        resp = session.post(url='https://api-seller.ozon.ru/v2/product/import', json={'items': data})
        if resp.status_code != 200:
            errors.append(data)
            continue
    if errors:
        app.log.error(errors)
        return 'Не смогли сформировать рич по данным артикулам. Пожалуйста передайте данные в айти для разбора деталей.'


def form_rich(name, url, annotation: str = None):
    img_resp = requests.get(url)
    img = cv2.imdecode(np.asarray(bytearray(img_resp.content)), cv2.IMREAD_COLOR)
    max_val = max(img.shape[0], img.shape[1])
    if annotation is not None:
        annotation = annotation.replace('<br>', '\n').replace('<br/>', '\n')
        try:
            ann = bs4.BeautifulSoup(annotation, features="lxml")
            annotation = ann.text
        except ModuleNotFoundError:
            pass
    rich = {'content': [
        {'widgetName': 'raShowcase',
         'type': 'roll',
         'blocks': [
             {'imgLink': '',
              'img': {'src': url,
                      'srcMobile': url,
                      'alt': name,
                      'width': img.shape[1],
                      'height': img.shape[0],
                      'widthMobile': max_val,
                      'heightMobile': max_val}
              }]}],
        'version': 0.3}
    if annotation is not None:
        # noinspection PyTypeChecker
        rich['content'].append({'widgetName': 'list',
                                'theme': 'bullet',
                                'blocks': [{'text': {'size': 'size2',
                                                     'align': 'left',
                                                     'color': 'color1',
                                                     'content': annotation.split('\n')},
                                            'title': {'content': ['Описание'],
                                                      'size': 'size4',
                                                      'align': 'left',
                                                      'color': 'color1'}}]})
    res = {'id': 11254,
           'complex_id': 0,
           'values': [
               {'dictionary_value_id': 0,
                'value': json.dumps(rich, ensure_ascii=False,)
            }]}
    return res


if __name__ == '__main__':
    heads = [
        {'Client-Id': '2523', 'Api-Key': '2136fa7b-e156-489f-94e7-fcf1e4f4bb8e'},
        {'Client-Id': '461420', 'Api-Key': 'ce3b2a21-5acd-482d-b61e-21650b00b64a'},
        {'Client-Id': '4007', 'Api-Key': 'bfd42883-dff0-4423-bb6d-dfa597e287d1'},
        {'Client-Id': '341020', 'Api-Key': 'ce21dfd4-f7c7-46a5-b0e9-966992b72408'},
        {'Client-Id': '230929', 'Api-Key': '66d1fe02-b0b9-4848-9bea-865606ac487b'},
        {'Client-Id': '22894', 'Api-Key': '18652e2c-1fbf-4fa9-a3b6-55c16091a26f'},
        {'Client-Id': '221957', 'Api-Key': 'c9f6e1af-d166-49a7-9923-836d745d0ba2'},
        {'Client-Id': '150565', 'Api-Key': '3c06412f-f368-408b-bbe2-1ce019c41caa'},
        {'Client-Id': '134376', 'Api-Key': '5f68812a-6713-4eef-87b2-29dc8d8e34ca'},
        {'Client-Id': '125665', 'Api-Key': '704f1cd8-acbd-4a3d-8487-e6696e30bd3c'},
        {'Client-Id': '113062', 'Api-Key': '56dfab75-3098-4be7-bb2c-20217fc858ff'},
    ]
    start(heads)

