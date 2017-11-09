import sys

import requests
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from pretix.base.models import Event


class Command(BaseCommand):
    help = "Import data from appsmart"

    def add_arguments(self, parser):
        parser.add_argument('event_id', type=int)
        parser.add_argument('url', type=str)
        parser.add_argument('branch_id', type=int)

    def handle(self, *args, **options):
        event = Event.objects.get(pk=options.get('event_id'))
        event.items.all().delete()
        event.categories.all().delete()

        event.quotas.get_or_create(name="all", size=None)
        r = requests.get(
            '{url}get-categories/{branch_id}'.format(**options)
        )
        for i, record in enumerate(r.json()['d']):
            self.add_category(options, i, event, record)

    def add_category(self, options, i, event, record):
        cat = event.categories.create(
            name=record.get('name'),
            description=record.get('description') or "",
            position=i
        )
        r = requests.get(
            '{options[url]}get-products-of-category/{options[branch_id]}/{r[id]}'.format(
                options=options, r=record
            )
        )
        for i, record in enumerate(r.json()['d']):
            self.add_item(options, i, event, cat, record)

    def add_item(self, options, i, event, category, record):
        r = requests.get(
            '{options[url]}get-single-product/{options[branch_id]}/{r[id]}'.format(
                options=options, r=record
            )
        )
        record = r.json()['d']

        for sizeid, s in record['sizes'].items():
            item = event.items.create(
                name='{record[name]} – {s[name]}'.format(record=record, s=s),
                description=record['description'] or '',
                category=category,
                position=i,
                default_price=s.get('delivery_price')
            )
            event.quotas.get(name="all").items.add(item)
            if record.get('picurl'):
                imgf = requests.get(record.get('picurl'))
                item.picture.save(
                    'picture.jpg',
                    ContentFile(imgf.content)
                )
                item.save()

            for ig in record.get('basic_ingredients_groups').values():
                self.add_ingredients_group(sizeid, i, event, item, ig)

            for ig in record.get('extra_ingredients_groups').values():
                self.add_ingredients_group(sizeid, i, event, item, ig)

    def add_ingredients_group(self, sizeid, i, event, item, record):
        cat = event.categories.create(
            name='{} – {}'.format(
                record.get('description'),
                item.name,
            ),
            is_addon=True
        )
        max_quan = record.get('max_quan')
        if 0 < record.get('free_quan') < max_quan:
            max_quan = record.get('free_quan')
        if max_quan == -1:
            max_quan = len(record.get('ingredients')) + 1

        item.addons.create(
            addon_category=cat,
            min_count=record.get('min_quan'),
            max_count=max_quan
        )
        for i in record.get('ingredients').values():
            item = event.items.create(
                name=i.get('name'),
                category=cat,
                default_price=i.get('price_diff').get(sizeid).get('price')
            )
            event.quotas.get(name="all").items.add(item)
