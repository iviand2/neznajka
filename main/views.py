import datetime
import time

from django.shortcuts import render, get_object_or_404, get_list_or_404
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from .models import Cab


# Create your views here.
@csrf_exempt
def index(request, **args):
	try:
		with open('log.txt', 'a') as file:
			file.write(
				f'''Time :: {
				datetime.datetime.now()
				}\nQuery :: {
				request.path
				}\nHeaders :: \n{
				request.headers
				}\nBody :: \n{
				request.body
				}\n{
				'-' * 100
				}\n\n''')
	except Exception as ex:
		pass
	data = {
		"version": "0.1",
		"name": "neznajka_api",
		"time": datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
	}
	return JsonResponse(data)


def table(request):
	cabs = {}
	return render(request, 'main/table.html')


def mass_copy_index(request):
	cabs = Cab.objects.all()
	return render(request, 'mass_copy_index.html', context={'cabs': cabs})


@csrf_exempt
def gag(request, **args):
	try:
		with open('log.txt', 'a') as file:
			file.write(
				f'''Time :: {
				datetime.datetime.now()
				}\nQuery :: {
				request.path
				}\nHeaders :: \n{
				request.headers
				}\nBody :: \n{
				request.body
				}\n{
				'-' * 100
				}\n\n''')
	except Exception as ex:
		pass
	data = {
		"version": "0.1",
		"name": "neznajka_api",
		"time": datetime.datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
	}
	return JsonResponse(data)

