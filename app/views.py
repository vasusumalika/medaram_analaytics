from django.http import JsonResponse
from django.shortcuts import render, redirect, HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import User, UserType, Depot, OperationType, Vehicle, VehicleDetails, SpecialBusDataEntry, StatisticsDateEntry
from django.db.models import Q
from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.contrib.auth.hashers import check_password
import pandas as pd
from functools import wraps


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

        if user_login_data and check_password(user_password, user_login_data.password):
            print(request.user.id)
            request.session['user_id'] = user_login_data.id
            return redirect("app:dashboard")
        else:
            messages.error(request, 'Invalid Login Credentials!!')
            return redirect("app:index")
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
    users_data = User.objects.filter(~Q(status=2))
    return render(request, 'users/list.html', {"users": users_data})


@custom_login_required
def user_add(request):
    if request.method == "POST":
        name = request.POST.get('name')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        password = request.POST.get('password')
        user_status = request.POST.get('status')
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
            depot_data = Depot.objects.get(id=depot)
            encrypted_password = make_password(password)
            user = User.objects.create(name=name, email=email, password=encrypted_password, phone_number=phone,
                                       status=user_status,
                                       user_type=user_type_data, depot=depot_data)
            user.save()
            messages.success(request, 'User Created Successfully')
        except Exception as e:
            print(e)
            messages.error(request, 'User Creation Failed!!')
        return redirect("app:users_list")
    try:
        user_type_data = UserType.objects.filter(Q(status=0) | Q(status=1))
        depot_data = Depot.objects.filter(Q(status=0) | Q(status=1))
        return render(request, 'users/add.html', {'user_type_data': user_type_data, "depot_data": depot_data})
    except Exception as e:
        print(e)
        return render(request, 'users/add.html', {})


@custom_login_required
def user_edit(request):
    user_id = request.GET.get('id')
    if user_id:
        user_data = User.objects.get(id=user_id)
        user_type_id_list = []
        depot_id_list = []
        if user_data.user_type:
            user_type_id_list.append(user_data.user_type.id)
        if user_data.depot:
            depot_id_list.append(user_data.depot.id)
    try:
        user_type_data = UserType.objects.filter(Q(status=0) | Q(status=1))
        depot_data = Depot.objects.filter(Q(status=0) | Q(status=1))
        return render(request, 'users/edit.html', {"user_type_data": user_type_data, 'depot_data': depot_data,
                                                   'user': user_data, 'user_type_id_list': user_type_id_list,
                                                   'depot_id_list': depot_id_list})
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
    user_status = request.POST.get('status')
    user_type = request.POST.get('user_type_id')
    depot = request.POST.get('depot_id')
    if user_id:
        try:
            user_data = User.objects.get(id=user_id)
            user_data.name = name
            user_data.email = email
            user_data.password = password
            user_data.phone = phone
            user_data.status = user_status
            user_type_data = UserType.objects.get(id=user_type)
            user_data.user_type = user_type_data
            depot_data = Depot.objects.get(id=depot)
            user_data.depot = depot_data
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
        user_status = request.POST.get('status')
        try:
            # user_data = User.objects.get(id=request.session['user_id'])
            user_type = UserType.objects.create(name=name, status=user_status)
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
    user_status = request.POST.get('status')
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
        depot_status = request.POST.get('status')
        try:
            # user_data = User.objects.get(id=request.session['user_id'])
            depot = Depot.objects.create(name=name, depot_code=depot_code, status=depot_status)
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
    depot_status = request.POST.get('status')
    if depot_id:
        try:
            depot_data = Depot.objects.get(id=depot_id)
            depot_data.name = name
            depot_data.depot_code = depot_code
            depot_data.status = depot_status
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
        status = request.POST.get('status')
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
    status = request.POST.get('status')
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
        status = request.POST.get('status')
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
    status = request.POST.get('status')
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
        vehicle_detail_status = request.POST.get('status')
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
    vehicle_detail_status = request.POST.get('status')
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
        return render(request, 'spl_bus_data_entry/add.html', {'depot_data': depot_data,
                                                               'operation_type_data': operation_type_data})
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
            spl_bus_data_entry_data.depot = sending_depot_data

            reporting_depot_data = Depot.objects.get(id=special_bus_reporting_depot)
            spl_bus_data_entry_data.depot = reporting_depot_data

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
            # user_data = User.objects.get(id=request.session['user_id'])
            df = pd.read_excel(file)
            row_iter = df.iterrows()
            for i, row in row_iter:
                print(row)
                try:
                    name = row[0]
                    depot_exist = Depot.objects.filter(name=name).count()
                    if depot_exist == 0:
                        depot = Depot.objects.create(name=name, depot_code=row[1], status=0)
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
                                                                       opt_type=opt_type_data, vehicle_owner=row[5],
                                                                       status=0, created_by=user_data,
                                                                       bus_number=bus_number)
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
def statistics_up_journey_list(request):
    statistics_up_journey_data = StatisticsDateEntry.objects.filter(~Q(status=2)).filter(entry_type='up')
    return render(request, 'statistics_date_entry/up_journey/list.html', {"statistics_up_journey_data": statistics_up_journey_data})


