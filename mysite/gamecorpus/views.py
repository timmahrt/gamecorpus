import os

from django.shortcuts import render

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


def scripts(request):
    gameScripts = models.GameScript.objects.values("title").all()
    gameTitles = [gameScript["title"] for gameScript in gameScripts]
    context = {"availables_game_titles": gameTitles}

    return render(request, "gamecorpus/list.html", context)


def scriptSections(request):
    title = request.GET["title"]
    script = models.GameScript.objects.get(title=title)
    partitions = script.partition_set.values("fileName").all()
    fileNames = [partition["fileName"] for partition in partitions]
    context = {"title": title, "available_partition_names": fileNames}

    return render(request, "gamecorpus/game_sections.html", context)


def script(request):
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
            setType = setSpeechType(utterance.utteranceType, setType)
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
        "title": title,
        "fileName": os.path.splitext(partitionName)[0],
        "events": events,
    }

    return render(request, "gamecorpus/game_script.html", context)


def setSpeechType(currentType, previousSetType):
    setType = currentType
    if currentType == "speaker":
        if previousSetType == "speaker_a":
            setType = "speaker_b"
        else:
            setType = "speaker_a"

    return setType
