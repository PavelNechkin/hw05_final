# Generated by Django 2.2.16 on 2022-04-18 16:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('posts', '0011_follow'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='follow',
            constraint=models.UniqueConstraint(fields=('user', 'author'), name='%(app_label)s_%(class)s_name_unique'),
        ),
    ]
