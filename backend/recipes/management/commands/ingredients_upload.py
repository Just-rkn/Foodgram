import csv
import json
import os

from django.core.management.base import BaseCommand
from django.db.utils import IntegrityError

from recipes.models import Ingredient


class Command(BaseCommand):

    def upload_to_db(self, path_to_file):
        with open(path_to_file, encoding='utf-8', mode='r') as file:
            data_for_db = []
            if path_to_file[-4:] == '.csv':
                reader = csv.reader(file)
                for name, measurement_unit in reader:
                    data_for_db.append(
                        {
                            'name': name,
                            'measurement_unit': measurement_unit,
                        }
                    )
            elif path_to_file[-5:] == '.json':
                data_for_db = json.load(file)

            try:
                for row_for_db in data_for_db:
                    Ingredient.objects.create(**row_for_db)
                self.stdout.write(f'{path_to_file} is uploaded.')
            except IntegrityError as e:
                self.stdout.write(
                    f'in {path_to_file} | {str(e)} | {row_for_db}'
                )

    def add_arguments(self, parser):
        parser.add_argument('directory', type=str, help='/path/to/file')

    def handle(self, *args, **options):
        directory = options['directory']

        if not os.path.exists(directory):
            self.stdout.write(self.style.ERROR(
                f'Directory "{directory}" does not exist.')
            )
            return

        self.upload_to_db(directory)
