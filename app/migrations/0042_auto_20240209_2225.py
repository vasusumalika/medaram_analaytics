# Generated by Django 3.2.5 on 2024-02-09 16:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0041_auto_20240209_1528'),
    ]

    operations = [
        migrations.AlterField(
            model_name='outdepotvehiclereceive',
            name='unique_no',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
        migrations.AlterField(
            model_name='tripstatistics',
            name='unique_code',
            field=models.CharField(blank=True, max_length=256, null=True),
        ),
    ]
