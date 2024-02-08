from django.http import JsonResponse
from django.shortcuts import render, redirect, HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.utils.datetime_safe import datetime

from .models import User, UserType, Depot, OperationType, Vehicle, VehicleDetails, SpecialBusDataEntry, \
    TripStatistics, OutDepotVehicleReceive, OwnDepotBusDetailsEntry, OwnDepotBusWithdraw, OutDepotVehicleSentBack, \
    HsdOilSubmission, BusesOnHand, PointData
from django.db.models import Q, Count
from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.contrib.auth.hashers import check_password
import pandas as pd
from functools import wraps
from cryptography.fernet import Fernet
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured
import ast

# RESTAPI IMPORT STARTS HERE
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from app import serializers as app_serializers

ENCRYPTION_KEY = getattr(settings, 'ENCRYPTION_KEY', None)
if ENCRYPTION_KEY is None:
    raise ImproperlyConfigured("ENCRYPTION_KEY setting is missing")

cipher_suite = Fernet(ENCRYPTION_KEY)

from django.db.models import Sum

def custom_login_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # Check if the specific session data exists
        user_id = request.session.get('user_id')

        if user_id is None:
            # Session data does not exist, redirect to login
            return redirect('app:index')

        return view_func(request, *args, **kwargs)

    return _wrapped_view


def index(request):
    if request.user.is_authenticated:
        return redirect("app:dashboard")
    else:
        return render(request, 'login.html')


def do_login(request):
    user_email_phone = request.POST.get('user_email_phone')
    user_password = request.POST.get('password')
    print("User", user_email_phone, user_password)
    if request.method == "POST":
        if not (user_email_phone and user_password):
            messages.error(request, "Please provide all the details!!")
            return redirect("app:index")
        user_login_data = User.objects.filter(Q(email=user_email_phone) | Q(phone_number=user_email_phone)).first()
        if user_login_data:
            encrypted_password = ast.literal_eval(user_login_data.password)
            decrypted_password = cipher_suite.decrypt(encrypted_password).decode()
            if decrypted_password == user_password:
                print(request.user.id)
                request.session['user_id'] = user_login_data.id
                request.session['user_type'] = user_login_data.user_type.name
                request.session['point_name'] = user_login_data.point_name.point_name
                return redirect("app:dashboard")
            else:
                messages.error(request, 'Invalid Login Credentials!!')
                return redirect("app:index")
        # if user_login_data and check_password(user_password, user_login_data.password):
        #     print(request.user.id)
        #     request.session['user_id'] = user_login_data.id
        #     request.session['user_type'] = user_login_data.user_type.name
        #     request.session['point_name'] = user_login_data.point_name.point_name
        #     return redirect("app:dashboard")
        # else:
        #     messages.error(request, 'Invalid Login Credentials!!')
        #     return redirect("app:index")
    else:
        messages.error(request, 'Login failed. Try again!!')
        return redirect("app:index")


@custom_login_required
def dashboard(request):
    return render(request, 'dashboard.html')


@custom_login_required
def logout_user(request):
    logout(request)
    try:
        del request.session['user_id']
    except:
        pass
    return HttpResponseRedirect('/')


@custom_login_required
def users_list(request):
    users_data_list = []
    users_data = User.objects.filter(~Q(status=2))
    for user in users_data:
        user_data = {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'phone': user.phone_number,
            'user_type': user.user_type.name,
            'depot': user.depot.name,
            'point_name': user.point_name.point_name,
            'created_at': user.created_at,
        }
        if request.session['user_type'] == 'Super_admin':
            try:
                encrypted_password = ast.literal_eval(user.password)
                decrypted_password = cipher_suite.decrypt(encrypted_password).decode()
                user_data['password'] = decrypted_password
            except Exception as e:
                print(e)
                messages.error(request, ' Failed!!')
        users_data_list.append(user_data)
    return render(request, 'users/list.html', {"users": users_data_list})


@custom_login_required
def user_add(request):
    if request.method == "POST":
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        password = request.POST.get('password')
        point_name = request.POST.get('point_name')
        user_status = 0
        user_type = request.POST.get('user_type')
        depot = request.POST.get('depot_id')
        try:
            # phone_count = Users.objects.filter(Q(phone__iexact=phone) & ~Q(status=2))
            # if phone_count.exists():
            #     messages.error(request, 'Phone number already exist. Please try again')
            #     return redirect('app:user_add')
            # email_count = Users.objects.all().filter(Q(email__iexact=email) & ~Q(status=2))
            # if email_count.exists():
            #     messages.error(request, 'Email already exist. Please try again')
            #     return redirect('app:user_add')
            user_type_data = UserType.objects.get(id=user_type)
            point_name_data = PointData.objects.get(id=point_name)
            depot_data = Depot.objects.get(id=depot)
            encrypted_password = cipher_suite.encrypt(password.encode())
            user = User.objects.create(name=name, email=email, password=encrypted_password, phone_number=phone,
                                       status=user_status, user_type=user_type_data, depot=depot_data,
                                       point_name=point_name_data)
            user.save()
            messages.success(request, 'User Created Successfully')
        except Exception as e:
            print(e)
            messages.error(request, 'User Creation Failed!!')
        return redirect("app:users_list")
    try:
        user_type_data = UserType.objects.filter(Q(status=0) | Q(status=1))
        depot_data = Depot.objects.filter(Q(status=0) | Q(status=1))
        point_name_data = PointData.objects.filter(Q(status=0) | Q(status=1))
        return render(request, 'users/add.html', {'user_type_data': user_type_data, "depot_data": depot_data,
                                                  "point_name_data": point_name_data})
    except Exception as e:
        print(e)
        return render(request, 'users/add.html', {})


@custom_login_required
def user_edit(request):
    user_id = request.GET.get('id')
    if user_id:
        user_data = User.objects.get(id=user_id)
        user_type_id_list = []
        point_name_id_list = []
        depot_id_list = []
        if user_data.user_type:
            user_type_id_list.append(user_data.user_type.id)
        if user_data.depot:
            depot_id_list.append(user_data.depot.id)
        if user_data.point_name:
            point_name_id_list.append(user_data.point_name.id)
    try:
        user_type_data = UserType.objects.filter(Q(status=0) | Q(status=1))
        depot_data = Depot.objects.filter(Q(status=0) | Q(status=1))
        point_name_data = PointData.objects.filter(Q(status=0) | Q(status=1))
        return render(request, 'users/edit.html', {"user_type_data": user_type_data, 'depot_data': depot_data,
                                                   'user': user_data, "point_name_data": point_name_data,
                                                   'user_type_id_list': user_type_id_list,
                                                   'depot_id_list': depot_id_list,
                                                   'point_name_id_list': point_name_id_list})
    except Exception as e:
        print(e)
        return render(request, 'users/edit.html', {})


@custom_login_required
def user_update(request):
    user_id = request.POST.get('id')
    name = request.POST.get('name')
    phone = request.POST.get('phone')
    email = request.POST.get('email')
    password = request.POST.get('password')
    user_status = 0
    user_type = request.POST.get('user_type_id')
    depot = request.POST.get('depot_id')
    point_name = request.POST.get('point_name_id')
    if user_id:
        try:
            user_data = User.objects.get(id=user_id)
            user_data.name = name
            user_data.email = email
            if user_data.password != password:  # edited the password
                encrypted_password = cipher_suite.encrypt(password.encode())
                user_data.password = encrypted_password
            user_data.phone = phone
            user_data.status = user_status
            user_type_data = UserType.objects.get(id=user_type)
            user_data.user_type = user_type_data
            depot_data = Depot.objects.get(id=depot)
            user_data.depot = depot_data
            point_name_data = PointData.objects.get(id=point_name)
            user_data.point_name = point_name_data
            user_data.save()
            messages.success(request, 'User updated  successfully!!')
            return redirect("app:users_list")
        except Exception as e:
            print(e)
            messages.error(request, 'User update  failed!!')
            return redirect("app:users_list")
    else:
        return redirect("app:users_list")


@transaction.atomic
@custom_login_required
def user_type_list(request):
    user_type_data = UserType.objects.filter(~Q(status=2))
    return render(request, 'user_type/list.html', {"user_type_data": user_type_data})


@custom_login_required
def user_type_add(request):
    if request.method == "POST":
        name = request.POST.get('name')
        user_status = 0
        try:
            user_data = User.objects.get(id=request.session['user_id'])
            user_type = UserType.objects.create(name=name, status=user_status, created_by=user_data)
            user_type.save()
            messages.success(request, 'User Type Created Successfully')
        except Exception as e:
            print(e)
            messages.error(request, 'User Type Creation Failed!!')
        return redirect("app:user_type_list")
    return render(request, 'user_type/add.html')


@custom_login_required
def user_type_edit(request):
    user_type_id = request.GET.get('id')
    if user_type_id:
        user_type_data = UserType.objects.get(id=user_type_id)
    try:
        return render(request, 'user_type/edit.html', {"user_type": user_type_data})
    except Exception as e:
        print(e)
        return render(request, 'user_type/edit.html', {})


@custom_login_required
def user_type_update(request):
    user_type_id = request.POST.get('id')
    name = request.POST.get('name')
    user_status = 0
    if user_type_id:
        try:
            user_type_data = UserType.objects.get(id=user_type_id)
            user_type_data.name = name
            user_type_data.status = user_status
            user_data = User.objects.get(id=request.session['user_id'])
            user_type_data.updated_by = user_data
            user_type_data.save()
            messages.success(request, 'User Type updated  successfully!!')
            return redirect("app:user_type_list")
        except Exception as e:
            print(e)
            messages.error(request, 'User Type update  failed!!')
            return redirect("app:user_type_list")
    else:
        return redirect("app:user_type_list")


@custom_login_required
def depots_list(request):
    depot_data = Depot.objects.filter(~Q(status=2))
    return render(request, 'depot/list.html', {"depots": depot_data})


@custom_login_required
def depot_add(request):
    if request.method == "POST":
        name = request.POST.get('name')
        depot_code = request.POST.get('depot_code')
        buses_allotted = request.POST.get('buses_allotted')
        depot_status = 0
        try:
            user_data = User.objects.get(id=request.session['user_id'])
            depot = Depot.objects.create(name=name, depot_code=depot_code, status=depot_status, created_by=user_data,
                                         buses_allotted=buses_allotted)
            depot.save()
            messages.success(request, 'Depot Created Successfully')
        except Exception as e:
            print(e)
            messages.error(request, 'Depot Creation Failed!!')
        return redirect("app:depots_list")

    return render(request, 'depot/add.html', {})


@custom_login_required
def depot_edit(request):
    depot_id = request.GET.get('id')
    if depot_id:
        depot_data = Depot.objects.get(id=depot_id)
    return render(request, 'depot/edit.html', {"depot": depot_data})


@custom_login_required
def depot_update(request):
    depot_id = request.POST.get('id')
    name = request.POST.get('name')
    depot_code = request.POST.get('depot_code')
    buses_allotted = request.POST.get('buses_allotted')
    depot_status = 0
    if depot_id:
        try:
            depot_data = Depot.objects.get(id=depot_id)
            depot_data.name = name
            depot_data.depot_code = depot_code
            depot_data.status = depot_status
            depot_data.buses_allotted = buses_allotted
            user_data = User.objects.get(id=request.session['user_id'])
            depot_data.updated_by = user_data
            depot_data.save()
            messages.success(request, 'Depot updated  successfully!!')
            return redirect("app:depots_list")
        except Exception as e:
            print(e)
            messages.error(request, 'Depot update  failed!!')
            return redirect("app:depots_list")
    else:
        return redirect("app:depots_list")


@custom_login_required
def operation_type_list(request):
    operation_type_data = OperationType.objects.filter(~Q(status=2))
    return render(request, 'operation_type/list.html', {"operation_type": operation_type_data})


@custom_login_required
def operation_type_add(request):
    if request.method == "POST":
        name = request.POST.get('name')
        description = request.POST.get('description')
        status = 0
        try:
            user = User.objects.get(id=request.session['user_id'])
            operation_type = OperationType.objects.create(name=name, description=description, status=status,
                                                          created_by=user)
            operation_type.save()
            messages.success(request, 'Operation Type Created Successfully')
        except Exception as e:
            print(e)
            messages.error(request, 'Operation Type Creation Failed!!')
        return redirect("app:operation_type_list")
    else:
        return render(request, 'operation_type/add.html', {})


@custom_login_required
def operation_type_edit(request):
    operation_type_id = request.GET.get('id')
    if operation_type_id:
        operation_type_data = OperationType.objects.get(id=operation_type_id)
        return render(request, 'operation_type/edit.html', {"operation_type_data": operation_type_data})
    else:
        return render(request, 'operation_type/edit.html', {})


@custom_login_required
def operation_type_update(request):
    operation_type_id = request.POST.get('id')
    name = request.POST.get('name')
    description = request.POST.get('description')
    status = 0
    if operation_type_id:
        try:
            operation_type_data = OperationType.objects.get(id=operation_type_id)
            operation_type_data.name = name
            operation_type_data.description = description
            operation_type_data.status = status
            user_data = User.objects.get(id=request.session['user_id'])
            operation_type_data.updated_by = user_data
            operation_type_data.save()
            messages.success(request, 'Operation Type updated  successfully!!')
            return redirect("app:operation_type_list")
        except Exception as e:
            print(e)
            messages.error(request, 'Operation Type update  failed!!')
            return redirect("app:operation_type_list")
    else:
        return redirect("app:operation_type_list")


