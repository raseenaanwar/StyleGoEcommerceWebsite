# Generated by Django 4.2.5 on 2023-10-03 17:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orderapp', '0006_orderproduct_is_wallet_purchase_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='wallet',
            name='is_used',
            field=models.BooleanField(default=False),
        ),
    ]
