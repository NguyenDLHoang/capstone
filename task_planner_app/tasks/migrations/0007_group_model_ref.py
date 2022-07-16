# Generated by Django 3.2.13 on 2022-07-16 05:42

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0006_alter_taskgroup_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='list_group',
            field=models.ForeignKey(default='', null=True, on_delete=django.db.models.deletion.CASCADE, to='tasks.taskgroup'),
        ),
        migrations.AddField(
            model_name='taskgroup',
            name='list_group',
            field=models.ForeignKey(default='', null=True, on_delete=django.db.models.deletion.CASCADE, to='tasks.taskgroup'),
        ),
    ]
