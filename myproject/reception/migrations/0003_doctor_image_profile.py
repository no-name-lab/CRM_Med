# Generated by Django 5.2.1 on 2025-05-31 16:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reception', '0002_alter_doctor_cabinet'),
    ]

    operations = [
        migrations.AddField(
            model_name='doctor',
            name='image_profile',
            field=models.FileField(blank=True, null=True, upload_to=''),
        ),
    ]
