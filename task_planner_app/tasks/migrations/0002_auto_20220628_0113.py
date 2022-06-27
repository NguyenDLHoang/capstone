# Generated by Django 3.2.13 on 2022-06-27 15:13

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tasks', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='task',
            name='priority',
            field=models.CharField(choices=[('Lowest', 'Lowest'), ('Low', 'Low'), ('Medium', 'Medium'), ('High', 'High'), ('Highest', 'Highest')], default='LOWEST', max_length=8),
        ),
        migrations.AlterField(
            model_name='task',
            name='status',
            field=models.CharField(choices=[(0, 'To do'), (1, 'In progress'), (2, 'Review'), (3, 'Complete')], default='TO_DO', max_length=8),
        ),
    ]
