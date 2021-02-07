from django.core.management.base import BaseCommand
from gamecorpus import models
from gamecorpus import services


class Command(BaseCommand):
    help = "Exports a script from the database to json"

    def add_arguments(self, parser):
        parser.add_argument("title", nargs=1, type=str)
        parser.add_argument("version", nargs=1, type=str)
        parser.add_argument("outputFn", nargs=1, type=str)

    def handle(self, *args, **options):
        title = options["title"][0]
        version = options["version"][0]
        outputFn = options["outputFn"][0]

        match = models.GameScript.objects.all().filter(title=title, version=version)
        if not match:
            self.stdout.write(f"{title}:{version} does not exist -- exiting")
        else:
            jsonTxt = models.gamescriptToJson(title, version)
            services.saveJsonFile(outputFn, jsonTxt)
            self.stdout.write("exported successfully")
