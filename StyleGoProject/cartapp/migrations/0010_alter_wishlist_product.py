# Generated by Django 4.1.4 on 2023-09-21 16:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        # ('shop', '0005_remove_product_colors_remove_product_quantity_and_more'),
        ('cartapp', '0009_wishlist'),
    ]

    operations = [
        migrations.AlterField(
            model_name='wishlist',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='shop.product'),
        ),
    ]
