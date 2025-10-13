from django.shortcuts import render, redirect
from .serializers import RegisterSerializer
from django.http import HttpResponse
from django.contrib.auth import authenticate, login
from django.contrib import messages

def home(request):
    return HttpResponse("Bienvenue sur ton Journal Santé Global !")

def register_page(request):
    if request.method == 'POST':
        data = {
            'username': request.POST.get('username'),
            'email': request.POST.get('email'),
            'password': request.POST.get('password'),
        }
        serializer = RegisterSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return redirect('/')  # redirige vers la home après inscription
        else:
            return render(request, 'users/register.html', {'errors': serializer.errors})
    return render(request, 'users/register.html')

def login_page(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('journal_page')  # après login
        else:
            messages.error(request, "Nom d'utilisateur ou mot de passe incorrect")

    return render(request, 'users/login.html')