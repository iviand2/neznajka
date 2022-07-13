from django.db import models


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
		# null=True,
		# related_name='attributeOf'
	)
	is_collection = models.BooleanField(

	)
	is_required = models.BooleanField(

	)
	dictionary_id = models.IntegerField(
		null=True,
	)


class AttributeValue(models.Model):
	identifier = models.IntegerField(
		unique=True,
		primary_key=True
	)
	name = models.CharField(max_length=100)
	attribute = models.ForeignKey(
		Attribute,
		on_delete=models.SET_NULL,
		null=True,
		# related_name='attributeOf'
	)
	value = models.CharField(max_length=10000)


class Card(models.Model):
	offer_id = models.CharField(max_length=20, unique=True)
	creator = models.CharField(max_length=200, null=True)


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

