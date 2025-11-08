from django.shortcuts import render


def home(request):
    """Landing page view"""
    return render(request, 'landing/index.html')
