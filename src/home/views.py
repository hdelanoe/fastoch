import pathlib
from django.http import HttpResponse
from django.shortcuts import redirect, render

from dashboard.views import dashboard_view

this_dir = pathlib.Path(__file__).resolve().parent

def home_view(request, *args, **kwargs):
    if request.user.is_authenticated:
        return redirect("dashboard")
    return render(request,"home.html", {})
