from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('quiz', '0003_topscorerun_topic'),
    ]

    operations = [
        migrations.AddField(
            model_name='topscorerun',
            name='selection_mode',
            field=models.CharField(
                choices=[
                    ('legacy', 'Legacy random selection'),
                    ('random_control', 'Randomized comparison'),
                    ('history', 'History-based adaptive selection'),
                    ('neural', 'Neural adaptive selection'),
                    ('offline', 'Offline selection'),
                ],
                default='legacy',
                help_text='Selection strategy used for this run; recorded for evaluation.',
                max_length=20,
            ),
        ),
        migrations.AddIndex(
            model_name='topscorerun',
            index=models.Index(fields=['selection_mode', 'started_at'], name='quiz_run_selection_date_idx'),
        ),
    ]
