import time
from json import dumps
import requests
# from modules.main_logger import log
from .static_data import heads, auth as heads, auth



class Result:
	def __init__(self):
		self.errors = []
		self.success = []
		self.data = []
		self.__created = time.asctime()
		self.__updated = None

	def __setattr__(self, key, value):
		super().__setattr__('__updated', time.asctime())
		super().__setattr__(key, value)

	def __repr__(self):
		return str({'errors': self.errors, 'success': self.success, 'data': self.data, 'created': self.__created})


def get_ozon_card(client_id: int, offers=None, visiblity: str = 'ALL', limit: int = 500, unchanged: bool = False) -> Result:
	client_id = int(client_id)
	result = Result()
	if offers is None:
		offers = []
	attrs = get_ozon_attributes(client_id, offers, visiblity, limit)
	result.errors += attrs.errors
	price = get_ozon_main_chars(client_id, attrs.success, limit)
	result.errors += price.errors
	data_main = {c['offer_id']: {'attrs': c} for c in attrs.data}
	for c in price.data:
		data_main[c['offer_id']]['main_inf'] = c
	if unchanged:
		result.success += [c for c in data_main.keys()]
		result.data += data_main
	else:
		for item in data_main.values():
			data = item['attrs']
			resp_price = item['main_inf']
			try:
				pr_image = data["primary_image"] if 'primary_image' in data.keys() else data['images'][0]['file_name']
			except IndexError:
				pr_image = ''
				result.errors += [{'id': data['offer_id'], 'error': 'Отсутствует изображение'}]
			try:
				result.data += [{
					"attributes": [
						{'id': c['attribute_id'], 'complex_id': c['complex_id'], 'values': c['values']}
						for c in data['attributes']
					],
					"barcode": data.setdefault('barcode', ''),
					"category_id": data.setdefault('category_id', ''),
					"color_image": data.setdefault("color_image", ''),
					"complex_attributes": [
						{'attributes': [
							{'complex_id': f['complex_id'], 'id': f['attribute_id'], 'values':f['values']}
							for f in c['attributes']
						]}
						for c in data["complex_attributes"]
					],
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
					"primary_image": pr_image,
					"images": [c['file_name'] for c in data["images"]],
					"vat": resp_price.setdefault("vat", '0.2'),
					"weight": data["weight"],
					"weight_unit": data["weight_unit"],
					"width": data["width"]
				}]
				result.success += [data['offer_id']]
			except Exception as Ex:
				log.error(Ex, stack_info=True, exc_info=True)
				result.errors += {'id': data['offer_id'], 'error': f'Непредвиденная ошибка при сборке карточки - {Ex}'}
	catched = result.success + [c['id'] for c in result.errors]
	not_found = [c for c in offers if c not in catched]
	result.errors += [{'id': c, 'error': 'Артикул не найден при сборке карточки'} for c in not_found]
	return result


def get_ozon_attributes(client_id: int, offers=None, visiblity: str = 'ALL', limit: int = 500) -> Result:
	client_id = int(client_id)
	result = Result()
	if offers is None:
		offers = []
	head = heads[client_id]
	url = 'https://api-seller.ozon.ru/v3/products/info/attributes'
	body = {
		"filter": {
			"offer_id": offers,
			"visibility": visiblity
		},
		"limit": limit,
		"last_id": "",
		"sort_dir": "ASC"
	}
	while True:
		resp = requests.post(url=url, data=dumps(body), headers=head)
		if resp.status_code == 404:
			break
		elif resp.status_code != 200:
			log.error(f', ответ :: {resp.text}')
			result.errors += [
				{'id': c, 'error': 'Ошибка получения данных по атрибутам из Озон'}
				for c in body['filter']['offer_id']
			]
			break
		response_json = resp.json()
		if not response_json['result']:
			break
		for item in response_json['result']:
			result.data += [item]
			result.success += [item['offer_id']]
		body['last_id'] = response_json['last_id']
	if offers:
		catched = result.success + [c['id'] for c in result.errors]
		not_found = [c for c in offers if c not in catched]
		result.errors += [{'id': c, 'error': 'Артикул не найден в ответе запроса атрибутов'} for c in not_found]
	return result


def get_ozon_main_chars(client_id, offers, limit: int = 500) -> Result:
	client_id = int(client_id)
	result = Result()
	if limit > 1000:
		limit = 1000
	url = 'https://api-seller.ozon.ru/v2/product/info/list'
	for i in range(500):
		body = {
			'offer_id': offers[i * limit: (i + 1) * limit]
		}
		if not body['offer_id']:
			break
		resp = requests.post(url, headers=heads[client_id], data=dumps(body))
		if resp.status_code != 200:
			log.error(f'Запрос: {body}\n\nОтвет: {resp.text}\n\nЗаголовки ответа: {resp.headers}\n\n')
			result.errors += [
				{
					'id': c,
					'error': 'Не смогли получить основные атрибуты по карточкам - не корректный ответ Озон'}
				for c in body["offer_id"]
			]
			continue
		data = resp.json()['result']['items']
		for item in data:
			result.data += [item]
			result.success += [item['offer_id']]
	catched = result.success + [c['id'] for c in result.errors]
	not_found = [c for c in offers if c not in catched]
	result.errors += [
		{'id': c, 'error': 'Карточка не найдена в ответе озон при получении основных данных'}
		for c in not_found
	]
	return result


