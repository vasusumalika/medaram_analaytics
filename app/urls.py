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
]
