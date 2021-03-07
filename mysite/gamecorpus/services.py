import os
import io
import json
import re

from gamecorpus import models


def loadJsonFile(fn):
    with io.open(fn, "r", encoding="utf-8") as fd:
        return json.load(fd)


def saveJsonFile(fn, jsonTxt):
    with io.open(fn, "w", encoding="utf-8") as fd:
        json.dump(jsonTxt, fd, ensure_ascii=False)


def _iterateJson(root):
    jsonList = os.listdir(root)
    jsonList = [fn for fn in jsonList if ".json" in fn]
    jsonList.sort()
    for fn in jsonList:
        with io.open(os.path.join(root, fn), "r", encoding="utf-8") as fd:
            yield fn, json.load(fd)


def _iterateTexts(root):
    for fn, gameData in _iterateJson(root):
        for content in gameData["content"]:
            for section in content["sections"]:
                for utterance in section:
                    if utterance["type"] != "speaker":
                        continue
                    yield gameData["game_content"], utterance


def searchDb(root, reStr, posList, tokenized, limitPerGame=1, limit=10):
    if tokenized:
        matches = _tokenizedDbSearch(reStr, posList, limitPerGame, limit)
    else:
        matches = _dbSearch(reStr, limitPerGame, limit)

    return matches


def _tokenizedDbSearch(reStr, posList, limitPerGame=1, limit=10):
    matches = []

    searchRe = re.compile(reStr)
    words = models.TokenizedWord.objects.all()
    if posList:
        posList = [posMap[pos] for pos in posList]
        words = words.filter(pos__in=posList)
    for word in words:
        match = searchRe.match(word.text)
        if match:
            for tokenizedSentenceWord in word.tokenizedsentenceword_set.all():
                utterance = tokenizedSentenceWord.sentence.utterance

                i = [ts for ts in utterance.tokenizedsentence_set.all()].index(
                    tokenizedSentenceWord.sentence
                )

                matches.append(
                    {
                        "title": utterance.event.partition.script.title,
                        "speaker": utterance.speaker,
                        "match": word.text,
                        "sentence": wrapMatch(
                            # TODO: Merge sentences and TokenizedSentence together
                            utterance.sentence_set.all()[i].text,
                            match.group(0),
                        ),
                    }
                )
                if len(matches) > limit:
                    break

        if len(matches) >= limit:
            matches = matches[:limit]
            break

    return matches


def _dbSearch(reStr, limitPerGame=1, limit=10):
    matches = []

    searchRe = re.compile(reStr)
    print(len(models.Sentence.objects.all()))
    for i, sentence in enumerate(models.Sentence.objects.all()):
        match = searchRe.search(sentence.text)
        if match:
            matchTxt = match.group(0)
            matches.append(
                {
                    "title": sentence.utterance.event.partition.script.title,
                    "speaker": sentence.utterance.speaker,
                    "match": matchTxt,
                    "sentence": wrapMatch(sentence.text, matchTxt),
                }
            )
            if len(matches) >= limit:
                break

    return matches


def searchCorpus(root, reStr, posList, tokenized, limitPerGame=1, limit=10):
    posList = [posMap[pos] for pos in posList]
    searchRe = re.compile(reStr)

    searchFunc = _search
    if tokenized:
        searchFunc = _tokenizedSearch

    retList = []
    for result in searchFunc(root, searchRe, posList, limitPerGame):
        retList.append(result)
        if len(retList) > limit:
            break

    return retList


def _tokenizedSearch(root, searchRe, posList, limitPerGame):
    lastTitle = None
    for title, utterance in _iterateTexts(root):
        if lastTitle != title:
            utterancesForCurrentGame = 0
            lastTitle = title

        for i, sentence in enumerate(utterance["tokenized_speech"]):
            if utterancesForCurrentGame >= limitPerGame:
                break
            for word, pos, _ in sentence:
                if len(posList) > 0 and pos not in posList:
                    continue
                match = searchRe.search(word)
                if match:
                    utterancesForCurrentGame += 1
                    highlightedText = wrapMatch(utterance["speech"][i], match.group(0))
                    yield {
                        "title": title,
                        "speaker": utterance["speaker"],
                        "match": word,
                        "sentence": highlightedText,
                    }
                    break


def _search(root, searchRe, _posList, limitPerGame):
    lastTitle = None
    for title, utterance in _iterateTexts(root):
        if lastTitle != title:
            utterancesForCurrentGame = 0
            lastTitle = title

        for i, sentence in enumerate(utterance["speech"]):
            if utterancesForCurrentGame >= limitPerGame:
                break
            match = searchRe.search(sentence)
            if match:
                utterancesForCurrentGame += 1
                matchTxt = match.group(0)
                highlightedText = wrapMatch(utterance["speech"][i], matchTxt)
                yield {
                    "title": title,
                    "speaker": utterance["speaker"],
                    "match": matchTxt,
                    "sentence": highlightedText,
                }


def wrapMatch(text, textToWrap):
    return text.replace(textToWrap, f"<span class='highlight'>{textToWrap}</span>")


posMap = {"V": "動詞", "N": "名詞", "Adv": "副詞", "Adj": "形容詞", "Adn": "連体詞", "AdjN": "形状詞"}
