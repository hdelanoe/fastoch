import pathlib
from django.http import HttpResponse
from django.shortcuts import render

from visits.models import PageVisit

this_dir = pathlib.Path(__file__).resolve().parent

def home_page_view(request, *args, **kwargs):
    qs = PageVisit.objects.all()
    page_qs = qs.filter(path=request.path)
    my_title = "My title"
    my_context = {
        "page_title": my_title,
        "page_visit_count": page_qs.count(),

    }
    html_template = "home.html"
    PageVisit.objects.create(path=request.path)
    return render(request, html_template, my_context)