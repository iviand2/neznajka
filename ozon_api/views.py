import concurrent.futures
import datetime
import inspect
import json
import logging
import time
import traceback

from threading import Thread
from django.shortcuts import render
from django.http.response import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .modules.main_api import extract_content_ratings
from .models import Ratings, Card, Category, AttributeValue, Attribute, Task
from .modules import static_data
from main.models import Cab
import requests
from timeit import default_timer as timer
from django.core.exceptions import *
from django.core.serializers import serialize


# Create your views here.
curr_tz = datetime.timezone(datetime.timedelta(hours=0))
logging.basicConfig(filename='log.txt')


def long(func):
	def task_work(*args, **kwargs):
		t = Task.objects.create(
			function=func.__name__,
			status='created',
			context=str(args),
			ended=None
		)
		t.status = 'started'
		t.save()

		def executing(task, function, *args, **kwargs):
			try:
				function(*args, **kwargs)
				t.status = 'completed'
			except Exception as ex:
				t.status = 'uncomplete_error'
				logging.error(ex)
			t.ended = datetime.datetime.now(tz=curr_tz)
			t.save()
		try:
			Thread(target=executing, args=(t, func, *args), kwargs=kwargs).start()
		except Exception as ex:
			t.status = 'thread_starting_error'
			t.ended = datetime.datetime.now()
			t.save()
			logging.error(ex)
		return JsonResponse({'task_id': t.id})
	return task_work


@csrf_exempt
def update_ratings(request):
	result = extract_content_ratings()
	if result.errors:
		pass
	data = result.data
	for cab in data:
		ratings = data[cab]
		for rate in ratings:
			card = Card.objects.get_or_create(offer_id=rate['offer_id'])
			ratings = Ratings.objects.get(
				card=card,
				cab=cab
			)
			if ratings:
				last_rate = ratings.objects.last()
				rating_now = float(ratings[rate]['rating'])
				if rating_now != last_rate.value:
					Ratings(
						cab=cab,
						last_rate=last_rate,
						value=rating_now,
						card=card,
					).save()
				else:
					pass
	return JsonResponse({'result': 'Success'})


@csrf_exempt
@long
def update_categories(request, *args, **kwargs):
	## Создаем рабочую сессию
	start = timer()
	heads = Cab.objects.latest().auth()
	session = requests.session()
	session.headers = heads
	url_tree = 'https://api-seller.ozon.ru/v1/categories/tree'
	resp = session.get(url_tree)
	tree = resp.json()['result']
	def categories_recurse(category, parent=None):
		if parent is not None:
			parent = Category.objects.get(category_id=parent)
		try:
			cat_base = Category.objects.get(category_id=category['category_id'])
			if cat_base.name != category['title']:
				cat_base.name = category['title']
				cat_base.save()
		except Category.DoesNotExist:
			Category(category_id=category['category_id'], name=category['title'], parent=parent).save()
		if category['children']:
			for child in category['children']:
				categories_recurse(child, category['category_id'])
	for cat in tree:
		categories_recurse(cat)
		# time.sleep(60)
	print(f'Выполнение обновления дерева категорий {timer() - start} секунд')
	update_attributes(request, heads, session)
	# return JsonResponse({'result': 'Ok'})


@csrf_exempt
@long
def update_attributes(request, heads=None, session=None):
	start = timer()
	if heads is None:
		heads = Cab.objects.latest().auth()
	if session is None:
		session = requests.session()
		session.headers = heads
	categories = Category.objects.all()
	url = 'https://api-seller.ozon.ru/v3/category/attribute'
	print(f'Запрос дерева категорий {timer() - start} секунд')
	for cat in categories:
		start_cat = timer()
		start_func = timer()
		body = {
			"attribute_type": "ALL",
			"category_id": [
				cat.category_id
			],
			"language": "DEFAULT"
		}
		resp = session.post(url, json=body)
		if resp.status_code != 200:
			time.sleep(10)
			resp = session.post(url, json=body)
			resp.raise_for_status()
		print(f'Запрос атрибутов из озон {timer() - start_func}')
		attributes = resp.json()['result'][0]['attributes']
		for attribute in attributes:
			start_func = timer()
			# attribute['id'] = int(attribute['id'])
			try:
				check_time = timer()
				attr = Attribute.objects.get(identifier=attribute['id'])
				if not cat.attribute_set.contains(attr):
					cat.attribute_set.add(attr)
				print(f'Проверка атрибута {timer() - check_time}')
			except Attribute.DoesNotExist:
				# cat.attribute_set.
				create_time = timer()
				attr = Attribute(
					identifier=attribute['id'],
					name=attribute['name'],
					is_collection=attribute['is_collection'],
					is_required=attribute['is_required'],
					dictionary_id=attribute['dictionary_id']
				)
				attr.save()
				cat.attribute_set.add(attr)
				print(f'Создание атрибута {timer() - create_time}')
			print(f'Отработка атрибута {timer() - start_func}')
		print(f'Обработка категории {timer() - start_cat}')
	print(f'Общее выполение: {timer() - start}')