def change_attr(card: dict, attr_to_change: dict):
	"""
	incoming attributes format: {
		<attr_id>: <full attribute body> (<- will be send to Ozone without changes)
	}
	"""
	try:
		attrs = {c['id']: c for c in card['attributes']}
		for new_attr in attr_to_change:
			attrs[new_attr['id']] = new_attr
		card['attributes'] = [c for c in attrs.values()]
		return card
	except Exception as Ex:
		log.error(Ex)
		raise Ex


def change_complex_attr(card: dict, attr_to_change: list):
	"""
	incoming attributes format: [<full attribute body> (<- will be sent to Ozone without changes)]
	"""
	try:
		# Разбираем в словарь
		attrs = {
			c['attributes'][0]['complex_id']: {
				f['id']: f for f in c['attributes']
			}
			for c in card['complex_attributes']
		}
		# Дополняем словарь
		for attr in attr_to_change:
			comp_id = attr['complex_id']
			attr_id = attr['id']
			attrs.setdefault(comp_id, {})[attr_id] = attr
		# Собираем обратно в список с исходной структурой
		new_attrs = [
			{'attributes': [attrs[comp_id][attr_id] for attr_id in attrs[comp_id]]} for comp_id in attrs
		]
		card['complex_attributes'] = new_attrs
		return card
	except Exception as Ex:
		log.error(Ex)
		raise Ex


def add_video(card: dict, video: list) -> dict:
	res = [
		{
			"complex_id": 4018,
			"id": 4074,
			"values": [
				{
					"value": val
				}
				for val in video
			]
		},
		{
			"complex_id": 4018,
			"id": 4068,
			"values": [
				{
					"value": f"video_name_{num}"
				}
				for num, _ in enumerate(video)
			]
		}
	]
	return change_complex_attr(card, res)


def videos(client_id: int, offers_with_videos: dict, limit: int = 500):
	client_id = int(client_id)
	result = Result()
	offers = [c for c in offers_with_videos.keys()]
	cards = get_ozon_card(client_id, offers)
	result.errors += cards.errors
	new_cards = [add_video(card, offers_with_videos[card['offer_id']]) for card in cards.data]
	send_result = send_to_import(client_id, new_cards)
	result.errors += send_result.errors
	return result


def send_to_import(client_id: int, offers: list, limit: int = 100):
	client_id = int(client_id)
	result = Result()
	url = 'https://api-seller.ozon.ru/v2/product/import'
	head = heads[client_id]
	for i in range(500):
		offers_slice = offers[i * limit: (i + 1) * limit]
		if not offers_slice:
			break
		resp = requests.post(url=url, data=dumps({'items': offers_slice}), headers=head)
		if resp.status_code != 200:
			# log.error(
			# 	f'Ошибка отправки характеристик, заголовки<br> '
			# 	f'{head}<br><br>'
			# 	f'Ответ<br>'
			# 	f'{resp.text}<br><br>'
			# 	f'Запрос<br>'
			# 	f'{resp.request.body}')
			result.errors += [
				{
					'id': c['offer_id'],
					'error': 'Ошибка при импорте товаров, неверный ответ озон'
				} for c in offers_slice
			]
			continue
		result.success += [c['offer_id'] for c in offers_slice]
		result.data += [resp.json()]
	return result


def extract_content_ratings() -> Result:
	# auth = auth
	session = requests.session()
	session.headers['user-agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0'
	resp = session.post('https://seller.ozon.ru/api/site/user/login', json=auth)
	session.headers['accesstoken'] = resp.json()['result']['access_token']
	c_url = 'https://seller.ozon.ru/api/content-rater/rating/get-by-sku'
	pl_url = 'https://seller.ozon.ru/api/site/product/list'
	cab_list = [4007, 230929, 22894, 221957, 150565, 134376, 125665, 2523]
	res = Result()
	res.data = dict()
	for cab in cab_list:
		res = set()
		session.headers['x-o3-company-id'] = str(cab)
		body = {
			"fields": ["COMMISSIONS"],
			"sort_by": "created_at",
			"sort_dir": "DESC",
			"company_id": cab,
			"language": "RU",
			"page": 1,
			"page_size": 1000,
			"from": 0,
			"limit": 1000,
			"last_id": ""
		}
		resp = session.post(pl_url, json=body)
		dictionary = {}
		count = 1
		while True:
			data = resp.json()
			for c in data['items']:
				dictionary[c['sku']] = c['offer_id']
			res = res.union({c['sku'] for c in data['items']})
			print(f'cab :: {cab} \n Page {count} COMPLETE')
			count += 1
			body['last_id'] = data['last_id']
			if len(data['items']) == 0:
				break
			resp = session.post(pl_url, json=body)
		count = 0
		res = [c for c in res]
		to_ser = {}

		while True:
			dd = res[count*100:(count+1)*100]
			if len(dd) == 0:
				break
			body = {'sku': dd}
			resp = session.post(url=c_url, json=body)
			if resp.status_code != 200:
				if resp.status_code == 500:
					ed = resp.json()['message']
					st = ed.find('for sku ') + 8
					end = ed.find(' ', st)
					val = ed[st:end-1]
					body['sku'].remove(val)
					resp = session.post(url=c_url, json=body)
				else:
					break
			for c in resp.json()['products']:
				to_ser[dictionary[c['sku']]] = c['rating']
				print(f'Кабинет :: {cab} \nСтраница {count} отработана')
				count += 1
		time.sleep(1)
		res.data[cab] = to_ser
		# serr.name = cab
		# df = df.append(serr)
	return res

