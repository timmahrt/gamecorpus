from __future__ import annotations

from django.db import models
from django.db import transaction


class GameScript(models.Model):
    title = models.CharField(max_length=100)
    sourceAttributionUrl = models.CharField(max_length=100, default="")
    comment = models.CharField(max_length=300, default="")
    version = models.IntegerField(default=1)
    isPlayed = models.BooleanField(default=False)
    numSentences = models.IntegerField(default=0)
    numWords = models.IntegerField(default=0)

    class Meta:
        unique_together = ("title", "version")

    def __str__(self):
        return "%s_%d" % (self.title, self.version)

    def toJson(self) -> dict:
        return {
            "game_content": self.title,
            "version": self.version,
            "content": [partition.toJson() for partition in self.partition_set.all()],
            "comment": self.comment,
            "is_played": self.isPlayed,
        }

    def setWordAndSentenceCounts(self) -> None:
        scriptNumSentences = 0
        scriptNumWords = 0

        for partition in self.partition_set.all():
            numWords = 0
            numSentences = 0
            for event in partition.event_set.all():
                for utterance in event.utterance_set.all():
                    numSentences += len(utterance.sentence_set.all())
                    numWords += len(
                        [
                            word
                            for sentence in utterance.tokenizedsentence_set.all()
                            for word in sentence.tokenizedsentenceword_set.all()
                        ]
                    )

            scriptNumWords += numWords
            scriptNumSentences += numSentences

            partition.numWords = numWords
            partition.numSentences = numSentences
            partition.save()

        self.numWords = scriptNumWords
        self.numSentences = scriptNumSentences
        self.save()


