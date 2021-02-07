import os

from django.core.management.base import BaseCommand
from gamecorpus import models
from gamecorpus import services


class Command(BaseCommand):
    help = "Adds data to the database from json files stored on disk"

    def add_arguments(self, parser):
        parser.add_argument("root_path", nargs=1, type=str)

    def handle(self, *args, **options):
        root = options["root_path"][0]
        fnList = [fn for fn in os.listdir(root) if ".json" in fn]
        fnList.sort()
        for fn in fnList:
            jsonText = services.loadJsonFile(os.path.join(root, fn))
            title = jsonText["game_content"]
            version = jsonText["version"]
            match = models.GameScript.objects.all().filter(title=title, version=version)
            if not match:
                models.createFromJson(jsonText)
                self.stdout.write(f"{title}:{version} added")
            else:
                self.stdout.write(f"{title}:{version} already exists -- skipping")
