# Generated by Django 5.1.1 on 2024-10-07 22:43

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0021_alter_user_options_alter_user_managers_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='age',
            field=models.IntegerField(validators=[django.core.validators.MinValueValidator(15)]),
        ),
    ]
