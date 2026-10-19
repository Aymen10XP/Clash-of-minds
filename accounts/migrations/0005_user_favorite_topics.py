from django.db import migrations, models


def copy_favorite_topic(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    through = User.favorite_topics.through
    database = schema_editor.connection.alias
    rows = [
        through(user_id=user.pk, topic_id=user.favorite_topic_id)
        for user in User.objects.using(database).exclude(favorite_topic_id=None)
    ]
    through.objects.using(database).bulk_create(rows, ignore_conflicts=True)


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0004_ensure_favorite_topics'),
        ('quiz', '0003_topscorerun_topic'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='favorite_topics',
            field=models.ManyToManyField(blank=True, related_name='favorite_players', to='quiz.topic'),
        ),
        migrations.RunPython(copy_favorite_topic, migrations.RunPython.noop),
        migrations.RemoveField(model_name='user', name='favorite_topic'),
    ]
