# Generated by Django 4.1.4 on 2023-09-26 21:13

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0004_categoryoffer'),
    ]

    operations = [
        migrations.AddField(
            model_name='coupon',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
