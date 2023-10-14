# Generated by Django 4.1.4 on 2023-09-11 19:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        # ('shop', '0004_color_size_product_quantity_delete_variation_and_more'),
        ('orderapp', '0002_remove_orderproduct_variations'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderproduct',
            name='color',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='shop.color'),
        ),
        migrations.AddField(
            model_name='orderproduct',
            name='size',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='shop.size'),
        ),
    ]
