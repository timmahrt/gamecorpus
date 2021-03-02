from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("scripts.html", views.scripts, name="scripts"),
    path("scriptSections.html", views.scriptSections, name="scriptSections"),
    path("script.html", views.script, name="script"),
]
