from django.urls import path
from . import views

urlpatterns = [
    path('<str:initiator>/', views.new_error),
]