@custom_login_required
def vehicle_list(request):
    vehicle_data = Vehicle.objects.filter(~Q(status=2))
    return render(request, 'vehicle/list.html', {"vehicle_data": vehicle_data})


@custom_login_required
def vehicle_add(request):
    if request.method == "POST":
        name = request.POST.get('name')
        vehicle_owner = request.POST.get('vehicle_owner')
        status = 0
        try:
            user = User.objects.get(id=request.session['user_id'])
            vehicle = Vehicle.objects.create(name=name, status=status, created_by=user, vehicle_owner=vehicle_owner)
            vehicle.save()
            messages.success(request, 'Vehicle  Created Successfully')
        except Exception as e:
            print(e)
            messages.error(request, 'Vehicle Type Creation Failed!!')
        return redirect("app:vehicle_list")
    else:
        return render(request, 'vehicle/add.html', {})


@custom_login_required
def vehicle_edit(request):
    vehicle_id = request.GET.get('id')
    if vehicle_id:
        vehicle_data = Vehicle.objects.get(id=vehicle_id)
        return render(request, 'vehicle/edit.html', {"vehicle_data": vehicle_data})
    else:
        return render(request, 'vehicle/edit.html', {})


@custom_login_required
def vehicle_update(request):
    vehicle_id = request.POST.get('id')
    name = request.POST.get('name')
    vehicle_owner = request.POST.get('vehicle_owner')
    status = 0
    if vehicle_id:
        try:
            vehicle_data = Vehicle.objects.get(id=vehicle_id)
            vehicle_data.name = name
            vehicle_data.status = status
            vehicle_data.vehicle_owner = vehicle_owner
            user_data = User.objects.get(id=request.session['user_id'])
            vehicle_data.updated_by = user_data
            vehicle_data.save()
            messages.success(request, 'Vehicle  updated  successfully!!')
            return redirect("app:vehicle_list")
        except Exception as e:
            print(e)
            messages.error(request, 'Vehicle update  failed!!')
            return redirect("app:vehicle_list")
    else:
        return redirect("app:vehicle_list")


@custom_login_required
def vehicle_details_list(request):
    vehicle_details_data = VehicleDetails.objects.filter(~Q(status=2))
    return render(request, 'vehicle_details/list.html', {"vehicle_details": vehicle_details_data})


@custom_login_required
def vehicle_detail_add(request):
    if request.method == "POST":
        vehicle_id = request.POST.get('vehicle_id')
        depot_id = request.POST.get('depot_id')
        bus_number = request.POST.get('bus_number')
        opt_type_id = request.POST.get('opt_type')
        vehicle_owner = request.POST.get('vehicle_owner')
        vehicle_detail_status = 0
        try:
            vehicle_data = Vehicle.objects.get(id=vehicle_id)
            depot_data = Depot.objects.get(id=depot_id)
            operation_type_data = OperationType.objects.get(id=opt_type_id)
            user_data = User.objects.get(id=request.session['user_id'])
            vehicle_detail = VehicleDetails.objects.create(vehicle_name=vehicle_data, depot=depot_data,
                                                           opt_type=operation_type_data, bus_number=bus_number,
                                                           status=vehicle_detail_status, created_by=user_data,
                                                           vehicle_owner=vehicle_owner)
            vehicle_detail.save()
            messages.success(request, 'Vehicle Details saved Successfully')
        except Exception as e:
            print(e)
            messages.error(request, 'Vehicle Details Creation Failed!!')
        return redirect("app:vehicle_details_list")
    try:
        vehicle_data = Vehicle.objects.filter(Q(status=0) | Q(status=1))
        depot_data = Depot.objects.filter(Q(status=0) | Q(status=1))
        operation_type_data = OperationType.objects.filter(Q(status=0) | Q(status=1))
        return render(request, 'vehicle_details/add.html', {'vehicle_data': vehicle_data, "depot_data": depot_data,
                                                            'operation_type_data': operation_type_data})
    except Exception as e:
        print(e)
        return render(request, 'vehicle_details/add.html', {})


@custom_login_required
def vehicle_detail_edit(request):
    vehicle_detail_id = request.GET.get('id')
    if vehicle_detail_id:
        vehicle_detail_data = VehicleDetails.objects.get(id=vehicle_detail_id)
        operation_type_id_list = []
        depot_id_list = []
        vehicle_id_list = []
        if vehicle_detail_data.depot:
            depot_id_list.append(vehicle_detail_data.depot.id)
        if vehicle_detail_data.opt_type:
            operation_type_id_list.append(vehicle_detail_data.opt_type.id)
        if vehicle_detail_data.vehicle_name:
            vehicle_id_list.append(vehicle_detail_data.vehicle_name.id)
    try:
        vehicle_data = Vehicle.objects.filter(Q(status=0) | Q(status=1))
        depot_data = Depot.objects.filter(Q(status=0) | Q(status=1))
        operation_type_data = OperationType.objects.filter(Q(status=0) | Q(status=1))
        return render(request, 'vehicle_details/edit.html', {"vehicle_data": vehicle_data, 'depot_data': depot_data,
                                                             'operation_type_data': operation_type_data,
                                                             'operation_type_id_list': operation_type_id_list,
                                                             'depot_id_list': depot_id_list,
                                                             'vehicle_id_list': vehicle_id_list,
                                                             'vehicle_detail': vehicle_detail_data})
    except Exception as e:
        print(e)
        return render(request, 'vehicle_details/edit.html', {})


@custom_login_required
def vehicle_detail_update(request):
    vehicle_detail_id = request.POST.get('id')
    vehicle_id = request.POST.get('vehicle_id')
    depot_id = request.POST.get('depot_id')
    bus_number = request.POST.get('bus_number')
    opt_type_id = request.POST.get('opt_type')
    vehicle_owner = request.POST.get('vehicle_owner')
    vehicle_detail_status = 0
    if vehicle_detail_id:
        try:
            vehicle_detail_data = VehicleDetails.objects.get(id=vehicle_detail_id)
            vehicle_detail_data.bus_number = bus_number
            vehicle_detail_data.vehicle_owner = vehicle_owner
            vehicle_detail_data.status = vehicle_detail_status
            vehicle_data = Vehicle.objects.get(id=vehicle_id)
            vehicle_detail_data.vehicle_name = vehicle_data
            depot_data = Depot.objects.get(id=depot_id)
            vehicle_detail_data.depot = depot_data
            operation_type_data = OperationType.objects.get(id=opt_type_id)
            vehicle_detail_data.opt_type = operation_type_data
            user_data = User.objects.get(id=request.session['user_id'])
            vehicle_detail_data.updated_by = user_data
            vehicle_detail_data.save()
            messages.success(request, 'Vehicle Details updated  successfully!!')
            return redirect("app:vehicle_details_list")
        except Exception as e:
            print(e)
            messages.error(request, 'Vehicle Details update  failed!!')
            return redirect("app:vehicle_details_list")
    else:
        return redirect("app:vehicle_details_list")


@transaction.atomic
@custom_login_required
def operation_type_import(request):
    print("Called")
    if request.method == "POST":
        file = request.FILES.get('operation_type_list')
        try:
            user_data = User.objects.get(id=request.session['user_id'])
            df = pd.read_excel(file)
            row_iter = df.iterrows()
            for i, row in row_iter:
                print(row)
                try:
                    name = row[1]
                    operation_type_exist = OperationType.objects.filter(name=name).count()
                    if operation_type_exist == 0:
                        operation_type = OperationType.objects.create(name=name, description=row[2], status=0,
                                                                      created_by=user_data)
                        operation_type.save()
                    else:
                        pass
                except Exception as e:
                    print(e)
            return redirect("app:operation_type_list")
        except Exception as e:
            print(e)
            messages.error(request, 'Operation Type import failed!!')
        return redirect("app:operation_type_list")
    return render(request, 'operation_type/import.html', {})


@custom_login_required
def spl_bus_data_entry_list(request):
    spl_bus_data_entry_data = SpecialBusDataEntry.objects.filter(~Q(status=2))
    return render(request, 'spl_bus_data_entry/list.html', {"spl_bus_data_entry_data": spl_bus_data_entry_data})


@transaction.atomic
@custom_login_required
def spl_bus_data_entry_add(request):
    if request.method == "POST":
        special_bus_sending_depot = request.POST.get('special_bus_sending_depot')
        special_bus_reporting_depot = request.POST.get('special_bus_reporting_depot')
        # bus_type means operation_type
        # bus_number means vechicle_no
        bus_type = request.POST.get('opt_type')
        bus_number = request.POST.get('vehicle_number')
        log_sheet_no = request.POST.get('log_sheet_no')
        driver1_name = request.POST.get('driver1_name')
        driver1_staff_no = request.POST.get('driver1_staff_no')
        driver1_phone_number = request.POST.get('driver1_phone_number')
        driver2_name = request.POST.get('driver2_name')
        driver2_staff_no = request.POST.get('driver2_staff_no')
        driver2_phone_number = request.POST.get('driver2_phone_number')
        incharge_name = request.POST.get('incharge_name')
        incharge_phone_number = request.POST.get('incharge_phone_number')
        status = 0
        try:
            sending_depot_data = Depot.objects.get(id=special_bus_sending_depot)
            reporting_depot_data = Depot.objects.get(id=special_bus_reporting_depot)
            bus_type_data = OperationType.objects.get(id=bus_type)
            bus_number_data = VehicleDetails.objects.get(bus_number=bus_number)

            user_data = User.objects.get(id=request.session['user_id'])
            spl_bus_data_entry = SpecialBusDataEntry.objects.create(special_bus_sending_depot=sending_depot_data,
                                                                    special_bus_reporting_depot=reporting_depot_data,
                                                                    bus_type=bus_type_data, bus_number=bus_number_data,
                                                                    log_sheet_no=log_sheet_no,
                                                                    driver1_name=driver1_name,
                                                                    driver1_staff_no=driver1_staff_no,
                                                                    driver1_phone_number=driver1_phone_number,
                                                                    driver2_name=driver2_name,
                                                                    driver2_staff_no=driver2_staff_no,
                                                                    driver2_phone_number=driver2_phone_number,
                                                                    incharge_name=incharge_name,
                                                                    incharge_phone_number=incharge_phone_number,
                                                                    status=status, created_by=user_data)
            spl_bus_data_entry.save()
            messages.success(request, 'Special bus data entry details saved Successfully')
        except Exception as e:
            print(e)
            messages.error(request, 'Special bus data entry details creation Failed!!')
        return redirect("app:spl_bus_data_entry_list")
    try:
        depot_data = Depot.objects.filter(Q(status=0) | Q(status=1))
        operation_type_data = OperationType.objects.filter(Q(status=0) | Q(status=1))
        return render(request, 'spl_bus_data_entry/add.html', {'operation_type_data': operation_type_data,
                                                               'depot_data': depot_data})
    except Exception as e:
        print(e)
        return render(request, 'spl_bus_data_entry/add.html', {})


@custom_login_required
def get_depot_vehicle_number(request):
    depot_id = request.GET.get('depot_id')
    vehicle_details_data = VehicleDetails.objects.filter(depot=depot_id).values('id', 'bus_number')
    vehicle_details = list(vehicle_details_data)
    return JsonResponse({'vehicle_details': vehicle_details})


@custom_login_required
def spl_bus_data_entry_edit(request):
    spl_bus_data_entry_id = request.GET.get('id')
    if spl_bus_data_entry_id:
        spl_bus_data_entry_data = SpecialBusDataEntry.objects.get(id=spl_bus_data_entry_id)
        depot_sending_list = []
        depot_reporting_list = []
        bus_type_id_list = []

        if spl_bus_data_entry_data.special_bus_sending_depot:
            depot_sending_list.append(spl_bus_data_entry_data.special_bus_sending_depot.id)
        if spl_bus_data_entry_data.special_bus_reporting_depot:
            depot_reporting_list.append(spl_bus_data_entry_data.special_bus_reporting_depot.id)
        if spl_bus_data_entry_data.bus_type:
            bus_type_id_list.append(spl_bus_data_entry_data.bus_type.id)

    try:
        depot_sending_data = Depot.objects.filter(Q(status=0) | Q(status=1))
        depot_reporting_data = Depot.objects.filter(Q(status=0) | Q(status=1))
        operation_type_data = OperationType.objects.filter(Q(status=0) | Q(status=1))

        return render(request, 'spl_bus_data_entry/edit.html',
                      {'depot_sending_data': depot_sending_data,
                       'depot_reporting_data': depot_reporting_data,
                       'depot_sending_list': depot_sending_list,
                       'depot_reporting_list': depot_reporting_list,
                       'operation_type_data': operation_type_data,
                       'bus_type_id_list': bus_type_id_list,
                       'spl_bus_data_entry_data': spl_bus_data_entry_data})
    except Exception as e:
        print(e)
        return render(request, 'spl_bus_data_entry/edit.html', {})