@custom_login_required
def statistics_up_journey_add(request):
    if request.method == "POST":
        bus_unique_code = request.POST.get('bus_unique_code')
        total_ticket_amount = request.POST.get('total_ticket_amount')
        total_adult_passengers = request.POST.get('total_adult_passengers')
        total_child_passengers = request.POST.get('total_child_passengers')
        mhl_adult_passengers = request.POST.get('mhl_adult_passengers')
        mhl_child_passengers = request.POST.get('mhl_child_passengers')
        mhl_adult_amount = request.POST.get('mhl_adult_amount')
        mhl_child_amount = request.POST.get('mhl_child_amount')
        entry_type = 'up'
        service_operated_date = request.POST.get('service_operated_date')
        status = 0

        try:
            user_data = User.objects.get(id=request.session['user_id'])
            statistics_data_entry = StatisticsDateEntry.objects.create(bus_unique_code=bus_unique_code,
                                                                       total_ticket_amount=total_ticket_amount,
                                                                       total_adult_passengers=total_adult_passengers,
                                                                       total_child_passengers=total_child_passengers,
                                                                       mhl_adult_passengers=mhl_adult_passengers,
                                                                       mhl_child_passengers=mhl_child_passengers,
                                                                       mhl_adult_amount=mhl_adult_amount,
                                                                       mhl_child_amount=mhl_child_amount,
                                                                       entry_type=entry_type,
                                                                       service_operated_date=service_operated_date,
                                                                       status=status, created_by=user_data)
            statistics_data_entry.save()
            messages.success(request, 'Statistics Data Entry Up Journey Created Successfully')
        except Exception as e:
            print(e)
            messages.error(request, 'Statistics Data Entry Up Journey Creation Failed!!')
        return redirect("app:statistics_up_journey_list")
    else:
        return render(request, 'statistics_date_entry/up_journey/add.html', {})


@custom_login_required
def statistics_up_journey_edit(request):
    statistics_up_journey_id = request.GET.get('id')
    if statistics_up_journey_id:
        statistics_up_journey_data = StatisticsDateEntry.objects.get(id=statistics_up_journey_id)
        return render(request, 'statistics_date_entry/up_journey/edit.html', {"statistics_up_journey_data": statistics_up_journey_data})
    else:
        return render(request, 'statistics_date_entry/up_journey/edit.html', {})


@custom_login_required
def statistics_up_journey_update(request):
    statistics_up_journey_id = request.POST.get('id')
    bus_unique_code = request.POST.get('bus_unique_code')
    total_ticket_amount = request.POST.get('total_ticket_amount')
    total_adult_passengers = request.POST.get('total_adult_passengers')
    total_child_passengers = request.POST.get('total_child_passengers')
    mhl_adult_passengers = request.POST.get('mhl_adult_passengers')
    mhl_child_passengers = request.POST.get('mhl_child_passengers')
    mhl_adult_amount = request.POST.get('mhl_adult_amount')
    mhl_child_amount = request.POST.get('mhl_child_amount')
    service_operated_date = request.POST.get('service_operated_date')
    status = 0
    if statistics_up_journey_id:
        try:
            statistics_up_journey_data = StatisticsDateEntry.objects.get(id=statistics_up_journey_id)
            statistics_up_journey_data.bus_unique_code = bus_unique_code
            statistics_up_journey_data.total_ticket_amount = total_ticket_amount
            statistics_up_journey_data.total_adult_passengers = total_adult_passengers
            statistics_up_journey_data.total_child_passengers = total_child_passengers
            statistics_up_journey_data.mhl_adult_passengers = mhl_adult_passengers
            statistics_up_journey_data.mhl_child_passengers = mhl_child_passengers
            statistics_up_journey_data.mhl_adult_amount = mhl_adult_amount
            statistics_up_journey_data.mhl_child_amount = mhl_child_amount
            statistics_up_journey_data.service_operated_date = service_operated_date
            statistics_up_journey_data.status = status
            user_data = User.objects.get(id=request.session['user_id'])
            statistics_up_journey_data.updated_by = user_data
            statistics_up_journey_data.save()
            messages.success(request, 'Statistics Date Entry Up Journey updated successfully!!')
            return redirect("app:statistics_up_journey_list")
        except Exception as e:
            print(e)
            messages.error(request, 'Statistics Data Entry Up Journey update  failed!!')
            return redirect("app:statistics_up_journey_list")
    else:
        return redirect("app:statistics_up_journey_list")


