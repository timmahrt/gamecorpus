from django.urls import path

from . import views

urlpatterns = [
    path("", views.gameScripts, name="index"),
    path("about.html", views.about, name="about"),
    path("search.html", views.search, name="search"),
    path("game_scripts.html", views.gameScripts, name="gameScripts"),
    path(
        "game_script_sections.html",
        views.gameScriptSections,
        name="gameScriptSections",
    ),
    path("game_script.html", views.gameScript, name="gameScript"),
    path("how_to_use.html", views.howToUse, name="howToUse"),
]
