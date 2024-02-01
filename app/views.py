from django.shortcuts import render, redirect, HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import User, UserType, Depot
from django.db.models import Q

# Create your views here.


def index(request):
    if request.user.is_authenticated:
        return redirect("app:dashboard")
    else:
        return render(request, 'login.html')


def do_login(request):
    print("here")
    username = request.POST.get('username')
    password = request.POST.get('password')
    # user_type = request.GET.get('user_type')
    print(username)
    print(password)
    print(request.user)
    if not (username and password):
        messages.error(request, "Please provide all the details!!")
        return redirect("app:index")

    user = authenticate(username=username, password=password)
    if not user:
        messages.error(request, 'Invalid Login Credentials!!')
        return redirect("app:index")

    login(request, user)

    request.session['user_id'] = request.user.id

    return redirect("app:dashboard")


def dashboard(request):
    return render(request, 'dashboard.html')


def logout_user(request):
    logout(request)
    try:
        del request.session['user_id']
    except:
        pass
    return HttpResponseRedirect('/')


def users_list(request):
    users_data = User.objects.filter(~Q(status=2) & Q(user_type=0))
    return render(request, 'users/list.html', {"users": users_data})


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
            user = User.objects.create(name=name, email=email, password=password, phone=phone, status=user_status,
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


def user_update(request):
    user_id = request.POST.get('id')
    name = request.POST.get('name')
    phone = request.POST.get('phone')
    email = request.POST.get('email')
    password = request.POST.get('password')
    user_status = request.POST.get('status')
    user_type = request.POST.get('user_type')
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