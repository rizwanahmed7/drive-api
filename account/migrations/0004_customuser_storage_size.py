# Generated by Django 4.2.6 on 2023-10-30 23:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0003_remove_folder_owner_remove_thumbnail_owner_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='storage_size',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