@custom_login_required
def spl_bus_data_entry_update(request):
    spl_bus_data_entry_id = request.POST.get('id')
    special_bus_sending_depot = request.POST.get('special_bus_sending_depot')
    special_bus_reporting_depot = request.POST.get('special_bus_reporting_depot')
    bus_type = request.POST.get('opt_type')
    bus_number = request.POST.get('vehicle_number')
    log_sheet_no = request.POST.get('log_sheet_no')
    driver1_name = request.POST.get('driver1_name')
    driver1_staff_name = request.POST.get('driver1_staff_name')
    driver1_phone_number = request.POST.get('driver1_phone_number')
    driver2_name = request.POST.get('driver2_name')
    driver2_staff_name = request.POST.get('driver2_staff_name')
    driver2_phone_number = request.POST.get('driver2_phone_number')
    incharge_name = request.POST.get('incharge_name')
    incharge_phone_number = request.POST.get('incharge_phone_number')
    status = 0
    if spl_bus_data_entry_id:
        try:
            spl_bus_data_entry_data = SpecialBusDataEntry.objects.get(id=spl_bus_data_entry_id)

            sending_depot_data = Depot.objects.get(id=special_bus_sending_depot)
            spl_bus_data_entry_data.special_bus_sending_depot = sending_depot_data

            reporting_depot_data = Depot.objects.get(id=special_bus_reporting_depot)
            spl_bus_data_entry_data.special_bus_reporting_depot = reporting_depot_data

            operation_type_data = OperationType.objects.get(id=bus_type)
            spl_bus_data_entry_data.opt_type = operation_type_data

            vehicle_number = VehicleDetails.objects.get(bus_number=bus_number)
            spl_bus_data_entry_data.bus_number = vehicle_number

            spl_bus_data_entry_data.log_sheet_no = log_sheet_no
            spl_bus_data_entry_data.driver1_name = driver1_name
            spl_bus_data_entry_data.driver1_staff_name = driver1_staff_name
            spl_bus_data_entry_data.driver1_phone_number = driver1_phone_number
            spl_bus_data_entry_data.driver2_name = driver2_name
            spl_bus_data_entry_data.driver2_staff_name = driver2_staff_name
            spl_bus_data_entry_data.driver2_phone_number = driver2_phone_number
            spl_bus_data_entry_data.incharge_name = incharge_name
            spl_bus_data_entry_data.incharge_phone_number = incharge_phone_number
            spl_bus_data_entry_data.status = status
            user_data = User.objects.get(id=request.session['user_id'])
            spl_bus_data_entry_data.updated_by = user_data
            spl_bus_data_entry_data.save()
            messages.success(request, 'Special bus data entry updated  successfully!!')
            return redirect("app:spl_bus_data_entry_list")
        except Exception as e:
            print(e)
            messages.error(request, 'Special bus data entry update  failed!!')
            return redirect("app:spl_bus_data_entry_list")
    else:
        return redirect("app:spl_bus_data_entry_list")


@transaction.atomic
@custom_login_required
def vehicle_names_import(request):
    print("Called")
    if request.method == "POST":
        file = request.FILES.get('vehicle_names_list')
        try:
            user_data = User.objects.get(id=request.session['user_id'])
            df = pd.read_excel(file)
            row_iter = df.iterrows()
            for i, row in row_iter:
                print(row)
                try:
                    name = row[0]
                    vehicle_exist = Vehicle.objects.filter(name=name).count()
                    if vehicle_exist == 0:
                        vehicle = Vehicle.objects.create(name=name, vehicle_owner=row[1], status=0,
                                                         created_by=user_data)
                        vehicle.save()
                    else:
                        pass
                except Exception as e:
                    print(e)
            return redirect("app:vehicle_list")
        except Exception as e:
            print(e)
            messages.error(request, 'Vehicle import failed!!')
        return redirect("app:vehicle_list")
    return render(request, 'vehicle/import.html', {})


@transaction.atomic
@custom_login_required
def depot_import(request):
    print("Called")
    if request.method == "POST":
        file = request.FILES.get('depot_list')
        try:
            user_data = User.objects.get(id=request.session['user_id'])
            df = pd.read_excel(file)
            row_iter = df.iterrows()
            for i, row in row_iter:
                print(row)
                try:
                    name = row[1]
                    depot_exist = Depot.objects.filter(name=name).count()
                    if depot_exist == 0:
                        depot = Depot.objects.create(name=name, depot_code=row[0], status=0, created_by=user_data)
                        depot.save()
                    else:
                        pass
                except Exception as e:
                    print(e)
            return redirect("app:depots_list")
        except Exception as e:
            print(e)
            messages.error(request, 'Deport import failed!!')
        return redirect("app:depots_list")
    return render(request, 'depot/import.html', {})


@transaction.atomic
@custom_login_required
def vehicle_details_import(request):
    print("Called")
    if request.method == "POST":
        file = request.FILES.get('vehicle_details_list')
        try:
            user_data = User.objects.get(id=request.session['user_id'])
            df = pd.read_excel(file)
            row_iter = df.iterrows()
            for i, row in row_iter:
                print(row)
                try:
                    bus_number = row[2]
                    vehicle_detail_exist = VehicleDetails.objects.filter(bus_number=bus_number).count()
                    if vehicle_detail_exist == 0:
                        vehicle_name_data = Vehicle.objects.get(name=row[4])
                        depot_data = Depot.objects.get(depot_code=row[1])
                        opt_type_data = OperationType.objects.get(name=row[3])
                        vehicle_detail = VehicleDetails.objects.create(vehicle_name=vehicle_name_data, depot=depot_data,
                                                                       opt_type=opt_type_data,
                                                                       status=0, created_by=user_data,
                                                                       bus_number=bus_number, depot_name=row[5],
                                                                       region_name=row[6], zone_name=row[7])
                        vehicle_detail.save()
                    else:
                        pass
                except Exception as e:
                    print(e)
            return redirect("app:vehicle_details_list")
        except Exception as e:
            print(e)
            messages.error(request, 'Vehicle Details import failed!!')
        return redirect("app:vehicle_details_list")
    return render(request, 'vehicle_details/import.html', {})


@custom_login_required
def trip_start_add(request):
    if request.method == "POST":
        unique_code = request.POST.get('out_depot_vehicle_receive_unique_no')
        bus_number = request.POST.get('out_depot_vehicle_receive_bus_number')
        total_ticket_amount = request.POST.get('total_ticket_amount')
        total_adult_passengers = request.POST.get('total_adult_passengers')
        total_child_passengers = request.POST.get('total_child_passengers')
        mhl_adult_passengers = request.POST.get('mhl_adult_passengers')
        mhl_child_passengers = request.POST.get('mhl_child_passengers')
        mhl_adult_amount = request.POST.get('mhl_adult_amount')
        mhl_child_amount = request.POST.get('mhl_child_amount')
        start_form_location = request.POST.get('start_form_location')
        start_to_location = request.POST.get('start_to_location')
        entry_type = request.POST.get('entry_type')
        service_operated_date = request.POST.get('service_operated_date')
        status = 0

        try:
            user_data = User.objects.get(id=request.session['user_id'])
            start_from_point_data = PointData.objects.get(point_name=start_form_location)
            start_to_pont_data = PointData.objects.get(point_name=start_to_location)

            statistics_data_entry = TripStatistics.objects.create(unique_code=unique_code, bus_number=bus_number,
                                                                  total_ticket_amount=total_ticket_amount,
                                                                  total_adult_passengers=total_adult_passengers,
                                                                  total_child_passengers=total_child_passengers,
                                                                  mhl_adult_passengers=mhl_adult_passengers,
                                                                  mhl_child_passengers=mhl_child_passengers,
                                                                  mhl_adult_amount=mhl_adult_amount,
                                                                  mhl_child_amount=mhl_child_amount,
                                                                  entry_type=entry_type,
                                                                  status=status, created_by=user_data,
                                                                  start_form_location=start_from_point_data,
                                                                  start_to_location=start_to_pont_data,
                                                                  data_enter_by=user_data,
                                                                  trip_start=datetime.now(),
                                                                  service_operated_date=service_operated_date)
            statistics_data_entry.save()
            messages.success(request, 'Statistics Trip Data Created Successfully')
            return redirect("app:trip_start_add")
        except Exception as e:
            print(e)
            messages.error(request, 'Statistics Trip Data Creation Failed!!')
            return redirect("app:trip_start_add")
    else:
        out_depot_vehicle_receive_data = OutDepotVehicleReceive.objects.filter(Q(status=0) | Q(status=1))
        point_data = PointData.objects.filter(Q(status=0) | Q(status=1))
        return render(request, 'trip_statistics/trip_start/add.html',
                      {'out_depot_vehicle_receive_data': out_depot_vehicle_receive_data, 'point_data': point_data})


@custom_login_required
def search_trip_end_form(request):
    out_depot_vehicle_receive_data = OutDepotVehicleReceive.objects.filter(Q(status=0) | Q(status=1))
    if request.method == "POST":
        unique_no = request.POST.get('unique_no')
        last_trip_details = TripStatistics.objects.filter(unique_code=unique_no).order_by('-created_at').first()
        if last_trip_details:
            return render(request, 'trip_statistics/trip_end/add.html',
                          {'last_trip_details': last_trip_details,
                           'out_depot_vehicle_receive_data': out_depot_vehicle_receive_data})
        else:
            messages.error(request, 'Selected Unique No has no TripStatistic details!!')
            return render(request, 'trip_statistics/trip_end/add.html',
                          {'out_depot_vehicle_receive_data': out_depot_vehicle_receive_data})
    try:
        return render(request, 'trip_statistics/trip_end/add.html',
                      {'out_depot_vehicle_receive_data': out_depot_vehicle_receive_data})
    except Exception as e:
        print(e)


@custom_login_required
def trip_end_add(request):
    trip_check_id = request.POST.get('id')
    trip_verified = request.POST.get('trip_verified')
    trip_verified_time = datetime.now()
    trip_end = datetime.now()
    service_operated_date = request.POST.get('service_operated_date')
    if trip_check_id:
        try:
            trip_check_data = TripStatistics.objects.get(id=trip_check_id)
            trip_check_data.trip_verified = trip_verified
            trip_check_data.trip_verified_time = trip_verified_time
            user_data = User.objects.get(id=request.session['user_id'])
            trip_check_data.trip_verify_by = user_data
            trip_check_data.service_operated_date = service_operated_date
            trip_check_data.updated_by = user_data
            trip_check_data.trip_end = trip_end
            trip_check_data.save()
            messages.success(request, 'Trip check updated successfully!!')
            return redirect("app:trip_end_add")
        except Exception as e:
            print(e)
            messages.error(request, 'Trip check updated failed!!')
            return redirect("app:trip_end_add")
    else:
        out_depot_vehicle_receive_data = OutDepotVehicleReceive.objects.filter(Q(status=0) | Q(status=1))
        return render(request, 'trip_statistics/trip_end/add.html',
                      {'out_depot_vehicle_receive_data': out_depot_vehicle_receive_data})


@custom_login_required
def out_depot_buses_receive_list(request):
    out_depot_vehicle_receive_data = OutDepotVehicleReceive.objects.filter(~Q(status=2))
    return render(request, 'out_depot_buses/out_depot_vehicle_receive/list.html',
                  {'out_depot_vehicle_receive_data': out_depot_vehicle_receive_data})


# @custom_login_required
# def out_depot_buses_receive_form(request):
#     try:
#         special_bus_data = SpecialBusDataEntry.objects.filter(~Q(status=2))
#         return render(request, 'out_depot_buses/out_depot_vehicle_receive/add.html',
#                       {'special_bus_numbers_data': special_bus_data})
#     except Exception as e:
#         print(e)


@custom_login_required
def search_special_bus_data(request):
    if request.method == "POST":
        bus_number = request.POST.get('bus_number')
        if bus_number:
            vehicle_detail = VehicleDetails.objects.get(bus_number=bus_number)
            special_bus_data = SpecialBusDataEntry.objects.get(bus_number=vehicle_detail)
    special_bus_numbers_data = SpecialBusDataEntry.objects.filter(~Q(status=2))
    return render(request, 'out_depot_buses/out_depot_vehicle_receive/add.html',
                  {'special_bus_data': special_bus_data, 'special_bus_numbers_data': special_bus_numbers_data})


@custom_login_required
def out_depot_buses_receive_add(request):
    if request.method == "POST":
        bus_number = request.POST.get('out_depot_vehicle_receive_bus_number')
        unique_no = request.POST.get('unique_no')
        new_log_sheet_no = request.POST.get('new_log_sheet_no')
        hsd_top_oil_liters = request.POST.get('hsd_top_oil_liters')
        mts_no = request.POST.get('mts_no')
        bus_reported_date = request.POST.get('bus_reported_date')
        bus_reported_time = request.POST.get('bus_reported_time')
        out_depot_buses_receive_status = 0
        try:
            vehicle_detail_data = VehicleDetails.objects.get(bus_number=bus_number)
            special_bus_data = SpecialBusDataEntry.objects.get(bus_number=vehicle_detail_data)
            out_depot_bus_sending_depot = Depot.objects.get(id=special_bus_data.special_bus_sending_depot.id)
            out_depot_bus_reporting_depot = Depot.objects.get(id=special_bus_data.special_bus_reporting_depot.id)
            user_data = User.objects.get(id=request.session['user_id'])
            out_depot_buses_receive_detail = OutDepotVehicleReceive.objects.create(bus_number=vehicle_detail_data,
                                                                                   special_bus_data_entry=special_bus_data,
                                                                                   unique_no=unique_no,
                                                                                   new_log_sheet_no=new_log_sheet_no,
                                                                                   hsd_top_oil_liters=hsd_top_oil_liters,
                                                                                   mts_no=mts_no,
                                                                                   bus_reported_date=bus_reported_date,
                                                                                   bus_reported_time=bus_reported_time,
                                                                                   created_by=user_data,
                                                                                   status=out_depot_buses_receive_status,
                                                                                   out_depot_bus_sending_depot=out_depot_bus_sending_depot,
                                                                                   out_depot_bus_reporting_depot=out_depot_bus_reporting_depot
                                                                                   )
            out_depot_buses_receive_detail.save()
            messages.success(request, 'Out Depot Vehicle Receive Details saved Successfully')
        except Exception as e:
            print(e)
            messages.error(request, 'Out Depot Vehicle Receive Details Creation Failed!!')
        return redirect("app:out_depot_buses_receive_list")
    try:
        special_bus_data = SpecialBusDataEntry.objects.filter(~Q(status=2))
        return render(request, 'out_depot_buses/out_depot_vehicle_receive/add.html',
                      {'special_bus_numbers_data': special_bus_data})
    except Exception as e:
        print(e)
    # return render(request, 'out_depot_buses/out_depot_vehicle_receive/add.html', {})


