from django.db import models


class Cab(models.Model):
	client_id = models.IntegerField(unique=True)
	name = models.TextField()
	api_key = models.TextField()
	created = models.DateTimeField(auto_now_add=True)
	updated = models.DateTimeField(auto_now=True)

	class Meta:
		ordering = ('client_id',)
		get_latest_by = ('created',)

	def __str__(self):
		return f'{self.name} :: {self.client_id}'

	def auth(self):
		return {'Client-Id': str(self.client_id), 'Api-Key': self.api_key}