class Partition(models.Model):
    fileName = models.CharField(max_length=100)
    title = models.CharField(max_length=100, default="")
    numSentences = models.IntegerField(default=0)
    numWords = models.IntegerField(default=0)
    script = models.ForeignKey(GameScript, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("fileName", "script")

    def __str__(self):
        return self.fileName

    def toJson(self) -> dict:
        events = []
        for event in self.event_set.all():
            events.append(event.toJson())

        return {"source": self.fileName, "title": self.title, "sections": events}


class Event(models.Model):
    partition = models.ForeignKey(Partition, on_delete=models.CASCADE)

    def toJson(self) -> list:
        utterances = []
        for utterance in self.utterance_set.all():
            utterances.append(utterance.toJson())

        return utterances


class Utterance(models.Model):
    class UtteranceType(models.TextChoices):
        SPEAKER = ("sp", "Speaker")
        CONTEXT = ("co", "Context")
        CHOICE = ("ch", "Choice")

    speaker = models.CharField(max_length=50)
    utteranceType = models.CharField(max_length=2, choices=UtteranceType.choices)
    event = models.ForeignKey(Event, on_delete=models.CASCADE)

    def __str__(self):
        return "%s_%s_%s" % (self.id, self.speaker, self.utteranceType)

    def toJson(self) -> dict:
        return {
            "speaker": self.speaker,
            "speech": [sentence.text for sentence in self.sentence_set.all()],
            "type": self.utteranceType,
            "tokenized_speech": [
                sentence.toJson() for sentence in self.tokenizedsentence_set.all()
            ],
        }

    @classmethod
    def createFromData(
        cls,
        event: Event,
        speaker: str,
        utteranceType: str,
        sentences: list,
        tokenizedSentences: list,
    ) -> Utterance:
        utterance = cls.objects.create(
            speaker=speaker,
            utteranceType=utteranceType,
            event=event,
        )
        for sentence in sentences:
            Sentence.objects.create(text=sentence, utterance=utterance)

        for tokenizedWords in tokenizedSentences:
            TokenizedSentence.createFromWords(utterance, tokenizedWords)

        return utterance


class Sentence(models.Model):
    text = models.CharField(max_length=200)
    utterance = models.ForeignKey(Utterance, on_delete=models.CASCADE)


class TokenizedWord(models.Model):
    class PosType(models.TextChoices):
        # https://universaldependencies.org/docsv1/ja/overview/morphology.html
        ADJ = "形容詞"
        ADP = "助詞"
        ADN = "形状詞"
        ADV = "副詞"
        AUX = "助動詞"
        CONJ = "接続詞"
        DET = "連体詞"
        INTJ = "感動詞"
        NOUN = "名詞"
        PREFIX = "接頭辞"
        PRP = "代名詞"
        PUNCT = "補助記号"
        SPACE = "空白"
        SUFFIX = "接尾辞"
        SYM = "記号"
        VERB = "動詞"

    text = models.CharField(max_length=20)
    pos = models.CharField(max_length=4, choices=PosType.choices)
    lemma = models.CharField(max_length=20)

    def toJson(self) -> list:
        return [self.text, self.pos, self.lemma]

    def getContainedUtterances(self):
        return [
            tokenizedSentenceWord.sentence.utterance
            for tokenizedSentenceWord in self.tokenizedsentenceword_set
        ]

    @classmethod
    def safeCreate(cls, text: str, pos: str, lemma: str) -> TokenizedWord:
        match = cls.objects.all().filter(text=text, pos=pos, lemma=lemma)
        if len(match) == 0:
            tokenizedWord = TokenizedWord.objects.create(
                text=text, pos=pos, lemma=lemma
            )
        else:
            tokenizedWord = match.get()

        return tokenizedWord

    @classmethod
    def bulkInsert(cls, tokenizedWords) -> None:
        words = [word for word, _, _ in tokenizedWords]
        existingTokenizedWords = (
            cls.objects.values_list("text", "pos", "lemma").all().filter(text__in=words)
        )
        newWords = set(tokenizedWords) - set(existingTokenizedWords)
        newWords = [
            TokenizedWord(text=text, pos=pos, lemma=lemma)
            for text, pos, lemma in newWords
        ]

        cls.objects.bulk_create(newWords)

    class Meta:
        unique_together = ("text", "pos", "lemma")


class TokenizedSentence(models.Model):
    utterance = models.ForeignKey(Utterance, on_delete=models.CASCADE)

    def toJson(self):
        tokenizedSentences = []
        for word in self.tokenizedsentenceword_set.all():
            tokenizedSentences.append(word.toJson())

        return tokenizedSentences

    @classmethod
    def createFromWords(cls, utterance: Utterance, words: list) -> TokenizedSentence:
        tokenizedSentence = cls.objects.create(utterance=utterance)
        for word in words:
            tokenizedWord = TokenizedWord.safeCreate(word[0], word[1], word[2])
            TokenizedSentenceWord.objects.create(
                word=tokenizedWord, sentence=tokenizedSentence
            )

        return tokenizedSentence


class TokenizedSentenceWord(models.Model):
    sentence = models.ForeignKey(TokenizedSentence, on_delete=models.CASCADE)
    word = models.ForeignKey(TokenizedWord, on_delete=models.CASCADE)

    def toJson(self):
        return self.word.toJson()


@transaction.atomic
def createFromJson(json: dict):
    """
    Given a parsed json representation of a gamescript, save it to the database

    TODO: Investigate why this is so slow 1~2 minutes to complete
    """
    # # Pre-insert all words in the corpus
    # # (Somehow, this did not change the time-to-completion)
    # tokenizedWords = []
    # for jsonPartition in json["content"]:
    #     for jsonEvent in jsonPartition["sections"]:
    #         for jsonUtterance in jsonEvent:
    #             for tokenizedSentence in jsonUtterance["tokenized_speech"]:
    #                 tokenizedWords.extend(
    #                     [tuple(tokenizedWord) for tokenizedWord in tokenizedSentence]
    #                 )

    # TokenizedWord.bulkInsert(tokenizedWords)

    # Build the main script and all dependent data
    script = GameScript.objects.create(
        title=json["game_content"],
        sourceAttributionUrl=json["source_attribute_url"],
        version=json["version"],
        comment=json["comment"] or "",
        isPlayed=json["is_played"] or False,
    )

    for jsonPartition in json["content"]:
        partition = Partition.objects.create(
            fileName=jsonPartition["source"],
            title=jsonPartition["title"] or "",
            script=script,
        )
        for jsonEvent in jsonPartition["sections"]:
            event = Event.objects.create(partition=partition)
            for jsonUtterance in jsonEvent:
                Utterance.createFromData(
                    event=event,
                    speaker=jsonUtterance["speaker"],
                    utteranceType=jsonUtterance["type"],
                    sentences=jsonUtterance["speech"],
                    tokenizedSentences=jsonUtterance["tokenized_speech"],
                )

    script.setWordAndSentenceCounts()


def gamescriptToJson(title: str, version: str = None) -> dict:
    """
    Get game script heirarchy as a dictionary (for saving as json, etc)
    """
    scripts = GameScript.objects.all().filter(title=title)
    if version:
        scripts = scripts.filter(version=version)

    if len(scripts) == 0:
        print("No title with that name and version")
        return
    if len(scripts) > 1:
        print("The following titles with versions were found.  Please choose one.")
        print([script.title for script in scripts])
        return

    script = scripts[0]
    return script.toJson()
