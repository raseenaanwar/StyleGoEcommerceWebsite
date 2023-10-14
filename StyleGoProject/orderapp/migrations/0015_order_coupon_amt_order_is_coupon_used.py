# Generated by Django 4.2.5 on 2023-10-11 02:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orderapp', '0014_order_tax_amount_order_total_with_tax'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='coupon_amt',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='order',
            name='is_coupon_used',
            field=models.BooleanField(default=False),
        ),
    ]
