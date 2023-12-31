# Generated by Django 4.1.4 on 2023-09-23 16:58

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='productvariant',
            name='colors',
        ),
        migrations.RemoveField(
            model_name='productvariant',
            name='sizes',
        ),
        migrations.AddField(
            model_name='productvariant',
            name='color',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='shop.color'),
        ),
        migrations.AddField(
            model_name='productvariant',
            name='size',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='shop.size'),
        ),
    ]
