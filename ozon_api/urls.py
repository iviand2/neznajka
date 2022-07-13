from django.urls import path, include
from .views import *

urlpatterns = [
	path('update_ratings/', update_ratings),
	path('update_categories/', update_categories),
	path('attribute/<int:attr_id>/update', update_attribute),

]

