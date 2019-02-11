# Generated by Django 2.1.6 on 2019-02-11 15:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('journal', '0008_remove_userinfo_deleted'),
    ]

    operations = [
        migrations.AlterField(
            model_name='entry',
            name='content',
            field=models.BinaryField(editable=True),
        ),
        migrations.AlterField(
            model_name='journal',
            name='content',
            field=models.BinaryField(editable=True),
        ),
        migrations.AlterField(
            model_name='journalmember',
            name='key',
            field=models.BinaryField(editable=True),
        ),
        migrations.AlterField(
            model_name='userinfo',
            name='content',
            field=models.BinaryField(editable=True),
        ),
        migrations.AlterField(
            model_name='userinfo',
            name='pubkey',
            field=models.BinaryField(editable=True),
        ),
    ]