def own_depot_bus_details_entry_list(request):
    own_depot_bus_detail_entry_data = OwnDepotBusDetailsEntry.objects.filter(~Q(status=2))
    return render(request, 'own_depot_buses/own_depot_bus_details_entry/list.html',
                  {'own_depot_bus_detail_entry_data': own_depot_bus_detail_entry_data})


def own_depot_bus_details_entry_add(request):
    if request.method == "POST":
        bus_number = request.POST.get('bus_number')
        unique_no = request.POST.get('unique_no')
        bus_type = request.POST.get('bus_type')
        log_sheet_no = request.POST.get('log_sheet_no')
        driver1_name = request.POST.get('driver1_name')
        driver1_phone_number = request.POST.get('driver1_phone_number')
        driver2_name = request.POST.get('driver2_name')
        driver2_phone_number = request.POST.get('driver2_phone_number')
        status = 0
        try:
            user_data = User.objects.get(id=request.session['user_id'])
            own_depot_bus_detail_entry = OwnDepotBusDetailsEntry.objects.create(bus_number=bus_number,
                                                                                bus_type=bus_type,
                                                                                unique_no=unique_no,
                                                                                log_sheet_no=log_sheet_no,
                                                                                driver1_name=driver1_name,
                                                                                driver1_phone_number=driver1_phone_number,
                                                                                driver2_name=driver2_name,
                                                                                driver2_phone_number=driver2_phone_number,
                                                                                status=status,
                                                                                created_by=user_data)
            own_depot_bus_detail_entry.save()
            messages.success(request, 'Own Depot Bus Detail Entry Saved Successfully')
        except Exception as e:
            print(e)
            messages.error(request, 'Own Depot Bus Detail Entry Creation Failed!!')
        return redirect("app:own_depot_bus_details_entry_list")

    return render(request, 'own_depot_buses/own_depot_bus_details_entry/add.html', {})


@custom_login_required
def own_depot_bus_details_entry_edit(request):
    own_depot_bus_details_entry_id = request.GET.get('id')
    if own_depot_bus_details_entry_id:
        own_depot_bus_details_entry_data = OwnDepotBusDetailsEntry.objects.get(id=own_depot_bus_details_entry_id)
        return render(request, 'own_depot_buses/own_depot_bus_details_entry/edit.html',
                      {"own_depot_bus_details_entry_data": own_depot_bus_details_entry_data})
    else:
        return render(request, 'own_depot_buses/own_depot_bus_details_entry/edit.html', {})


@custom_login_required
def own_depot_bus_details_entry_update(request):
    own_depot_bus_details_entry_id = request.POST.get('id')
    bus_number = request.POST.get('bus_number')
    unique_no = request.POST.get('unique_no')
    bus_type = request.POST.get('bus_type')
    log_sheet_no = request.POST.get('log_sheet_no')
    driver1_name = request.POST.get('driver1_name')
    driver1_phone_number = request.POST.get('driver1_phone_number')
    driver2_name = request.POST.get('driver2_name')
    driver2_phone_number = request.POST.get('driver2_phone_number')
    status = 0
    if own_depot_bus_details_entry_id:
        try:
            own_depot_bus_details_entry_data = OwnDepotBusDetailsEntry.objects.get(id=own_depot_bus_details_entry_id)
            own_depot_bus_details_entry_data.bus_number = bus_number
            own_depot_bus_details_entry_data.unique_no = unique_no
            own_depot_bus_details_entry_data.bus_type = bus_type
            own_depot_bus_details_entry_data.log_sheet_no = log_sheet_no
            own_depot_bus_details_entry_data.driver1_name = driver1_name
            own_depot_bus_details_entry_data.driver1_phone_number = driver1_phone_number
            own_depot_bus_details_entry_data.driver2_name = driver2_name
            own_depot_bus_details_entry_data.driver2_phone_number = driver2_phone_number
            own_depot_bus_details_entry_data.status = status
            user_data = User.objects.get(id=request.session['user_id'])
            own_depot_bus_details_entry_data.updated_by = user_data
            own_depot_bus_details_entry_data.save()
            messages.success(request, 'Own Depot Bus Detail Entry updated successfully!!')
            return redirect("app:own_depot_bus_details_entry_list")
        except Exception as e:
            print(e)
            messages.error(request, 'Own Depot Bus Detail Entry update  failed!!')
            return redirect("app:own_depot_bus_details_entry_list")
    else:
        return redirect("app:own_depot_bus_details_entry_list")


def own_depot_bus_withdraw_list(request):
    own_depot_bus_withdraw_data = OwnDepotBusWithdraw.objects.filter(~Q(status=2))
    return render(request, 'own_depot_buses/own_depot_bus_withdraw/list.html',
                  {'own_depot_bus_withdraw_data': own_depot_bus_withdraw_data})


def own_depot_bus_withdraw_add(request):
    if request.method == "POST":
        bus_number = request.POST.get('bus_number')
        status = 0
        try:
            user_data = User.objects.get(id=request.session['user_id'])
            own_depot_bus_withdraw = OwnDepotBusWithdraw.objects.create(bus_number=bus_number,
                                                                        status=status,
                                                                        created_by=user_data)
            own_depot_bus_withdraw.save()
            messages.success(request, 'Own Depot Bus Withdraw Saved Successfully')
        except Exception as e:
            print(e)
            messages.error(request, 'Own Depot Bus withdraw Creation Failed!!')
        return redirect("app:own_depot_bus_withdraw_list")

    return render(request, 'own_depot_buses/own_depot_bus_withdraw/add.html', {})


@custom_login_required
def own_depot_bus_withdraw_edit(request):
    own_depot_bus_withdraw_id = request.GET.get('id')
    if own_depot_bus_withdraw_id:
        own_depot_bus_withdraw_data = OwnDepotBusWithdraw.objects.get(id=own_depot_bus_withdraw_id)
        return render(request, 'own_depot_buses/own_depot_bus_withdraw/edit.html',
                      {"own_depot_bus_withdraw_data": own_depot_bus_withdraw_data})
    else:
        return render(request, 'own_depot_buses/own_depot_bus_withdraw/edit.html', {})


@custom_login_required
def own_depot_bus_withdraw_update(request):
    own_depot_bus_withdraw_id = request.POST.get('id')
    bus_number = request.POST.get('bus_number')
    status = 0
    if own_depot_bus_withdraw_id:
        try:
            own_depot_bus_withdraw_data = OwnDepotBusWithdraw.objects.get(id=own_depot_bus_withdraw_id)
            own_depot_bus_withdraw_data.bus_number = bus_number
            own_depot_bus_withdraw_data.status = status
            user_data = User.objects.get(id=request.session['user_id'])
            own_depot_bus_withdraw_data.updated_by = user_data
            own_depot_bus_withdraw_data.save()
            messages.success(request, 'Own Depot Bus Withdraw updated successfully!!')
            return redirect("app:own_depot_bus_withdraw_list")
        except Exception as e:
            print(e)
            messages.error(request, 'Own Depot Bus Withdraw update  failed!!')
            return redirect("app:own_depot_bus_withdraw_list")
    else:
        return redirect("app:own_depot_bus_withdraw_list")


@custom_login_required
def out_depot_vehicle_send_back_list(request):
    out_depot_vehicle_send_back_data = OutDepotVehicleSentBack.objects.filter(~Q(status=2))
    return render(request, 'out_depot_buses/out_depot_vehicle_send_back/list.html',
                  {'out_depot_vehicle_send_back_data': out_depot_vehicle_send_back_data})


@custom_login_required
def out_depot_vehicle_send_back_add(request):
    if request.method == "POST":
        unique_no = request.POST.get('out_depot_vehicle_receive_unique_no')
        bus_number = request.POST.get('out_depot_vehicle_receive_bus_number')
        log_sheet_no = request.POST.get('out_depot_send_back_log_sheet_no')
        out_depot_buses_send_back_status = 0
        try:
            special_bus_data = SpecialBusDataEntry.objects.filter(log_sheet_no=log_sheet_no)
            if special_bus_data.count() == 0:
                messages.error(request, 'Log Sheet number not exist!!')
                return redirect("app:out_depot_vehicle_send_back_add")
            user_data = User.objects.get(id=request.session['user_id'])
            out_depo_buse_send_back_detail = OutDepotVehicleSentBack.objects.create(unique_no=unique_no,
                                                                                    bus_number=bus_number,
                                                                                    log_sheet_no=log_sheet_no,
                                                                                    special_bus_data_entry=
                                                                                    special_bus_data[0],
                                                                                    created_by=user_data,
                                                                                    status=
                                                                                    out_depot_buses_send_back_status)
            out_depo_buse_send_back_detail.save()
            messages.success(request, 'Out Depot Vehicle Send Back Details saved Successfully')
        except Exception as e:
            print(e)
            messages.error(request, 'Out Depot Vehicle Send Back Details Creation Failed!!')
        return redirect("app:out_depot_vehicle_send_back_list")
    try:
        out_depot_vehicle_receive_data = OutDepotVehicleReceive.objects.filter(Q(status=0) | Q(status=1))
        return render(request, 'out_depot_buses/out_depot_vehicle_send_back/add.html',
                      {'out_depot_vehicle_receive_data': out_depot_vehicle_receive_data})
    except Exception as e:
        print(e)
        return render(request, 'out_depot_buses/out_depot_vehicle_send_back/add.html', {})


def hsd_oil_submission_list(request):
    hsd_oil_submission_data = HsdOilSubmission.objects.filter(~Q(status=2))
    return render(request, 'hsd_oil_submission/list.html',
                  {'hsd_oil_submission_data': hsd_oil_submission_data})


@custom_login_required
def hsd_oil_submission_form(request):
    return render(request, 'hsd_oil_submission/add.html')


@custom_login_required
def search_unique_no_bus_no_special_bus_data(request):
    if request.method == "POST":
        unique_no_bus_no = request.POST.get('unique_no_bus_no')
        if unique_no_bus_no.isdigit():
            try:
                out_depot_vehicle_receive_data = OutDepotVehicleReceive.objects.get(unique_no=unique_no_bus_no)
                special_bus_data = out_depot_vehicle_receive_data.special_bus_data_entry
                return render(request, 'hsd_oil_submission/add.html', {'special_bus_data': special_bus_data,
                                                                       'unique_bus_no': unique_no_bus_no})
            except Exception as e:
                print(e)
                messages.error(request, 'Unique number not matching please try again')
                return redirect("app:hsd_oil_submission_add")
        else:
            try:
                vehicle_details = VehicleDetails.objects.get(bus_number=unique_no_bus_no)
                special_bus_data = SpecialBusDataEntry.objects.get(bus_number=vehicle_details)
                return render(request, 'hsd_oil_submission/add.html', {'special_bus_data': special_bus_data,
                                                                       'unique_bus_no': unique_no_bus_no})
            except Exception as e:
                print(e)
                messages.error(request, 'Bus number not matching please try again')
                return redirect("app:hsd_oil_submission_add")
    else:
        return redirect("app:hsd_oil_submission_add")


@custom_login_required
def hsd_oil_submission_add(request):
    if request.method == "POST":
        bus_number = request.POST.get('hsd_oil_bus_number')
        hsd_liters = request.POST.get('hsd_top_oil_liters')
        mts_no = request.POST.get('mts_no')
        point_name = request.POST.get('point_name')
        unique_no_bus_no = request.POST.get('unique_bus_no')
        shift = request.POST.get('shift')
        hsd_oil_submission_status = 0
        try:
            vehicle_detail_data = VehicleDetails.objects.get(bus_number=bus_number)
            special_bus_data = SpecialBusDataEntry.objects.get(bus_number=vehicle_detail_data)
            user_data = User.objects.get(id=request.session['user_id'])
            hsd_oil_submission_detail = HsdOilSubmission.objects.create(special_bus_data_entry=special_bus_data,
                                                                        hsd_liters=hsd_liters,
                                                                        mts_no=mts_no, point_name=point_name,
                                                                        created_by=user_data,
                                                                        unique_no_bus_no=unique_no_bus_no,
                                                                        status=hsd_oil_submission_status,
                                                                        shift=shift)
            hsd_oil_submission_detail.save()
            messages.success(request, 'HSD Oil Submission Details saved Successfully')
        except Exception as e:
            print(e)
            messages.error(request, 'HSD Oil Submission Details Creation Failed!!')
        return redirect("app:hsd_oil_submission_list")

    return render(request, 'hsd_oil_submission/add.html', {})


