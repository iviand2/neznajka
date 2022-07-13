from django.shortcuts import render
from json import loads, dumps
from .models import Error
from django.http import JsonResponse
from datetime import datetime
from django.views.decorators.csrf import csrf_exempt


# Create your views here.
@csrf_exempt
def new_error(request, initiator):
	if request.method.lower() == 'post':
		try:
			body_dict = loads(request.body)
			initiator = initiator
			level = body_dict['level'] if 'level' in body_dict.keys() \
				else 'info'
			error = body_dict['error'] if 'error' in body_dict.keys() \
				else 'Краткое описание ошибки не передано'
			traceback = body_dict['traceback'] if 'traceback' in body_dict.keys() \
				else 'Трейсбэк ошибки не передан'
			context = body_dict['context'] if 'context' in body_dict.keys() \
				else 'Трейсбэк ошибки не передан'
			if type(context) in [dict, list]:
				context = dumps(context)
			else:
				context = context.__str__()
			Error(initiator=initiator, error=error, traceback=traceback, context=context, level=level).save()
			data = {
				'status': 'success',
				'context': '',
				'dt': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
			}
		except Exception as ex:
			data = {
				'status': 'error',
				'context': ex.__str__(),
				'dt': datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
			}
	else:
		data = {
			'error': 'string: short name of error',
			'traceback': 'string: traceback of error',
			'context': 'string: any context in json'
		}
	return JsonResponse(data)

