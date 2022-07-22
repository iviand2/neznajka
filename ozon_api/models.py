from django.db import models
from main.models import Cab


# Create your models here.
class Category(models.Model):
	category_id = models.IntegerField(
		unique=True,
		primary_key=True,
	)
	name = models.CharField(max_length=100)
	parent = models.ForeignKey(
		'self',
		on_delete=models.CASCADE,
		# related_name='parentOf',
		null=True,
	)


class Attribute(models.Model):
	identifier = models.IntegerField(
		unique=True,
		primary_key=True,
	)
	name = models.CharField(max_length=100)
	category = models.ManyToManyField(
		Category,
	)
	is_collection = models.BooleanField(

	)
	is_required = models.BooleanField(

	)
	dictionary_id = models.IntegerField(
		null=True,
	)


class AttributeValue(models.Model):
	"""
	identifier = int,
	name = str,
	attribute = Attribute
	value = str
	"""
	class Meta:
		ordering = ('created',)
	identifier = models.IntegerField(
		null=True
	)
	name = models.CharField(max_length=100)
	attribute = models.ForeignKey(
		Attribute,
		on_delete=models.CASCADE,
		null=True,
		# related_name='attributeOf'
	)
	value = models.CharField(max_length=10000)
	# card = models.ManyToManyField(
	# 	Card,
	# 	null=True,
	# )
	created = models.DateTimeField(
		auto_now_add=True
	)
	updated = models.DateTimeField(
		auto_now=True
	)


class Card(models.Model):
	"""
	ozon_id = int,
	ozon_fbs = int,
	ozon_fbo = int,
	offer_id = str,
	creator = str
	"""
	ozon_id = models.IntegerField(
		unique=True,
	)
	ozon_fbs = models.IntegerField(
		null=True,
	)
	ozon_fbo = models.IntegerField(
		null=True,
	)
	offer_id = models.CharField(
		max_length=20,
	)
	creator = models.CharField(
		max_length=200,
		null=True,
	)
	created = models.DateTimeField(
		auto_now_add=True,
	)
	updated = models.DateTimeField(
		auto_now=True,
	)
	cab = models.ForeignKey(
		Cab,
		on_delete=models.CASCADE
	)
	category = models.ForeignKey(
		Category,
		on_delete=models.CASCADE
	)
	attributes = models.ManyToManyField(
		AttributeValue,
	)

	class Meta:
		ordering = ('created',)
		# unique_together = (
		# 	'cab',
		# 	'offer_id'
		# )

# class NanAttributeValue(models.Model):
# 	value = models.CharField(max_length=10000)
# 	attribute = models.ForeignKey(
# 		Attribute,
# 		on_delete=models.CASCADE
# 	)
# 	card = models.ForeignKey(
# 		Card,
# 		on_delete=models.CASCADE
# 	)


class Ratings(models.Model):
	value = models.FloatField()
	card = models.ForeignKey(
		Card,
		on_delete=models.CASCADE,
		# related_name='cardOf'
	)
	date = models.DateTimeField(
		auto_now_add=True
	)
	previous_value = models.ForeignKey(
		'self',
		null=True,
		on_delete=models.SET_NULL,
		# related_name='previousOf'
	)
	cab = models.IntegerField(
		null=False
	)

	class Meta:
		ordering = ('date', 'cab')


class Task(models.Model):
	"""
	function = str,
	status = str,
	context = str,
	ended = datetime
	"""

	class Meta:
		ordering = ('created',)

	# identifier = models.IntegerField(
	# 	primary_key=True
	# )
	status = models.CharField(
		default='created',
		max_length=50
	)
	function = models.CharField(
		max_length=50
	)
	created = models.DateTimeField(
		auto_now_add=True
	)
	context = models.CharField(
		null=True,
		default=None,
		max_length=10000
	)
	ended = models.DateTimeField(
		null=True,
		default=None,
	)

	def __str__(self):
		return f'{self.function.__str__()} {self.created.__str__()}'