@csrf_exempt
@long
def update_attribute(request, attr_id):
	attr = Attribute.objects.get(identifier=attr_id)
	head = Cab.objects.latest().auth()
	url = 'https://api-seller.ozon.ru/v2/category/attribute/values'
	session = requests.session()
	session.headers = head
	vals = AttributeValue.objects.all()
	with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
		futures = [executor.submit(__resp_work_attributes, category, session, attr, vals) for category in attr.category.all()]
		for future in concurrent.futures.as_completed(futures):
			try:
				print(future.result())
			except Exception as ex:
				print(traceback.format_exception(ex))
		# print(f'Начали категорию {category.category_id}')
		# t = timer()
		# body = {
		# 	"attribute_id": attr.identifier,
		# 	"category_id": category.category_id,
		# 	"language": "DEFAULT",
		# 	"last_value_id": 0,
		# 	"limit": 5000
		# }
		# while True:
		# 	resp = session.post(url=url, json=body)
		# 	if resp.status_code != 200:
		# 		# logging.log(level=4, msg=resp.text, exc_info=True, stack_info=True)
		# 		print(f'ERROR :: {resp.text}')
		# 		break
		#
		# 	data = resp.json()['result']
		# 	for val in data:
		# 		# try:
		# 		# 	base_value = vals.get_or_create(
		# 		# 		identifier=val['id'],
		# 		# 		defaults={
		# 		# 			'name': val['value'],
		# 		# 			'attribute': attr
		# 		# 		}
		# 		# 	)[0]
		# 		# 	if base_value.name != val['value']:
		# 		# 		base_value.name = val['value']
		# 		# 		base_value.save()
		# 		# except Exception as ex:
		# 		# 	traceback.format_exc(ex)
		# 		base_value = vals.get_or_create(
		# 			identifier=val['id'],
		# 			defaults={
		# 				'name': val['value'],
		# 				'attribute': attr
		# 			}
		# 		)[0]
		# 		if base_value.name != val['value']:
		# 			base_value.name = val['value']
		# 			base_value.save()
		# 	if data:
		# 		body['last_value_id'] = data[-1]['id']
		# 		print(f'Уже выполняем {timer() - t}')
		# 	else:
		# 		break
		# print(f'Закончили отработку категории {category.category_id} выполнение - {timer() - t}')


def __resp_work_attributes(category, session, attr, vals):
	url = 'https://api-seller.ozon.ru/v2/category/attribute/values'
	print(f'Начали категорию {category.category_id}')
	t = timer()
	body = {
		"attribute_id": attr.identifier,
		"category_id": category.category_id,
		"language": "DEFAULT",
		"last_value_id": 0,
		"limit": 5000
	}
	while True:
		resp = session.post(url=url, json=body)
		if resp.status_code != 200:
			# logging.log(level=4, msg=resp.text, exc_info=True, stack_info=True)
			print(f'ERROR :: {resp.text}')
			break
		data = resp.json()['result']
		for val in data:
			# try:
			# 	base_value = vals.get_or_create(
			# 		identifier=val['id'],
			# 		defaults={
			# 			'name': val['value'],
			# 			'attribute': attr
			# 		}
			# 	)[0]
			# 	if base_value.name != val['value']:
			# 		base_value.name = val['value']
			# 		base_value.save()
			# except Exception as ex:
			# 	traceback.format_exc(ex)
			base_value = vals.get_or_create(
				identifier=val['id'],
				defaults={
					'name': val['value'],
					'attribute': attr
				}
			)[0]
			if base_value.name != val['value']:
				base_value.name = val['value']
				base_value.save()
		if data:
			body['last_value_id'] = data[-1]['id']
			print(f'{category.category_id} :: Уже выполняем {timer() - t}')
		else:
			break
	print(f'Закончили отработку категории {category.category_id} выполнение - {timer() - t}')
	return f'{category.category_id}  - готово. \nВыполнение - {timer() - t}'


@csrf_exempt
def get_by_name(request):
	try:
		data = json.loads(request.body)
		value = AttributeValue.objects.get(**data)
		return JsonResponse({'id': value.identifier, 'name': value.name, 'error': ''}, status=200)
	except FieldError:
		return JsonResponse({'id': '', 'name': '', 'error': 'incorrect param name'}, status=400)
	except AttributeValue.DoesNotExist:
		return JsonResponse({'id': '', 'name': '', 'error': 'Not found'}, status=200)
	except AttributeValue.MultipleObjectsReturned:
		value = AttributeValue.objects.filter(**data).order_by('identifier').last()
		return JsonResponse({
			'id': value.identifier,
			'name': value.name,
			'error': 'Multiple return. Returned max identifier'
		}, status=200)
	except Exception as ex:
		return JsonResponse({'error': str(ex), 'trace': traceback.format_exc()}, status=400)

