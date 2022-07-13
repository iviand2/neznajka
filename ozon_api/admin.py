from django.contrib import admin
from .models import Attribute, Category, AttributeValue, Card


# Register your models here.
@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
	list_display = ('identifier', 'name', 'is_required')
	list_filter = ('identifier', 'name')
	search_fields = ('identifier', 'name')
	# raw_id_fields = ('client_id',)
	ordering = ('identifier',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
	list_display = ('category_id', 'name')
	list_filter = ('category_id', 'name')
	search_fields = ('category_id', 'name')
	# raw_id_fields = ('client_id',)
	ordering = ('category_id',)

