# Generated by Django 4.2.5 on 2023-10-07 17:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0013_alter_referral_referee_recentlysearched'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='recentlysearched',
            name='user',
        ),
    ]