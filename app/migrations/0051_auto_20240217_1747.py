# Generated by Django 3.2.5 on 2024-02-17 17:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0050_alter_outdepotvehiclereceive_new_log_sheet_no'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='hsdoilsubmission',
            name='special_bus_data_entry',
        ),
        migrations.AddField(
            model_name='hsdoilsubmission',
            name='is_bus_number',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
    ]
