# Generated by Django 4.2.5 on 2023-10-11 19:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('cartapp', '0018_cart_tax_amount_cart_total_with_tax'),
    ]

    operations = [
        migrations.AddField(
            model_name='cart',
            name='coupon_amount',
            field=models.FloatField(default=0),
        ),
    ]