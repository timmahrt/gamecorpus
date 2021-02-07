import os

from django.shortcuts import render

from . import services

dir_path = os.path.dirname(os.path.realpath(__file__))


def _getNumberFromInput(request, fieldName, defaultVal):
    value = defaultVal
    if fieldName in request.GET:
        tmpValue = request.GET[fieldName]
        if tmpValue.isnumeric():
            value = int(tmpValue)
    return value


def index(request):
    searchResults = []
    if "search_text" in request.GET:
        searchRe = request.GET["search_text"]

        tokenized = "tokenized" in request.GET
        posList = []
        if tokenized:
            posList = ["N", "V", "Adv", "Adj", "Adn", "AdjN"]
            posList = list(filter(lambda x: x in request.GET, posList))

        limitPerGame = _getNumberFromInput(request, "hits_per_game", 1)
        limit = _getNumberFromInput(request, "total_hits", 10)

        searchResults = services.searchDb(
            os.path.join(dir_path, "data"),
            searchRe,
            posList,
            tokenized,
            limitPerGame=limitPerGame,
            limit=limit,
        )

    context = {"search_results": searchResults}

    return render(request, "gamecorpus/index.html", context)
