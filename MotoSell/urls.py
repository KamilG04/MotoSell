from django.urls import path
from . import views

app_name = 'vehicles'

urlpatterns = [
    path('', views.vehicle_list_published, name='public_list'),
    path('<int:pk>/', views.vehicle_detail, name='detail'),
    path('moje-ogloszenia/', views.vehicle_list_user, name='user_list'),
    path('dodaj/', views.vehicle_create, name='create'),
    path('<int:pk>/edytuj/', views.vehicle_update, name='update'),
    path('<int:pk>/publikuj/', views.vehicle_publish, name='publish'),
    path('<int:pk>/usun/', views.vehicle_delete, name='delete'),
]
