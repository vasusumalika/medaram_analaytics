from django.urls import path
from .views import *
from django.contrib import admin
from . import views

app_name = "app"
urlpatterns = [
    path('admin/', admin.site.urls),
    path('', index, name='index'),
    path('do_login', views.do_login, name="do_login"),
    path('dashboard', dashboard, name='dashboard'),
    path('logout_user', views.logout_user, name="logout_user"),
    path('users/list', views.users_list, name='users_list'),
    path('users/add', views.user_add, name='user_add'),
    path('users/edit', views.user_edit, name='user_edit'),
    path('users/update', views.user_update, name='user_update'),

    path('operation_type/list', views.operation_type_list, name='operation_type_list'),
    path('operation_type/add', views.operation_type_add, name='operation_type_add'),
    path('operation_type/edit', views.operation_type_edit, name='operation_type_edit'),
    path('operation_type/update', views.operation_type_update, name='operation_type_update'),

    path('vehicle/list', views.vehicle_list, name='vehicle_list'),
    path('vehicle/add', views.vehicle_add, name='vehicle_add'),
    path('vehicle/edit', views.vehicle_edit, name='vehicle_edit'),
    path('vehicle/update', views.vehicle_update, name='vehicle_update'),
]
