from django.shortcuts import render


# Create your views here.
def index(request):
    template = 'homepage/index.html'
    return render(request, template)


def about(request):
    template = 'homepage/about.html'
    return render(request, template)
