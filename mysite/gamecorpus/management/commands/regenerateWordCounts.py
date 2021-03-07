from django.core.management.base import BaseCommand
from gamecorpus import models


class Command(BaseCommand):
    help = "Exports a script from the database to json"

    def handle(self, *args, **options):
        for script in models.GameScript.objects.all():
            script.setWordAndSentenceCounts()
