from django.db import models


# Create your models here.
class Error(models.Model):
	datetime = models.DateTimeField(auto_now_add=True)
	initiator = models.CharField(max_length=20)
	error = models.CharField(max_length=300)
	traceback = models.CharField(max_length=10000)
	context = models.CharField(max_length=10000)

	def __str__(self):
		return f'{self.initiator} : {self.datetime.date().strftime("%Y-%m-%d %H:%M:%S")} :: {self.error}'
