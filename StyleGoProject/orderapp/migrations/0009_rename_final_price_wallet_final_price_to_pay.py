# Generated by Django 4.2.5 on 2023-10-03 18:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orderapp', '0008_wallet_final_price'),
    ]

    operations = [
        migrations.RenameField(
            model_name='wallet',
            old_name='final_price',
            new_name='final_price_to_pay',
        ),
    ]