from django.urls import path
from . import views

urlpatterns = [
	path('', views.index),
	path('mass_copy/', views.mass_copy_index),
	path('<str:path>', views.gag)
]

