# Copyright 2015 Digital Borderlands Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License, version 3,
# as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                (
                    'id',
                    models.AutoField(
                        verbose_name='ID',
                        serialize=False,
                        auto_created=True,
                        primary_key=True
                    )
                ),
                ('active', models.BooleanField()),
                ('datetime', models.DateTimeField(auto_now=True)),
                ('user_root', models.IntegerField()),
                ('author', models.TextField(max_length=64)),
                ('name', models.TextField(max_length=64)),
                ('password', models.TextField(max_length=64)),
            ],
        ),
        migrations.CreateModel(
            name='Value',
            fields=[
                (
                    'entry_id',
                    models.AutoField(serialize=False, primary_key=True)
                ),
                ('active', models.BooleanField()),
                ('id', models.IntegerField()),
                ('parent', models.IntegerField()),
                ('name', models.TextField(max_length=128)),
                ('override', models.TextField(max_length=64)),
                ('author', models.TextField(max_length=64)),
                ('datetime', models.DateTimeField(auto_now=True)),
                ('entry', models.TextField(max_length=2048)),
                ('protect', models.BooleanField()),
                ('first_last', models.BooleanField()),
            ],
        ),
        migrations.AlterIndexTogether(
            name='value',
            index_together=set(
                [
                    ('active', 'parent', 'name', 'override'),
                    ('active', 'parent', 'id'),
                    ('active', 'id')
                ]
            ),
        ),
        migrations.AlterIndexTogether(
            name='user',
            index_together=set([('name', 'password', 'active')]),
        ),
    ]
