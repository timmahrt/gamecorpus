import os
import io
import json
import re


def _iterateJson(root):
    jsonList = os.listdir(root)
    jsonList = [fn for fn in jsonList if ".json" in fn]
    jsonList.sort()
    for fn in jsonList:
        with io.open(os.path.join(root, fn)) as fd:
            yield fn, json.load(fd)


def _iterateTexts(root):
    for fn, gameData in _iterateJson(root):
        for content in gameData["content"]:
            for section in content["sections"]:
                for utterance in section:
                    if utterance["type"] != "speaker":
                        continue
                    yield gameData["game_content"], utterance


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
