import os
import time

from django.shortcuts import render
from django import forms

from gamecorpus import services
from gamecorpus import models

dir_path = os.path.dirname(os.path.realpath(__file__))


def _getNumberFromInput(request, fieldName, defaultVal):
    value = defaultVal
    if fieldName in request.GET:
        tmpValue = request.GET[fieldName]
        if tmpValue.isnumeric():
            value = int(tmpValue)
    return value


def index(request):
    return render(request, "gamecorpus/index.html", {})


def howToUse(request):
    return render(request, "gamecorpus/how_to_use.html", {})


def about(request):
    return render(request, "gamecorpus/about.html", {})


def search(request):
    searchResults = []

    if "search_text" not in request.GET.keys():
        form = SearchForm(request.GET)
    else:
        form = SearchForm(request.GET)
        if form.is_valid():
            searchRe = form.cleaned_data["search_text"]

            tokenized = "tokenized" in request.GET
            posList = []
            if tokenized:
                posList = ["N", "V", "Adv", "Adj", "Adn", "AdjN"]
                posList = list(filter(lambda x: x in request.GET, posList))

            limitPerGame = _getNumberFromInput(request, "hits_per_game", 1)
            limit = _getNumberFromInput(request, "total_hits", 10)

            start = time.time()
            searchResults = services.searchDb(
                os.path.join(dir_path, "data"),
                searchRe,
                posList,
                tokenized,
                limitPerGame=limitPerGame,
                limit=limit,
            )
            stop = time.time()

    context = {"form": form, "search_results": searchResults}

    return render(request, "gamecorpus/search.html", context)


class SearchForm(forms.Form):
    pass
    search_text = forms.CharField(required=True)
    search_tokenized = forms.BooleanField(
        help_text="Search Tokenized Text",
        label="Search Tokenized Text",
        required=False,
    )
    noun_flag = forms.BooleanField(
        help_text="Noun",
        label="Noun",
        required=False,
    )
    verb_flag = forms.BooleanField(
        help_text="Verb",
        label="Verb",
        required=False,
    )
    adjective_flag = forms.BooleanField(
        help_text="Adjective", label="Adjective", required=False
    )
    adverb_flag = forms.BooleanField(
        help_text="Adverb",
        label="Adverb",
        required=False,
    )
    adnomial_flag = forms.BooleanField(
        help_text="Adnominal", label="Adnominal", required=False
    )
    adjectival_noun_flag = forms.BooleanField(
        help_text="Adjectival Noun",
        label="Adjectival Noun",
        required=False,
    )
    hits_per_game = forms.IntegerField(initial=1, label="Hits / game", required=False)
    total_hits = forms.IntegerField(initial=None, label="Total hits", required=False)

    posCheckboxes = [
        "noun_flag",
        "verb_flag",
        "adjective_flag",
        "adverb_flag",
        "adnomial_flag",
        "adjectival_noun_flag",
    ]

    def __init__(self, request, *args, **kwargs):
        super(SearchForm, self).__init__(request, *args, **kwargs)

        disabledStatus = True
        if (
            request
            and "search_tokenized" in request.keys()
            and request["search_tokenized"] == "on"
        ):
            disabledStatus = False

        if disabledStatus:
            for id in self.posCheckboxes:
                self.fields[id].widget.attrs["disabled"] = "true"

        for id in self.posCheckboxes:
            self.fields[id].widget.attrs["id"] = id

        # https://stackoverflow.com/questions/15261286/django-forms-disable-field-if-booleanfield-is-checked
        self.fields["search_tokenized"].widget.attrs["onclick"] = "toggleTokenized();"


def gameScripts(request):
    scripts = models.GameScript.objects.values_list(
        "title", "isPlayed", "sourceAttributionUrl"
    ).all()
    context = {"availables_game_titles": scripts}

    return render(request, "gamecorpus/game_scripts.html", context)


def gameScriptSections(request):
    title = request.GET["title"]
    script = models.GameScript.objects.get(title=title)
    comment = script.comment
    partitions = script.partition_set.values(
        "fileName", "title", "numWords", "numSentences"
    ).all()
    fileInfo = [
        [
            i + 1,
            partition["fileName"],
            partition["title"],
            partition["numWords"],
            partition["numSentences"],
        ]
        for i, partition in enumerate(partitions)
    ]
    context = {
        "title": title,
        "comment": comment,
        "available_partitions": fileInfo,
        "total_sentence_count": script.numSentences,
        "total_word_count": script.numWords,
    }

    return render(request, "gamecorpus/game_script_sections.html", context)


def gameScript(request):
    title = request.GET["title"]
    friendlyTitle = title.lower().replace(" ", "_")
    partitionName = request.GET["partition_name"]
    script = models.GameScript.objects.filter(
        title=title
    ).first()  # TODO: Properly do this: ie handle multiple versions

    partition = script.partition_set.get(script=script, fileName=partitionName)
    eventObjs = partition.event_set.all()

    events = []
    for event in eventObjs:
        utteranceObjs = event.utterance_set.all()

        setType = None
        utterances = []
        for utterance in utteranceObjs:
            setType = _setSpeechType(utterance.utteranceType, setType)
            utterances.append(
                [
                    utterance.speaker,
                    setType,
                    [
                        [f"{friendlyTitle}_{sentence.id}_{i}", sentence.text]
                        for i, sentence in enumerate(utterance.sentence_set.all())
                    ],
                ]
            )
        for u in utterances:
            if len(u) > 3:
                print(u)
        events.append(utterances)

    context = {
        "game_title": title,
        "partition_title": partition.title,
        "events": events,
    }

    return render(request, "gamecorpus/game_script.html", context)


def _setSpeechType(currentType, previousSetType):
    setType = currentType
    if currentType == "speaker":
        if previousSetType == "speaker_a":
            setType = "speaker_b"
        else:
            setType = "speaker_a"

    return setType
