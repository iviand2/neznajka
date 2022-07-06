from django.contrib import admin
from .models import Cab
from logg.models import Error

# Register your models here.


@admin.register(Cab)
class CabAdmin(admin.ModelAdmin):
	list_display = ('client_id', 'created', 'updated')
	list_filter = ('client_id', 'created', 'updated')
	search_fields = ('client_id', 'name')
	# raw_id_fields = ('client_id',)
	ordering = ('client_id',)


@admin.register(Error)
class ErrorAdmin(admin.ModelAdmin):
	readonly_fields = ('datetime', )
	ordering = ('datetime', )
	list_display = ('datetime', 'initiator', 'error', 'traceback', 'context')
	list_filter = ('datetime', 'initiator')


# admin.site.register(Cab)
# admin.site.register(Error)
