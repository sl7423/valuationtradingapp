# Generated by Django 2.2.5 on 2022-07-25 01:24

from django.db import migrations, models
import tradingapp.models


class Migration(migrations.Migration):

    dependencies = [
        ('tradingapp', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='stock',
            name='ticker',
            field=models.CharField(max_length=10, validators=[tradingapp.models.validate_ticker]),
        ),
    ]
