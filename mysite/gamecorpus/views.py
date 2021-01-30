import os

from django.http import HttpResponse
from django.shortcuts import render

from . import services

dir_path = os.path.dirname(os.path.realpath(__file__))

def index(request):
    searchResults = []
    if 'search_text' in request.GET:
        searchRe = request.GET['search_text']
        
        tokenized = 'tokenized' in request.GET
        posList = []
        if tokenized:
            posList = ['N', 'V', 'Adv', 'Adj', 'Adn', 'AdjN']
            posList = list(filter(lambda x: x in request.GET, posList))

        searchResults = services.searchCorpus(os.path.join(dir_path, 'data'), searchRe, posList, tokenized, limit=10)
    context = {"search_results": searchResults}

    return render(request, 'gamecorpus/index.html', context)
