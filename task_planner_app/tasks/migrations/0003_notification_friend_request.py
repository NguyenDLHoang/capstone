# Generated by Django 3.2.13 on 2022-07-25 13:18

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0003_remove_user_proficiencies'),
        ('tasks', '0002_auto_20220724_1758'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='friend_request',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='users.friendrequest'),
        ),
    ]