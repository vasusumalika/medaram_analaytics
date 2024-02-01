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

    path('user/type/list', views.user_type_list, name='user_type_list'),
    path('user/type/add', views.user_type_add, name='user_type_add'),
    path('user/type/edit', views.user_type_edit, name='user_type_edit'),
    path('user/type/update', views.user_type_update, name='user_type_update'),

    path('depot/list', views.depots_list, name='depots_list'),
    path('depot/add', views.depot_add, name='depot_add'),
    path('depot/edit', views.depot_edit, name='depot_edit'),
    path('depot/update', views.depot_update, name='depot_update'),

    path('operation/type/list', views.operation_type_list, name='operation_type_list'),
    path('operation/type/add', views.operation_type_add, name='operation_type_add'),
    path('operation/type/edit', views.operation_type_edit, name='operation_type_edit'),
    path('operation/type/update', views.operation_type_update, name='operation_type_update'),
    path('operation/type/import', views.operation_type_import, name='operation_type_import'),

    path('vehicle/list', views.vehicle_list, name='vehicle_list'),
    path('vehicle/add', views.vehicle_add, name='vehicle_add'),
    path('vehicle/edit', views.vehicle_edit, name='vehicle_edit'),
    path('vehicle/update', views.vehicle_update, name='vehicle_update'),

    path('vehicle/details/list', views.vehicle_details_list, name='vehicle_details_list'),
    path('vehicle/details/add', views.vehicle_detail_add, name='vehicle_detail_add'),
    path('vehicle/details/edit', views.vehicle_detail_edit, name='vehicle_detail_edit'),
    path('vehicle/details/update', views.vehicle_detail_update, name='vehicle_detail_update'),

    path('spl/bus/data/entry/list', views.spl_bus_data_entry_list, name='spl_bus_data_entry_list'),
    path('spl/bus/data/entry/add', views.spl_bus_data_entry_add, name='spl_bus_data_entry_add'),
    path('spl/bus/data/entry/edit', views.spl_bus_data_entry_edit, name='spl_bus_data_entry_edit'),
    path('spl/bus/data/entry/update', views.spl_bus_data_entry_update, name='spl_bus_data_entry_update'),

    path('get/depot/vehicle/number', views.get_depot_vehicle_number, name='get_depot_vehicle_number'),

]
