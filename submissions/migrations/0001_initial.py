# Generated by Django 5.2.4 on 2025-07-19 15:00

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DspEntityQueue',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('entity_type', models.CharField(max_length=50)),
                ('payload', models.JSONField()),
                ('status', models.CharField(choices=[('waiting', 'Waiting'), ('pending', 'Pending'), ('submitted', 'Submitted'), ('completed', 'Completed'), ('failed', 'Failed')], default='waiting', max_length=20)),
                ('attempts', models.IntegerField(default=0)),
                ('last_error', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('depends_on', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='submissions.dspentityqueue')),
            ],
        ),
        migrations.CreateModel(
            name='DspEntityAudit',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('attempt_at', models.DateTimeField(auto_now_add=True)),
                ('http_status', models.IntegerField(null=True)),
                ('response', models.JSONField(null=True)),
                ('backoff_secs', models.IntegerField(default=0)),
                ('queue', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='audits', to='submissions.dspentityqueue')),
            ],
        ),
    ]