@custom_login_required
def buses_on_hand_list(request):
    buses_on_hand_data = BusesOnHand.objects.filter(~Q(status=2))
    return render(request, 'buses_on_hand/list.html',
                  {'buses_on_hand_data': buses_on_hand_data})


@custom_login_required
def buses_on_hand_add(request):
    if request.method == "POST":
        unique_code = request.POST.get('unique_code')
        point_name = request.POST.get('point_name')
        bus_in_out = request.POST.get('bus_in_out')
        buses_on_hand_status = 0
        try:
            out_depot_vehicle_receive_data = OutDepotVehicleReceive.objects.get(unique_no=unique_code)
            special_bus_data = out_depot_vehicle_receive_data.special_bus_data_entry
            point_name_data = PointData.objects.get(id=point_name)
            user_data = User.objects.get(id=request.session['user_id'])
            buses_on_hand_detail = BusesOnHand.objects.create(unique_code=unique_code, status=buses_on_hand_status,
                                                              special_bus_data_entry=special_bus_data,
                                                              created_by=user_data, bus_in_out=bus_in_out,
                                                              point_name=point_name_data)
            buses_on_hand_detail.save()
            messages.success(request, 'Buses on hand Details saved Successfully')
        except Exception as e:
            print(e)
            messages.error(request, 'Buses On Hand Details Creation Failed!!')
        return redirect("app:buses_on_hand_list")
    try:
        point_name_data = PointData.objects.filter(Q(status=0) | Q(status=1))
        return render(request, 'buses_on_hand/add.html', {"point_name_data": point_name_data})
    except Exception as e:
        print(e)
        return render(request, 'buses_on_hand/add.html', {})


@custom_login_required
def summary_sending_buses_list(request):
    summary_depot_result = []
    summary_depot_data = Depot.objects.filter(~Q(status=2))
    for summary_depot in summary_depot_data:
        no_of_buses_allotted = summary_depot.buses_allotted
        no_of_buses_dispatched = SpecialBusDataEntry.objects.filter(special_bus_sending_depot=summary_depot).count()
        if summary_depot.buses_allotted != 0:
            no_of_buses_due = summary_depot.buses_allotted - no_of_buses_dispatched
        else:
            no_of_buses_due = 0

        no_of_buses_reached = OutDepotVehicleReceive.objects.filter(out_depot_bus_sending_depot=summary_depot).count()

        if no_of_buses_dispatched != 0:
            no_of_buses_not_reached = no_of_buses_dispatched - no_of_buses_reached
        else:
            no_of_buses_not_reached = 0

        summary_depot_result.append({
            'depot_id': summary_depot.id,
            'depot_name': summary_depot.name,
            'buses_allotted': no_of_buses_allotted,
            'buses_dispatched': no_of_buses_dispatched,
            'buses_due': no_of_buses_due,
            'buses_reached': no_of_buses_reached,
            'buses_not_reached': no_of_buses_not_reached,
        })
    return render(request, 'reports/summary_sending_buses_list.html',
                  {'summary_depot_result': summary_depot_result})


@custom_login_required
def buses_dispatched_list(request):
    depot_id = request.GET.get('id')
    depot_data = Depot.objects.get(id=depot_id)
    buses_dispatched_data = SpecialBusDataEntry.objects.filter(~Q(status=2)).filter(special_bus_sending_depot=depot_id)
    return render(request, 'reports/buses_dispatched_list.html',
                  {'buses_dispatched_data': buses_dispatched_data, 'depot_data': depot_data})


@custom_login_required
def buses_dispatched_display_details(request):
    bus_number = request.GET.get('id')
    if bus_number:
        buses_dispatched_display_data = SpecialBusDataEntry.objects.get(bus_number=bus_number)
        date_part = buses_dispatched_display_data.created_at.date()
        time_part = buses_dispatched_display_data.created_at.time()
    try:
        return render(request, 'reports/buses_dispatched_display_details.html',
                      {"buses_dispatched_display_data": buses_dispatched_display_data, "date_part": date_part,
                       "time_part": time_part})
    except Exception as e:
        print(e)
        return render(request, 'reports/buses_dispatched_display_details.html', {})


@custom_login_required
def buses_reached_list(request):
    depot_id = request.GET.get('id')
    depot_data = Depot.objects.get(id=depot_id)
    buses_reached_data = OutDepotVehicleReceive.objects.filter(~Q(status=2)).filter(
        out_depot_bus_sending_depot=depot_id)
    return render(request, 'reports/buses_reached_list.html',
                  {'buses_reached_data': buses_reached_data, 'depot_data': depot_data})


@custom_login_required
def buses_reached_display_details(request):
    bus_number = request.GET.get('id')
    if bus_number:
        buses_reached_display_data = OutDepotVehicleReceive.objects.get(bus_number=bus_number)
    try:
        return render(request, 'reports/buses_reached_display_details.html',
                      {"buses_reached_display_data": buses_reached_display_data})
    except Exception as e:
        print(e)
        return render(request, 'reports/buses_reached_display_details.html', {})


@custom_login_required
def buses_not_reached_list(request):
    depot_id = request.GET.get('id')
    buses_reached_data = OutDepotVehicleReceive.objects.values_list('special_bus_data_entry__id', flat=True). \
        filter(~Q(status=2)).filter(out_depot_bus_sending_depot=depot_id)
    buses_not_reached_data = SpecialBusDataEntry.objects.filter(~Q(status=2)).exclude(id__in=buses_reached_data). \
        filter(special_bus_sending_depot=depot_id)
    depot_data = Depot.objects.get(id=depot_id)

    return render(request, 'reports/buses_not_reached_list.html',
                  {'buses_not_reached_data': buses_not_reached_data, 'depot_data': depot_data})


@custom_login_required
def buses_not_reached_display_details(request):
    bus_number = request.GET.get('id')
    if bus_number:
        buses_not_reached_display_data = SpecialBusDataEntry.objects.get(bus_number=bus_number)
        date_part = buses_not_reached_display_data.created_at.date()
        time_part = buses_not_reached_display_data.created_at.time()
    try:
        return render(request, 'reports/buses_not_reached_display_details.html',
                      {"buses_not_reached_display_data": buses_not_reached_display_data, "date_part": date_part,
                       "time_part": time_part})
    except Exception as e:
        print(e)
        return render(request, 'reports/buses_not_reached_display_details.html', {})


@custom_login_required
def buses_reached_display_details(request):
    bus_number = request.GET.get('id')
    if bus_number:
        buses_reached_display_data = SpecialBusDataEntry.objects.get(bus_number=bus_number)
        date_part = buses_reached_display_data.created_at.date()
        time_part = buses_reached_display_data.created_at.time()
        bus_reported = OutDepotVehicleReceive.objects.get(special_bus_data_entry=buses_reached_display_data.id)
        bus_reported_date = bus_reported.bus_reported_date
        bus_reported_time = bus_reported.bus_reported_time
    try:
        return render(request, 'reports/buses_reached_display_details.html',
                      {"buses_reached_display_data": buses_reached_display_data, "date_part": date_part,
                       "time_part": time_part, "bus_reported_date": bus_reported_date,
                       "bus_reported_time": bus_reported_time})
    except Exception as e:
        print(e)
        return render(request, 'reports/buses_reached_display_details.html', {})


@custom_login_required
def display_bus_details(request):
    bus_number = request.GET.get('id')
    if bus_number:
        display_bus_data = OutDepotVehicleReceive.objects.get(bus_number=bus_number)
    try:
        return render(request, 'reports/display_bus_details.html', {"display_bus_data": display_bus_data})
    except Exception as e:
        print(e)
        return render(request, 'reports/display_bus_details.html', {})


@custom_login_required
def search_depot_list(request):
    special_bus_sending_depot = SpecialBusDataEntry.objects.values('special_bus_sending_depot__id',
                                                                   'special_bus_sending_depot__name').distinct()
    if request.method == "POST":
        performance_depot_result = []
        depot_name = request.POST.get('depot_name')
        out_depot_bus_reporting_depot = OutDepotVehicleReceive.objects.values_list("out_depot_bus_reporting_depot",
                                                                                   flat=True).filter(
            out_depot_bus_sending_depot=depot_name).distinct()
        if len(out_depot_bus_reporting_depot) > 0:
            for reporting_Depot in out_depot_bus_reporting_depot:
                depot_info = Depot.objects.get(id=reporting_Depot)
                report_depot_id = depot_info.id
                report_depot_name = depot_info.name
                alloted_buses = OutDepotVehicleReceive.objects.filter(
                    out_depot_bus_reporting_depot=reporting_Depot).count()

                depot_points = PointData.objects.values_list('id', flat=True).filter(depot_name=reporting_Depot)

                no_of_trips_up_count = TripStatistics.objects.filter(entry_type='up').filter(start_form_location__in=depot_points).count()
                no_of_trips_down_count = TripStatistics.objects.filter(entry_type='down').filter(start_to_location__in=depot_points).count()
                no_of_trips_count = no_of_trips_up_count+no_of_trips_down_count
                # total_passenger_count = TripStatistics.objects. \
                #     values('total_adult_passengers', 'total_child_passengers', 'mhl_adult_passengers',
                #            'mhl_child_passengers').count()
                # total_earnings_count = TripStatistics.objects. \
                #     values('total_ticket_amount', 'mhl_adult_amount', 'mhl_child_amount').sum()

                total_earnings_up = TripStatistics.objects.filter(entry_type='up').filter(start_form_location__in=depot_points).aggregate(
                    total_ticket_amount_sum=Sum('total_ticket_amount'),
                    mhl_adult_amount_sum=Sum('mhl_adult_amount'),
                    mhl_child_amount_sum=Sum('mhl_child_amount')
                )

                total_earnings_down = TripStatistics.objects.filter(entry_type='down').filter(start_to_location__in=depot_points).aggregate(
                    total_ticket_amount_sum=Sum('total_ticket_amount'),
                    mhl_adult_amount_sum=Sum('mhl_adult_amount'),
                    mhl_child_amount_sum=Sum('mhl_child_amount')
                )

                total_passenger_up = TripStatistics.objects.filter(entry_type='up').filter(
                    start_form_location__in=depot_points).aggregate(
                    total_adult_passengers=Sum('total_adult_passengers'),
                    total_child_passengers=Sum('total_child_passengers'),
                    mhl_adult_passengers=Sum('mhl_adult_passengers'),
                    mhl_child_passengers=Sum('mhl_child_passengers')
                )

                total_passengers_down = TripStatistics.objects.filter(entry_type='down').filter(
                    start_form_location__in=depot_points).aggregate(
                    total_adult_passengers=Sum('total_adult_passengers'),
                    total_child_passengers=Sum('total_child_passengers'),
                    mhl_adult_passengers=Sum('mhl_adult_passengers'),
                    mhl_child_passengers=Sum('mhl_child_passengers')
                )
                total_earnings_count = total_earnings_up + total_earnings_down
                total_passenger_count = total_passenger_up + total_passengers_down
                performance_depot_result.append({
                    'depot_id': report_depot_id,
                    'depot_name': report_depot_name,
                    'buses_allotted': alloted_buses,
                    'no_of_trips_count': no_of_trips_count,
                    'no_of_trips_up_count': no_of_trips_up_count,
                    'no_of_trips_down_count': no_of_trips_down_count,
                    'total_passenger_count': total_passenger_count,
                    'total_earnings_count': total_earnings_count,
                })

                # messages.error(request, 'Selected Unique No has no TripStatistic details!!')
                return render(request, 'reports/performance_of_buses_list.html',
                              {'performance_depot_result': performance_depot_result})
        else:
            return render(request, 'reports/performance_of_buses_list.html',
                          {'special_bus_sending_depot': special_bus_sending_depot})
    else:
        return render(request, 'reports/performance_of_buses_list.html',
                      {'special_bus_sending_depot': special_bus_sending_depot})


@custom_login_required
def performance_of_buses_list(request):
    performance_of_buses_data = SpecialBusDataEntry.objects.filter(~Q(status=2))
    return render(request, 'reports/performance_of_buses_list.html',
                  {'performance_of_buses_data': performance_of_buses_data})


def display_operating_depot_list(request):
    operating_depot_name = request.GET.get('id')
    special_bus_entry = SpecialBusDataEntry.objects.get(special_bus_reporting_depot=operating_depot_name)
    display_operating_depot_data = OutDepotVehicleReceive.objects.filter(~Q(status=2)).filter(
        special_bus_data_entry=special_bus_entry)
    return render(request, 'reports/display_operating_depot_list.html',
                  {'display_operating_depot_data': display_operating_depot_data})


def status_return_back_buses_list(request):
    status_return_back_buses_data = OutDepotVehicleReceive.objects.values('bus_number',
                                                                          'special_bus_data_entry__special_bus_sending_depot__name').annotate(
        bus_count=Count('bus_number'))

    return render(request, 'reports/status_return_back_buses_list.html',
                  {'status_return_back_buses_data': status_return_back_buses_data})


@custom_login_required
def buses_sending_back_list(request):
    buses_sending_back_data = OutDepotVehicleSentBack.objects.filter(~Q(status=2))
    return render(request, 'reports/buses_sending_back_list.html',
                  {'buses_sending_back_data': buses_sending_back_data})


