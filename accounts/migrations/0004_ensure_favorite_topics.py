from django.db import migrations


TOPICS = (
    ('ancient-civilizations', 'Ancient Civilizations', 'Empires, myths, rulers, and lost cities.', 1),
    ('medieval-world', 'Medieval World', 'Kingdoms, scholars, trade, and conquest.', 2),
    ('revolutions', 'Age of Revolutions', 'Ideas and uprisings that reshaped nations.', 3),
    ('inventions', 'Inventions', 'Discoveries that changed how humanity lives.', 4),
    ('computing', 'Computing & AI', 'From early machines to intelligent systems.', 5),
    ('mixed-knowledge', 'Across the Ages', 'A balanced challenge drawn from every archive.', 6),
)


def ensure_favorite_topics(apps, schema_editor):
    Topic = apps.get_model('quiz', 'Topic')
    database = schema_editor.connection.alias

    for slug, title, description, sort_order in TOPICS:
        topic, _ = Topic.objects.using(database).get_or_create(
            slug=slug,
            defaults={
                'title': title,
                'description': description,
                'sort_order': sort_order,
                'is_active': True,
            },
        )
        if not topic.is_active:
            topic.is_active = True
            topic.save(using=database, update_fields=('is_active',))


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_user_favorite_topic'),
        ('quiz', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(ensure_favorite_topics, migrations.RunPython.noop),
    ]