@custom_login_required
def statistics_down_journey_list(request):
    statistics_down_journey_data = StatisticsDateEntry.objects.filter(~Q(status=2)).filter(entry_type='down')
    return render(request, 'statistics_date_entry/down_journey/list.html', {"statistics_down_journey_data": statistics_down_journey_data})


@custom_login_required
def statistics_down_journey_add(request):
    if request.method == "POST":
        bus_unique_code = request.POST.get('bus_unique_code')
        total_ticket_amount = request.POST.get('total_ticket_amount')
        total_adult_passengers = request.POST.get('total_adult_passengers')
        total_child_passengers = request.POST.get('total_child_passengers')
        mhl_adult_passengers = request.POST.get('mhl_adult_passengers')
        mhl_child_passengers = request.POST.get('mhl_child_passengers')
        mhl_adult_amount = request.POST.get('mhl_adult_amount')
        mhl_child_amount = request.POST.get('mhl_child_amount')
        entry_type = 'down'
        service_operated_date = request.POST.get('service_operated_date')
        status = 0

        try:
            user_data = User.objects.get(id=request.session['user_id'])
            statistics_data_entry = StatisticsDateEntry.objects.create(bus_unique_code=bus_unique_code,
                                                                       total_ticket_amount=total_ticket_amount,
                                                                       total_adult_passengers=total_adult_passengers,
                                                                       total_child_passengers=total_child_passengers,
                                                                       mhl_adult_passengers=mhl_adult_passengers,
                                                                       mhl_child_passengers=mhl_child_passengers,
                                                                       mhl_adult_amount=mhl_adult_amount,
                                                                       mhl_child_amount=mhl_child_amount,
                                                                       entry_type=entry_type,
                                                                       service_operated_date=service_operated_date,
                                                                       status=status, created_by=user_data)
            statistics_data_entry.save()
            messages.success(request, 'Statistics Date Entry down Journey Created Successfully')
        except Exception as e:
            print(e)
            messages.error(request, 'Statistics Date Entry down Journey Creation Failed!!')
        return redirect("app:statistics_down_journey_list")
    else:
        return render(request, 'statistics_date_entry/down_journey/add.html', {})


@custom_login_required
def statistics_down_journey_edit(request):
    statistics_down_journey_id = request.GET.get('id')
    if statistics_down_journey_id:
        statistics_down_journey_data = StatisticsDateEntry.objects.get(id=statistics_down_journey_id)
        return render(request, 'statistics_date_entry/down_journey/edit.html', {"statistics_down_journey_data": statistics_down_journey_data})
    else:
        return render(request, 'statistics_date_entry/down_journey/edit.html', {})


@custom_login_required
def statistics_down_journey_update(request):
    statistics_down_journey_id = request.POST.get('id')
    bus_unique_code = request.POST.get('bus_unique_code')
    total_ticket_amount = request.POST.get('total_ticket_amount')
    total_adult_passengers = request.POST.get('total_adult_passengers')
    total_child_passengers = request.POST.get('total_child_passengers')
    mhl_adult_passengers = request.POST.get('mhl_adult_passengers')
    mhl_child_passengers = request.POST.get('mhl_child_passengers')
    mhl_adult_amount = request.POST.get('mhl_adult_amount')
    mhl_child_amount = request.POST.get('mhl_child_amount')
    service_operated_date = request.POST.get('service_operated_date')
    status = 0
    if statistics_down_journey_id:
        try:
            statistics_up_journey_data = StatisticsDateEntry.objects.get(id=statistics_down_journey_id)
            statistics_up_journey_data.bus_unique_code = bus_unique_code
            statistics_up_journey_data.total_ticket_amount = total_ticket_amount
            statistics_up_journey_data.total_adult_passengers = total_adult_passengers
            statistics_up_journey_data.total_child_passengers = total_child_passengers
            statistics_up_journey_data.mhl_adult_passengers = mhl_adult_passengers
            statistics_up_journey_data.mhl_child_passengers = mhl_child_passengers
            statistics_up_journey_data.mhl_adult_amount = mhl_adult_amount
            statistics_up_journey_data.mhl_child_amount = mhl_child_amount
            statistics_up_journey_data.service_operated_date = service_operated_date
            statistics_up_journey_data.status = status
            user_data = User.objects.get(id=request.session['user_id'])
            statistics_up_journey_data.updated_by = user_data
            statistics_up_journey_data.save()
            messages.success(request, 'Statistics Date Entry down Journey updated successfully!!')
            return redirect("app:statistics_down_journey_list")
        except Exception as e:
            print(e)
            messages.error(request, 'Statistics Date Entry down Journey update  failed!!')
            return redirect("app:statistics_down_journey_list")
    else:
        return redirect("app:statistics_down_journey_list")