@custom_login_required
def out_depot_vehicle_receive_edit(request):
    out_depot_vehicle_receive_id = request.GET.get('id')
    if out_depot_vehicle_receive_id:
        out_depot_vehicle_receive_data = OutDepotVehicleReceive.objects.get(id=out_depot_vehicle_receive_id)
    try:
        return render(request, 'out_depot_buses/out_depot_vehicle_receive/edit.html',
                      {"out_depot_vehicle_receive_data": out_depot_vehicle_receive_data})
    except Exception as e:
        print(e)
        return render(request, 'out_depot_buses/out_depot_vehicle_receive/edit.html', {})


@custom_login_required
def out_depot_vehicle_receive_update(request):
    out_depot_vehicle_receive_id = request.POST.get('id')
    bus_number = request.POST.get('bus_number')
    unique_no = request.POST.get('unique_no')
    new_log_sheet_no = request.POST.get('new_log_sheet_no')
    hsd_top_oil_liters = request.POST.get('hsd_top_oil_liters')
    mts_no = request.POST.get('mts_no')
    bus_reported_date = request.POST.get('bus_reported_date')
    bus_reported_time = request.POST.get('bus_reported_time')
    out_depot_buses_receive_status = 0
    if out_depot_vehicle_receive_id:
        try:
            out_depot_vehicle_receive_data = OutDepotVehicleReceive.objects.get(id=out_depot_vehicle_receive_id)
            out_depot_vehicle_receive_data.unique_no = unique_no
            out_depot_vehicle_receive_data.new_log_sheet_no = new_log_sheet_no
            out_depot_vehicle_receive_data.hsd_top_oil_liters = hsd_top_oil_liters
            out_depot_vehicle_receive_data.mts_no = mts_no
            out_depot_vehicle_receive_data.bus_reported_date = bus_reported_date
            out_depot_vehicle_receive_data.bus_reported_time = bus_reported_time
            out_depot_vehicle_receive_data.status = out_depot_buses_receive_status
            vehicle_detail_data = VehicleDetails.objects.get(bus_number=bus_number)
            out_depot_vehicle_receive_data.bus_number = vehicle_detail_data
            special_bus_data = SpecialBusDataEntry.objects.get(bus_number=vehicle_detail_data)
            out_depot_vehicle_receive_data.special_bus_data_entry = special_bus_data
            out_depot_bus_sending_depot = Depot.objects.get(id=special_bus_data.special_bus_sending_depot.id)
            out_depot_vehicle_receive_data.out_depot_bus_sending_depot = out_depot_bus_sending_depot
            out_depot_bus_reporting_depot = Depot.objects.get(id=special_bus_data.special_bus_reporting_depot.id)
            out_depot_vehicle_receive_data.out_depot_bus_reporting_depot = out_depot_bus_reporting_depot
            user_data = User.objects.get(id=request.session['user_id'])
            out_depot_vehicle_receive_data.updated_by = user_data
            out_depot_vehicle_receive_data.save()
            messages.success(request, 'Out Depot Vehicle Receive Details updated  successfully!!')
            return redirect("app:out_depot_buses_receive_list")
        except Exception as e:
            print(e)
            messages.error(request, 'Out Depot Vehicle Receive Details update  failed!!')
            return redirect("app:out_depot_buses_receive_list")
    else:
        return redirect("app:out_depot_buses_receive_list")


@custom_login_required
def out_depot_vehicle_send_back_edit(request):
    out_depot_vehicle_send_back_id = request.GET.get('id')
    if out_depot_vehicle_send_back_id:
        out_depot_vehicle_send_back_data = OutDepotVehicleSentBack.objects.get(id=out_depot_vehicle_send_back_id)
        unique_no_list = []
        if out_depot_vehicle_send_back_data.unique_no:
            unique_no_list.append(out_depot_vehicle_send_back_data.unique_no)
    try:
        out_depot_vehicle_receive_data = OutDepotVehicleReceive.objects.filter(Q(status=0) | Q(status=1))
        return render(request, 'out_depot_buses/out_depot_vehicle_send_back/edit.html',
                      {"out_depot_vehicle_send_back_data": out_depot_vehicle_send_back_data,
                       'unique_no_list': unique_no_list,
                       'out_depot_vehicle_receive_data': out_depot_vehicle_receive_data})
    except Exception as e:
        print(e)
        return render(request, 'out_depot_buses/out_depot_vehicle_send_back/edit.html', {})


@custom_login_required
def out_depot_vehicle_send_back_update(request):
    out_depot_vehicle_send_back_id = request.POST.get('id')
    unique_no = request.POST.get('out_depot_vehicle_receive_unique_no')
    bus_number = request.POST.get('out_depot_vehicle_receive_bus_number')
    log_sheet_no = request.POST.get('log_sheet_no')
    out_depot_buses_send_back_status = 0
    if out_depot_vehicle_send_back_id:
        try:
            out_depot_vehicle_send_back_data = OutDepotVehicleSentBack.objects.get(id=out_depot_vehicle_send_back_id)
            out_depot_vehicle_send_back_data.unique_no = unique_no
            out_depot_vehicle_send_back_data.bus_number = bus_number
            out_depot_vehicle_send_back_data.status = out_depot_buses_send_back_status
            special_bus_data = SpecialBusDataEntry.objects.get(log_sheet_no=log_sheet_no)
            out_depot_vehicle_send_back_data.special_bus_data_entry = special_bus_data
            user_data = User.objects.get(id=request.session['user_id'])
            out_depot_vehicle_send_back_data.updated_by = user_data
            out_depot_vehicle_send_back_data.save()
            messages.success(request, 'Out Depot Vehicle Send Back Details updated  successfully!!')
            return redirect("app:out_depot_vehicle_send_back_list")
        except Exception as e:
            print(e)
            messages.error(request, 'Out Depot Vehicle Send Back Details update  failed!!')
            return redirect("app:out_depot_vehicle_send_back_list")
    else:
        return redirect("app:out_depot_vehicle_send_back_list")


@custom_login_required
def buses_on_hand_edit(request):
    buses_on_hand_id = request.GET.get('id')
    if buses_on_hand_id:
        buses_on_hand_data = BusesOnHand.objects.get(id=buses_on_hand_id)
        point_name_id_list = []
        if buses_on_hand_data.point_name:
            point_name_id_list.append(buses_on_hand_data.point_name.id)
    try:
        point_name_data = PointData.objects.filter(Q(status=0) | Q(status=1))
        return render(request, 'buses_on_hand/edit.html', {"buses_on_hand_data": buses_on_hand_data,
                                                           'point_name_data': point_name_data,
                                                           'point_name_id_list': point_name_id_list})
    except Exception as e:
        print(e)
        return render(request, 'buses_on_hand/edit.html', {})


@custom_login_required
def buses_on_hand_update(request):
    buses_on_hand_id = request.POST.get('id')
    unique_code = request.POST.get('unique_code')
    bus_in_out = request.POST.get('bus_in_out')
    point_name = request.POST.get('point_name_id')
    buses_on_hand_status = 0
    if buses_on_hand_id:
        try:
            buses_on_hand_data = BusesOnHand.objects.get(id=buses_on_hand_id)
            buses_on_hand_data.unique_code = unique_code
            point_name_data = PointData.objects.get(id=point_name)
            buses_on_hand_data.point_name = point_name_data
            buses_on_hand_data.bus_in_out = bus_in_out
            buses_on_hand_data.status = buses_on_hand_status
            out_depot_vehicle_receive_data = OutDepotVehicleReceive.objects.get(unique_no=unique_code)
            special_bus_data = out_depot_vehicle_receive_data.special_bus_data_entry
            buses_on_hand_data.special_bus_data_entry = special_bus_data
            user_data = User.objects.get(id=request.session['user_id'])
            buses_on_hand_data.updated_by = user_data
            buses_on_hand_data.save()
            messages.success(request, 'Buses on hand Details Details updated  successfully!!')
            return redirect("app:buses_on_hand_list")
        except Exception as e:
            print(e)
            messages.error(request, 'Buses on hand Details Details update  failed!!')
            return redirect("app:buses_on_hand_list")
    else:
        return redirect("app:buses_on_hand_list")


@custom_login_required
def hsd_oil_submission_edit(request):
    hsd_oil_submission_id = request.GET.get('id')
    if hsd_oil_submission_id:
        hsd_oil_submission_data = HsdOilSubmission.objects.get(id=hsd_oil_submission_id)
    try:
        return render(request, 'hsd_oil_submission/edit.html', {"hsd_oil_submission_data": hsd_oil_submission_data})
    except Exception as e:
        print(e)
        return render(request, 'hsd_oil_submission/edit.html', {})


@custom_login_required
def hsd_oil_submission_update(request):
    hsd_oil_submission_id = request.POST.get('id')
    bus_number = request.POST.get('hsd_oil_bus_number')
    hsd_liters = request.POST.get('hsd_top_oil_liters')
    mts_no = request.POST.get('mts_no')
    point_name = request.POST.get('point_name')
    unique_no_bus_no = request.POST.get('unique_bus_no')
    shift = request.POST.get('shift')
    hsd_oil_submission_status = 0
    if hsd_oil_submission_id:
        try:
            hsd_oil_submission_data = HsdOilSubmission.objects.get(id=hsd_oil_submission_id)
            hsd_oil_submission_data.unique_no_bus_no = unique_no_bus_no
            hsd_oil_submission_data.point_name = point_name
            hsd_oil_submission_data.hsd_liters = hsd_liters
            hsd_oil_submission_data.mts_no = mts_no
            hsd_oil_submission_data.status = hsd_oil_submission_status
            vehicle_detail_data = VehicleDetails.objects.get(bus_number=bus_number)
            special_bus_data = SpecialBusDataEntry.objects.get(bus_number=vehicle_detail_data)
            hsd_oil_submission_data.special_bus_data_entry = special_bus_data
            hsd_oil_submission_data.shift = shift
            user_data = User.objects.get(id=request.session['user_id'])
            hsd_oil_submission_data.updated_by = user_data
            hsd_oil_submission_data.save()
            messages.success(request, 'HSD Oil Submission Details updated  successfully!!')
            return redirect("app:hsd_oil_submission_list")
        except Exception as e:
            print(e)
            messages.error(request, 'HSD Oil Submission Details update  failed!!')
            return redirect("app:hsd_oil_submission_list")
    else:
        return redirect("app:hsd_oil_submission_list")


@transaction.atomic
@custom_login_required
def point_data_import(request):
    print("Called")
    if request.method == "POST":
        file = request.FILES.get('point_data_list')
        try:
            df = pd.read_excel(file)
            row_iter = df.iterrows()
            for i, row in row_iter:
                print(row)
                try:
                    name = row[1]
                    point_name_exist = PointData.objects.filter(point_name=name).count()
                    if point_name_exist == 0:
                        depot_data = Depot.objects.get(name=row[2])
                        point_name = PointData.objects.create(point_name=name, depot_name=depot_data, region=row[3],
                                                              zone=row[4], status=0)
                        point_name.save()
                    else:
                        pass
                except Exception as e:
                    print(e)
            return redirect("app:point_data_list")
        except Exception as e:
            print(e)
            messages.error(request, 'Point Data import failed!!')
        return redirect("app:point_data_list")
    return render(request, 'point_data/import.html', {})


@custom_login_required
def point_data_list(request):
    point_data = PointData.objects.filter(~Q(status=2))
    return render(request, 'point_data/list.html', {"point_name_data": point_data})


def validate_log_sheet(request):
    log_sheet_no = request.GET.get('log_sheet_no')
    try:
        special_bus_data = SpecialBusDataEntry.objects.get(log_sheet_no=log_sheet_no)
        exists = True
    except SpecialBusDataEntry.DoesNotExist:
        exists = False
    return JsonResponse({'exists': exists})


@custom_login_required
def get_out_depot_vehicle_receive_bus_number(request):
    unique_no = request.GET.get('unique_no')
    out_depot_vehicle_receive_data = OutDepotVehicleReceive.objects.get(unique_no=unique_no)
    special_bus_data = out_depot_vehicle_receive_data.special_bus_data_entry
    return JsonResponse({'bus_number': special_bus_data.bus_number.bus_number})


@custom_login_required
def point_name_add(request):
    if request.method == "POST":
        point_name = request.POST.get('point_name')
        depot_id = request.POST.get('depot_id')
        region = request.POST.get('region')
        zone = request.POST.get('zone')
        point_status = 0
        try:
            depot_data = Depot.objects.get(id=depot_id)
            point_data = PointData.objects.create(point_name=point_name, status=point_status, region=region, zone=zone,
                                                  depot_name=depot_data)
            point_data.save()
            messages.success(request, 'Point Created Successfully')
        except Exception as e:
            print(e)
            messages.error(request, 'Point Creation Failed!!')
        return redirect("app:point_data_list")
    try:
        depot_data = Depot.objects.filter(Q(status=0) | Q(status=1))
        return render(request, 'point_data/add.html', {"depot_data": depot_data})
    except Exception as e:
        print(e)
        return render(request, 'point_data/add.html', {})


@custom_login_required
def point_name_edit(request):
    point_name_id = request.GET.get('id')
    if point_name_id:
        point_name_data = PointData.objects.get(id=point_name_id)
        depot_id_list = []
        if point_name_data.depot_name:
            depot_id_list.append(point_name_data.depot_name.id)
    try:
        depot_data = Depot.objects.filter(Q(status=0) | Q(status=1))
        return render(request, 'point_data/edit.html', {'depot_data': depot_data, "point": point_name_data,
                                                        'depot_id_list': depot_id_list})
    except Exception as e:
        print(e)
        return render(request, 'point_data/edit.html', {})


