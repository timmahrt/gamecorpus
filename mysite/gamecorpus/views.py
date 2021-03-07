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
    scripts = models.GameScript.objects.values_list(
        "title", "isPlayed", "sourceAttributionUrl"
    ).all()
    context = {"availables_game_titles": scripts}

    return render(request, "gamecorpus/list.html", context)


def scriptSections(request):
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
        "game_title": title,
        "partition_title": partition.title,
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
