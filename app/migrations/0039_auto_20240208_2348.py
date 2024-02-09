# Generated by Django 3.2.5 on 2024-02-08 18:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0038_auto_20240208_2159'),
    ]

    operations = [
        migrations.AlterField(
            model_name='tripstatistics',
            name='mhl_adult_amount',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='tripstatistics',
            name='mhl_adult_passengers',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='tripstatistics',
            name='mhl_child_amount',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='tripstatistics',
            name='mhl_child_passengers',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='tripstatistics',
            name='total_adult_passengers',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='tripstatistics',
            name='total_child_passengers',
            field=models.IntegerField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='tripstatistics',
            name='total_ticket_amount',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]