@custom_login_required
def point_name_update(request):
    point_name_id = request.POST.get('id')
    point_name = request.POST.get('point_name')
    depot_id = request.POST.get('depot_id')
    region = request.POST.get('region')
    zone = request.POST.get('zone')
    point_status = 0
    if point_name_id:
        try:
            point_name_data = PointData.objects.get(id=point_name_id)
            point_name_data.point_name = point_name
            point_name_data.region = region
            point_name_data.zone = zone
            point_name_data.status = point_status
            depot_data = Depot.objects.get(id=depot_id)
            point_name_data.depot_name = depot_data
            point_name_data.save()
            messages.success(request, 'Point Data updated  successfully!!')
            return redirect("app:point_data_list")
        except Exception as e:
            print(e)
            messages.error(request, 'Point Data update  failed!!')
            return redirect("app:point_data_list")
    else:
        return redirect("app:point_data_list")


# REST API STARTS FROM HERE

class LoginAPIView(APIView):
    def post(self, request):
        serializer_instance = app_serializers.LoginSerializer(data=request.data)

        if not serializer_instance.is_valid():
            return Response(status=status.HTTP_400_BAD_REQUEST, data=serializer_instance.errors)

        serialized_data = serializer_instance.validated_data

        user_login_data = User.objects.filter(
            Q(email=serialized_data.get("user_email_phone")) | Q(phone_number=serialized_data.get("user_email_phone"))
        ).filter(password=serialized_data.get("user_password")).last()

        if user_login_data:  # and check_password(serialized_data.get("user_password"), user_login_data.password) this needs to be implementd.
            return Response(status=status.HTTP_200_OK, data={
                "code": "Success",
                "message": "User Login Successful.",
                "result": user_login_data.get_details()
            })
        else:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={
                "code": "Fail",
                "message": "Something Went Wrong. Login unsuccessful.",
                "result": []
            })


class DepotAPIView(APIView):
    def get(self, request):
        depot_instances = Depot.objects.all()
        depot_details = [depot.get_details() for depot in depot_instances]
        return Response(status=status.HTTP_200_OK, data={
            "code": "Success",
            "message": "All Depot Fetched Successfully.",
            "result": depot_details
        })


class OperationTypeAPIView(APIView):
    def get(self, request):
        operation_type_instances = OperationType.objects.all()
        operation_details = [opt_type.get_details() for opt_type in operation_type_instances]
        return Response(status=status.HTTP_200_OK, data={
            "code": "Success",
            "message": "All Opeartion Type Fetched Successfully.",
            "result": operation_details
        })


class DepotVehicleAPIView(APIView):
    def get(self, request):
        special_bus_sending_depot = request.GET.get("special_bus_sending_depot")
        serializer_instance = app_serializers.DepotVehicleSerializer(
            data={"special_bus_sending_depot": special_bus_sending_depot}
        )

        if not serializer_instance.is_valid():
            return Response(status=status.HTTP_400_BAD_REQUEST, data=serializer_instance.errors)

        serialized_data = serializer_instance.validated_data
        try:
            depot_instance = Depot.objects.get(
                id=serialized_data.get("special_bus_sending_depot")
            )
            vehicle_instances = VehicleDetails.objects.filter(depot=depot_instance)
            vehicle_details = [vehicle.get_details() for vehicle in vehicle_instances]
            return Response(status=status.HTTP_200_OK, data={
                "code": "Success",
                "message": "All Opeartion Type Fetched Successfully.",
                "result": vehicle_details
            })
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={
                "code": "Fail",
                "message": "Something Went Wrong.",
                "result": []
            })


class AllSplBusEntryAPIView(APIView):
    def get(self, request):
        spl_bus_entry_instances = SpecialBusDataEntry.objects.all()
        spl_buses_details = [bus.get_basic_details() for bus in spl_bus_entry_instances]
        return Response(status=status.HTTP_200_OK, data={
            "code": "Success",
            "message": "All Special Bus Entry Data Fetched Successfully.",
            "result": spl_buses_details
        })


class SplBusEntryAPIView(APIView):
    def get(self, request):
        special_bus_data_id = request.GET.get("special_bus_data_id")
        serializer_instance = app_serializers.GetSplBusDataEntrySerializer(
            data={"special_bus_data_id": special_bus_data_id}
        )
        if not serializer_instance.is_valid():
            return Response(status=status.HTTP_400_BAD_REQUEST, data=serializer_instance.errors)

        serialized_data = serializer_instance.validated_data

        try:
            spl_bus_entry_instance = SpecialBusDataEntry.objects.get(
                id=serialized_data.get("special_bus_data_id")
            )
            return Response(status=status.HTTP_200_OK, data={
                "code": "Success",
                "message": "Special Bus Entry Data Fetched Successfully.",
                "result": spl_bus_entry_instance.get_complete_detail()
            })
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={
                "code": "Fail",
                "message": "Something Went Wrong.",
                "result": []
            })

    def post(self, request):
        serializer_instance = app_serializers.SplBusEntrySerializer(data=request.data)

        if not serializer_instance.is_valid():
            return Response(status=status.HTTP_400_BAD_REQUEST, data=serializer_instance.errors)

        serialized_data = serializer_instance.validated_data

        try:
            special_bus_sending_depot_instance = Depot.objects.get(
                id=serialized_data.get("bus_sending_depot")
            )
            special_bus_reporting_depot_instance = Depot.objects.get(
                id=serialized_data.get("bus_reporting_depot")
            )
            operation_type_instance = OperationType.objects.get(
                id=serialized_data.get("bus_type")
            )
            vehicle_instance = VehicleDetails.objects.get(
                id=serialized_data.get("bus_number")
            )

            spl_bus_entry_instance = SpecialBusDataEntry.objects.create(
                special_bus_sending_depot=special_bus_sending_depot_instance,
                special_bus_reporting_depot=special_bus_reporting_depot_instance,
                bus_type=operation_type_instance,
                bus_number=vehicle_instance,
                log_sheet_no=serialized_data.get("log_sheet_no"),
                driver1_name=serialized_data.get("driver1_name"),
                driver1_staff_no=serialized_data.get("driver1_staff_no"),
                driver1_phone_number=serialized_data.get("driver1_phone_number"),
                driver2_name=serialized_data.get("driver2_name"),
                driver2_staff_no=serialized_data.get("driver2_staff_no"),
                driver2_phone_number=serialized_data.get("driver2_phone_number"),
                incharge_name=serialized_data.get("incharge_name"),
                incharge_phone_number=serialized_data.get("incharge_phone_no"),
                status=0,
                # created_by = request.user,
                # updated_by = request.user
            )

            return Response(status=status.HTTP_200_OK, data={
                "code": "Success",
                "message": "Special Bus Entry Data Added Successfully.",
                "result": []
            })
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={
                "code": "Fail",
                "message": "Something Went Wrong.",
                "result": []
            })


class SearchBusNumberAPI(APIView):
    def get(self, request):
        bus_number = request.GET.get("bus_number")
        serializer_instance = app_serializers.SearchBusNumberSerializer(
            data={"bus_number": bus_number}
        )
        if not serializer_instance.is_valid():
            return Response(status=status.HTTP_400_BAD_REQUEST, data=serializer_instance.errors)

        serialized_data = serializer_instance.validated_data

        try:
            bus_instance = VehicleDetails.objects.get(bus_number=serialized_data.get("bus_number"))
            spl_bus_details = SpecialBusDataEntry.objects.get(
                bus_number=bus_instance
            )
            return Response(status=status.HTTP_200_OK, data={
                "code": "Success",
                "message": "Special Bus Details Fetched Successfully.",
                "result": spl_bus_details.get_complete_detail()
            })
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={
                "code": "Fail",
                "message": "Something Went Wrong.",
                "result": []
            })


class GetAllOutDepotVehicleReceiveAPIView(APIView):
    def get(self, request):
        out_depot_vehicle_instances = OutDepotVehicleReceive.objects.filter(~Q(status=2))
        out_depot_vehicle_receive_details = [bus.get_complete_details() for bus in out_depot_vehicle_instances]
        return Response(status=status.HTTP_200_OK, data={
            "code": "Success",
            "message": "All Out Depot Vehicle Receive Data Fetched Successfully.",
            "result": out_depot_vehicle_receive_details
        })


class OutDepotVehicleReceiveAPIView(APIView):
    def get(self, request):
        out_depot_vehicle_receive_id = request.GET.get("out_depot_vehicle_receive_id")
        serializer_instance = app_serializers.GetOutDepotVehicleReceiveSerializer(
            data={"out_depot_vehicle_receive_id": out_depot_vehicle_receive_id}
        )
        if not serializer_instance.is_valid():
            return Response(status=status.HTTP_400_BAD_REQUEST, data=serializer_instance.errors)

        serialized_data = serializer_instance.validated_data

        try:
            out_depot_vehicle_receive_instance = OutDepotVehicleReceive.objects.get(
                id=serialized_data.get("out_depot_vehicle_receive_id")
            )
            return Response(status=status.HTTP_200_OK, data={
                "code": "Success",
                "message": "Special Bus Entry Data Fetched Successfully.",
                "result": out_depot_vehicle_receive_instance.get_complete_detail()
            })
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={
                "code": "Fail",
                "message": "Something Went Wrong.",
                "result": []
            })

    def post(self, request):
        serializer_instance = app_serializers.OutDepotVehicleReceiveSerializer(data=request.data)

        if not serializer_instance.is_valid():
            return Response(status=status.HTTP_400_BAD_REQUEST, data=serializer_instance.errors)

        serialized_data = serializer_instance.validated_data

        try:
            vehicle_detail_data = VehicleDetails.objects.get(bus_number=serialized_data.get("bus_number"))
            special_bus_data = SpecialBusDataEntry.objects.get(bus_number=vehicle_detail_data)
            user_data = User.objects.get(id=serialized_data.get("user_id"))
            out_depo_buse_receive_detail = OutDepotVehicleReceive.objects.create(
                bus_number=vehicle_detail_data,
                special_bus_data_entry=special_bus_data,
                unique_no=serialized_data.get("unique_no"),
                new_log_sheet_no=serialized_data.get("new_log_sheet_no"),
                hsd_top_oil_liters=serialized_data.get("hsd_top_oil_lts"),
                mts_no=serialized_data.get("mts_no"),
                bus_reported_date=serialized_data.get("bus_reported_date"),
                bus_reported_time=serialized_data.get("bus_reported_time"),
                created_by=user_data,
                status=0
            )
            return Response(status=status.HTTP_200_OK, data={
                "code": "Success",
                "message": "Out Depot Vehicle Receive Data Added Successfully.",
                "result": []
            })
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={
                "code": "Fail",
                "message": "Something Went Wrong.",
                "result": []
            })


class GetAllOutDepotVehicleSendBackAPIView(APIView):
    def get(self, request):
        out_depot_vehicle_instances = OutDepotVehicleSentBack.objects.filter(~Q(status=2))
        out_depot_vehicle_receive_details = [bus.get_complete_details() for bus in out_depot_vehicle_instances]
        return Response(status=status.HTTP_200_OK, data={
            "code": "Success",
            "message": "All Out Depot Vehicle Send Back Data Fetched Successfully.",
            "result": out_depot_vehicle_receive_details
        })


class OutDepotVehicleSendBackAPIView(APIView):
    def get(self, request):
        out_depot_vehicle_send_back_id = request.GET.get("out_depot_vehicle_send_back_id")
        serializer_instance = app_serializers.GetOutDepotVehicleSendBackSerializer(
            data={"out_depot_vehicle_send_back_id": out_depot_vehicle_send_back_id}
        )
        if not serializer_instance.is_valid():
            return Response(status=status.HTTP_400_BAD_REQUEST, data=serializer_instance.errors)

        serialized_data = serializer_instance.validated_data

        try:
            out_depot_vehicle_receive_instance = OutDepotVehicleSentBack.objects.get(
                id=serialized_data.get("out_depot_vehicle_send_back_id")
            )
            return Response(status=status.HTTP_200_OK, data={
                "code": "Success",
                "message": "Out Depot Vehicle Sent Back Data Fetched Successfully.",
                "result": out_depot_vehicle_receive_instance.get_complete_detail()
            })
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={
                "code": "Fail",
                "message": "Something Went Wrong.",
                "result": []
            })

    def post(self, request):
        serializer_instance = app_serializers.OutDepotVehicleSendBackSerializer(data=request.data)

        if not serializer_instance.is_valid():
            return Response(status=status.HTTP_400_BAD_REQUEST, data=serializer_instance.errors)

        serialized_data = serializer_instance.validated_data

        try:
            special_bus_data = SpecialBusDataEntry.objects.get(log_sheet_no=serialized_data.get("log_sheet_no"))
            user_data = User.objects.get(id=serialized_data.get("user_id"))
            out_depo_buse_send_back_detail = OutDepotVehicleSentBack.objects.create(
                unique_no_bus_no=serialized_data.get("unique_no_or_bus_number"),
                log_sheet_no=serialized_data.get("log_sheet_no"),
                special_bus_data_entry=
                special_bus_data,
                created_by=user_data,
                status=0
            )
            return Response(status=status.HTTP_200_OK, data={
                "code": "Success",
                "message": "Out Depot Vehicle Send Back Data Added Successfully.",
                "result": []
            })
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={
                "code": "Fail",
                "message": "Something Went Wrong.",
                "result": []
            })


