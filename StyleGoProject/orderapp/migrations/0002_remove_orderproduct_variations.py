# Generated by Django 4.1.4 on 2023-09-11 19:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orderapp', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='orderproduct',
            name='variations',
        ),
    ]
