from django.shortcuts import render

def home(request):
    return render(request, 'core/home.html')

def about(request):
    return render(request, 'core/about.html')

def projects(request):
    return render(request, 'core/projects.html')

def gallery(request):
    return render(request, 'core/gallery.html')

def contact(request):
    return render(request, 'core/contact.html')
