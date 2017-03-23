# -*- coding: utf-8 -*-
# Generated by Django 1.10.1 on 2017-03-20 14:55
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0016_auto_20170209_1753'),
    ]

    operations = [
        migrations.AlterField(
            model_name='appropriationaccountbalances',
            name='data_source',
            field=models.CharField(choices=[('USA', 'USAspending'), ('DBR', 'DATA Act Broker')], help_text='The source of this entry, either Data Broker (DBR) or USASpending (USA)', max_length=3, null=True),
        ),
        migrations.AlterField(
            model_name='treasuryappropriationaccount',
            name='data_source',
            field=models.CharField(choices=[('USA', 'USAspending'), ('DBR', 'DATA Act Broker')], help_text='The source of this entry, either Data Broker (DBR) or USASpending (USA)', max_length=3, null=True),
        ),
    ]