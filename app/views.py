from django.shortcuts import render, redirect, HttpResponseRedirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

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
