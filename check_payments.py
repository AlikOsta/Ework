#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ework.settings')
django.setup()

from ework_premium.models import Payment

print('Последние платежи:')
for p in Payment.objects.order_by('-id')[:5]:
    print(f'ID: {p.id}, Status: {p.status}, User: {p.user.id}, Post data exists: {bool(p.post_data)}')
    if p.post_data:
        print(f'  Post data keys: {list(p.post_data.keys())}')
        if 'form_data' in p.post_data:
            print(f'  Form data keys: {list(p.post_data["form_data"].keys()) if p.post_data["form_data"] else "None"}')
    print()
