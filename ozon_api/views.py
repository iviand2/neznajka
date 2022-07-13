import datetime
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
				function(args, kwargs)
				t.status = 'completed'
			except Exception as ex:
				t.status = 'uncomplete_error'
				logging.error(ex)
			t.ended = datetime.datetime.now(tz=curr_tz)
			t.save()
		try:
			Thread(target=executing, args=(t, func, args), kwargs=kwargs).start()
		except Thread as ex:
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
	attr_id = attr_id['attr_id']
	attr = Attribute.objects.get(identifier=attr_id)
	head = Cab.objects.latest().auth()
	url = 'https://api-seller.ozon.ru/v2/category/attribute/values'
	session = requests.session()
	session.headers = head
	vals = AttributeValue.objects.all()
	for category in attr.category.all():
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
				logging.log(level=4, msg=resp.text, exc_info=True, stack_info=True)

			data = resp.json()['result']
			for val in data:
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
			else:
				break

# def long_execution(task)