class GetAllOwnDepotBusDetailAPIView(APIView):
    def get(self, request):
        own_depot_bus_entry_instances = OwnDepotBusDetailsEntry.objects.filter(~Q(status=2))
        own_depot_bus_entry_details = [bus.get_complete_details() for bus in own_depot_bus_entry_instances]
        return Response(status=status.HTTP_200_OK, data={
            "code": "Success",
            "message": "All Own Depot Bus Entry Data Fetched Successfully.",
            "result": own_depot_bus_entry_details
        })


class OwnDepotBusDetailAPIView(APIView):
    def get(self, request):
        own_depot_bus_detail_id = request.GET.get("own_depot_bus_detail_id")
        serializer_instance = app_serializers.GetOwnDepotBusDetailSerializer(
            data={"own_depot_bus_detail_id": own_depot_bus_detail_id}
        )
        if not serializer_instance.is_valid():
            return Response(status=status.HTTP_400_BAD_REQUEST, data=serializer_instance.errors)

        serialized_data = serializer_instance.validated_data

        try:
            own_depot_bus_entry_instance = OwnDepotBusDetailsEntry.objects.get(
                id=serialized_data.get("own_depot_bus_detail_id")
            )
            return Response(status=status.HTTP_200_OK, data={
                "code": "Success",
                "message": "Own Depot Bus Entry Data Fetched Successfully.",
                "result": own_depot_bus_entry_instance.get_complete_details()
            })
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={
                "code": "Fail",
                "message": "Something Went Wrong.",
                "result": []
            })

    def post(self, request):
        serializer_instance = app_serializers.OwnDepotBusDetailSerializer(data=request.data)

        if not serializer_instance.is_valid():
            return Response(status=status.HTTP_400_BAD_REQUEST, data=serializer_instance.errors)

        serialized_data = serializer_instance.validated_data

        try:
            user_data = User.objects.get(id=serialized_data.get("user_id"))
            own_depot_bus_detail_entry = OwnDepotBusDetailsEntry.objects.create(
                bus_number=serialized_data.get("bus_number"),
                bus_type=serialized_data.get("bus_type"),
                unique_no=serialized_data.get("unique_number"),
                log_sheet_no=serialized_data.get("log_sheet_no"),
                driver1_name=serialized_data.get("driver1_name"),
                driver1_phone_number=serialized_data.get("driver1_phone_number"),
                driver2_name=serialized_data.get("driver2_name"),
                driver2_phone_number=serialized_data.get("driver2_phone_number"),
                status=0,
                created_by=user_data
            )
            return Response(status=status.HTTP_200_OK, data={
                "code": "Success",
                "message": "Own Depot Bus Entry Data Added Successfully.",
                "result": []
            })
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={
                "code": "Fail",
                "message": "Something Went Wrong.",
                "result": []
            })


class GetAllOwnDepotBusWithdrawAPIView(APIView):
    def get(self, request):
        own_depot_bus_withdraw_instances = OwnDepotBusWithdraw.objects.filter(~Q(status=2))
        own_depot_bus_withdraw_details = [bus.get_complete_details() for bus in own_depot_bus_withdraw_instances]
        return Response(status=status.HTTP_200_OK, data={
            "code": "Success",
            "message": "All Own Depot Bus Withdraw Data Fetched Successfully.",
            "result": own_depot_bus_withdraw_details
        })


class OwnDepotBusWithdrawAPIView(APIView):
    def get(self, request):
        own_depot_bus_withdraw_id = request.GET.get("own_depot_bus_withdraw_id")
        serializer_instance = app_serializers.GetOwnDepotBusWithdrawSerializer(
            data={"own_depot_bus_withdraw_id": own_depot_bus_withdraw_id}
        )
        if not serializer_instance.is_valid():
            return Response(status=status.HTTP_400_BAD_REQUEST, data=serializer_instance.errors)

        serialized_data = serializer_instance.validated_data

        try:
            own_depot_bus_withdraw_instance = OwnDepotBusWithdraw.objects.get(
                id=serialized_data.get("own_depot_bus_withdraw_id")
            )
            return Response(status=status.HTTP_200_OK, data={
                "code": "Success",
                "message": "Own Depot Bus Withdraw Data Fetched Successfully.",
                "result": own_depot_bus_withdraw_instance.get_complete_details()
            })
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={
                "code": "Fail",
                "message": "Something Went Wrong.",
                "result": []
            })

    def post(self, request):
        serializer_instance = app_serializers.OwnDepotBusWithdrawSerializer(data=request.data)

        if not serializer_instance.is_valid():
            return Response(status=status.HTTP_400_BAD_REQUEST, data=serializer_instance.errors)

        serialized_data = serializer_instance.validated_data

        try:
            user_data = User.objects.get(id=serialized_data.get("user_id"))
            own_depot_bus_withdraw = OwnDepotBusWithdraw.objects.create(
                bus_number=serialized_data.get("bus_number"),
                status=0,
                created_by=user_data
            )
            return Response(status=status.HTTP_200_OK, data={
                "code": "Success",
                "message": "Own Depot Bus Withdraw Data Added Successfully.",
                "result": []
            })
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={
                "code": "Fail",
                "message": "Something Went Wrong.",
                "result": []
            })


class GetAllUpJourneyAPIView(APIView):
    def get(self, request):
        up_journey_instances = StatisticsDateEntry.objects.filter(~Q(status=2))
        up_journey_details = [instance.get_complete_details() for instance in up_journey_instances]
        return Response(status=status.HTTP_200_OK, data={
            "code": "Success",
            "message": "All Up Journey Data Fetched Successfully.",
            "result": up_journey_details
        })


class UpJourneyAPIView(APIView):
    def get(self, request):
        up_journey_id = request.GET.get("up_journey_id")
        serializer_instance = app_serializers.GetUpJourneySerializer(
            data={"up_journey_id": up_journey_id}
        )
        if not serializer_instance.is_valid():
            return Response(status=status.HTTP_400_BAD_REQUEST, data=serializer_instance.errors)

        serialized_data = serializer_instance.validated_data

        try:
            up_journey_instance = StatisticsDateEntry.objects.get(
                id=serialized_data.get("up_journey_id")
            )
            return Response(status=status.HTTP_200_OK, data={
                "code": "Success",
                "message": "Up Journey Data Fetched Successfully.",
                "result": up_journey_instance.get_complete_details()
            })
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={
                "code": "Fail",
                "message": "Something Went Wrong.",
                "result": []
            })

    def post(self, request):
        serializer_instance = app_serializers.UpDownJourneySerializer(data=request.data)

        if not serializer_instance.is_valid():
            return Response(status=status.HTTP_400_BAD_REQUEST, data=serializer_instance.errors)

        serialized_data = serializer_instance.validated_data

        try:
            user_data = User.objects.get(id=serialized_data.get("user_id"))
            statistics_data_entry = StatisticsDateEntry.objects.create(
                bus_unique_code=serialized_data.get("bus_unique_code"),
                total_ticket_amount=serialized_data.get("total_ticket_amount"),
                total_adult_passengers=serialized_data.get("total_adult_passengers"),
                total_child_passengers=serialized_data.get("total_child_passengers"),
                mhl_adult_passengers=serialized_data.get("mhl_adult_passengers"),
                mhl_child_passengers=serialized_data.get("mhl_child_passengers"),
                mhl_adult_amount=serialized_data.get("mhl_adult_amount"),
                mhl_child_amount=serialized_data.get("mhl_child_amount"),
                entry_type="up",
                # service_operated_date=serialized_data.get("user_id"),
                status=0,
                created_by=user_data
            )
            return Response(status=status.HTTP_200_OK, data={
                "code": "Success",
                "message": "Up Journey Data Added Successfully.",
                "result": []
            })
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={
                "code": "Fail",
                "message": "Something Went Wrong.",
                "result": []
            })


class GetAllDownJourneyAPIView(APIView):
    def get(self, request):
        down_journey_instances = StatisticsDateEntry.objects.filter(~Q(status=2))
        down_journey_details = [instance.get_complete_details() for instance in down_journey_instances]
        return Response(status=status.HTTP_200_OK, data={
            "code": "Success",
            "message": "All Down Journey Data Fetched Successfully.",
            "result": down_journey_details
        })


class DownJourneyAPIView(APIView):
    def get(self, request):
        down_journey_id = request.GET.get("down_journey_id")
        serializer_instance = app_serializers.GetDownJourneySerializer(
            data={"down_journey_id": down_journey_id}
        )
        if not serializer_instance.is_valid():
            return Response(status=status.HTTP_400_BAD_REQUEST, data=serializer_instance.errors)

        serialized_data = serializer_instance.validated_data

        try:
            down_journey_instance = StatisticsDateEntry.objects.get(
                id=serialized_data.get("down_journey_id")
            )
            return Response(status=status.HTTP_200_OK, data={
                "code": "Success",
                "message": "Down Journey Data Fetched Successfully.",
                "result": down_journey_instance.get_complete_details()
            })
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={
                "code": "Fail",
                "message": "Something Went Wrong.",
                "result": []
            })

    def post(self, request):
        serializer_instance = app_serializers.UpDownJourneySerializer(data=request.data)

        if not serializer_instance.is_valid():
            return Response(status=status.HTTP_400_BAD_REQUEST, data=serializer_instance.errors)

        serialized_data = serializer_instance.validated_data

        try:
            user_data = User.objects.get(id=serialized_data.get("user_id"))
            statistics_data_entry = StatisticsDateEntry.objects.create(
                bus_unique_code=serialized_data.get("bus_unique_code"),
                total_ticket_amount=serialized_data.get("total_ticket_amount"),
                total_adult_passengers=serialized_data.get("total_adult_passengers"),
                total_child_passengers=serialized_data.get("total_child_passengers"),
                mhl_adult_passengers=serialized_data.get("mhl_adult_passengers"),
                mhl_child_passengers=serialized_data.get("mhl_child_passengers"),
                mhl_adult_amount=serialized_data.get("mhl_adult_amount"),
                mhl_child_amount=serialized_data.get("mhl_child_amount"),
                entry_type="down",
                # service_operated_date=serialized_data.get("user_id"),
                status=0,
                created_by=user_data
            )
            return Response(status=status.HTTP_200_OK, data={
                "code": "Success",
                "message": "Down Journey Data Added Successfully.",
                "result": []
            })
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={
                "code": "Fail",
                "message": "Something Went Wrong.",
                "result": []
            })


class GetAllHSDOilSubmissionAPIView(APIView):
    def get(self, request):
        hsd_oil_submission_instances = HsdOilSubmission.objects.filter(~Q(status=2))
        hsd_oil_submission_details = [instance.get_complete_details() for instance in hsd_oil_submission_instances]
        return Response(status=status.HTTP_200_OK, data={
            "code": "Success",
            "message": "All HSD Oil Submission Data Fetched Successfully.",
            "result": hsd_oil_submission_details
        })


class HSDOilSubmissionAPIView(APIView):
    def get(self, request):
        hsd_oil_submission_id = request.GET.get("hsd_oil_submission_id")
        serializer_instance = app_serializers.GetHSDOilSubmissionSerializer(
            data={"hsd_oil_submission_id": hsd_oil_submission_id}
        )
        if not serializer_instance.is_valid():
            return Response(status=status.HTTP_400_BAD_REQUEST, data=serializer_instance.errors)

        serialized_data = serializer_instance.validated_data

        try:
            down_journey_instance = HsdOilSubmission.objects.get(
                id=serialized_data.get("hsd_oil_submission_id")
            )
            return Response(status=status.HTTP_200_OK, data={
                "code": "Success",
                "message": "HSD Oil Submission Data Fetched Successfully.",
                "result": down_journey_instance.get_complete_details()
            })
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={
                "code": "Fail",
                "message": "Something Went Wrong.",
                "result": []
            })

    def post(self, request):
        serializer_instance = app_serializers.HSDOilSubmissionSerializer(data=request.data)

        if not serializer_instance.is_valid():
            return Response(status=status.HTTP_400_BAD_REQUEST, data=serializer_instance.errors)

        serialized_data = serializer_instance.validated_data

        try:
            vehicle_detail_data = VehicleDetails.objects.get(bus_number=serialized_data.get("bus_number"))
            special_bus_data = SpecialBusDataEntry.objects.get(bus_number=vehicle_detail_data)
            user_data = User.objects.get(id=serialized_data.get("user_id"))
            hsd_oil_submission_detail = HsdOilSubmission.objects.create(
                special_bus_data_entry=special_bus_data,
                hsd_liters=serialized_data.get("hsd_liters"),
                mts_no=serialized_data.get("mts_no"),
                point_name=serialized_data.get("point_name"),
                created_by=user_data,
                unique_no_bus_no=serialized_data.get("unique_no_bus_no"),
                status=0
            )
            return Response(status=status.HTTP_200_OK, data={
                "code": "Success",
                "message": "HSD Oil Subimission Data Added Successfully.",
                "result": []
            })
        except Exception as e:
            return Response(status=status.HTTP_400_BAD_REQUEST, data={
                "code": "Fail",
                "message": "Something Went Wrong.",
                "result": []
            })
