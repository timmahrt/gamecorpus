from django.test import TestCase
from gamecorpus import models as m

PosType = m.TokenizedWord.PosType
UtteranceType = m.Utterance.UtteranceType


class GamecorpusTestCase(TestCase):
    @classmethod
    def setUpClass(self):
        super().setUpClass()
        script = m.GameScript.objects.create(title="Fantasy Adventure", version="1")
        partition = m.Partition.objects.create(fileName="first.txt", script=script)
        event = m.Event.objects.create(partition=partition)

        m.Utterance.createFromData(
            event,
            "",
            UtteranceType.CONTEXT,
            ["玄関で"],
            [[["玄関", "名詞", "玄関"], ["で", "助詞", "を"]]],
        )

        m.Utterance.createFromData(
            event,
            "Bahamut",
            UtteranceType.SPEAKER,
            ["昼ごはんを食べた？", "スーパーに行くのです。"],
            [
                [
                    ["昼ごはん", "名詞", "昼ごはん"],
                    ["を", "助詞", "を"],
                    ["食べ", "動詞", "食べる"],
                    ["た", "助動詞", "た"],
                    ["？", "補助記号", "？"],
                ],
                [
                    ["スーパー", "名詞", "スーパー"],
                    ["に", "助詞", "に"],
                    ["行く", "動詞", "行く"],
                    ["の", "助詞", "の"],
                    ["です", "助動詞", "です"],
                    ["。", "補助記号", "。"],
                ],
            ],
        )

        m.Utterance.createFromData(
            event,
            "Shiva",
            UtteranceType.SPEAKER,
            ["大丈夫です。"],
            [[["大丈夫", "形状詞", "大丈夫"], ["です", "助動詞", "です"], ["。", "補助記号", "。"]]],
        )

    def testClimbUpTree(self):
        word = m.TokenizedWord.objects.all().first()
        tokenizedSentenceWord = word.tokenizedsentenceword_set.first()
        script = tokenizedSentenceWord.sentence.utterance.event.partition.script

        self.assertEqual("Fantasy Adventure", script.title)

    def testModelCoherence(self):
        script = m.GameScript.objects.all().get(title="Fantasy Adventure")

        partitions = script.partition_set.all()
        events = partitions[0].event_set.all()
        utterances = events[0].utterance_set.all()

        self.assertEqual(3, len(utterances))

        utterance1 = utterances[1]
        self.assertEqual("Bahamut", utterance1.speaker)
        self.assertEqual(UtteranceType.SPEAKER, utterance1.utteranceType)

        sentences = utterance1.sentence_set.all()
        self.assertEqual("昼ごはんを食べた？", sentences[0].text)
        self.assertEqual(2, len(sentences))

        tokenizedSentences = utterance1.tokenizedsentence_set.all()
        self.assertEqual(2, len(tokenizedSentences))

        tokenizedWords = tokenizedSentences[0].tokenizedsentenceword_set.all()
        self.assertEqual(5, len(tokenizedWords))

        self.assertEqual("昼ごはん", tokenizedWords[0].word.text)
        self.assertEqual(PosType.NOUN, tokenizedWords[0].word.pos)
        self.assertEqual("昼ごはん", tokenizedWords[0].word.lemma)

        self.assertEqual("食べ", tokenizedWords[2].word.text)
        self.assertEqual(PosType.VERB, tokenizedWords[2].word.pos)
        self.assertEqual("食べる", tokenizedWords[2].word.lemma)

        tokenizedWords = tokenizedSentences[1].tokenizedsentenceword_set.all()
        self.assertEqual(6, len(tokenizedWords))
