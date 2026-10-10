from django.core.management.base import BaseCommand
from django.db import transaction

from quiz.models import AnswerChoice, Question, Topic


TOPICS = (
    {
        'slug': 'ancient-civilizations',
        'title': 'Ancient Civilizations',
        'description': 'Empires, myths, rulers, and lost cities.',
        'sort_order': 1,
    },
    {
        'slug': 'medieval-world',
        'title': 'Medieval World',
        'description': 'Kingdoms, scholars, trade, and conquest.',
        'sort_order': 2,
    },
    {
        'slug': 'revolutions',
        'title': 'Age of Revolutions',
        'description': 'Ideas and uprisings that reshaped nations.',
        'sort_order': 3,
    },
    {
        'slug': 'inventions',
        'title': 'Inventions',
        'description': 'Discoveries that changed how humanity lives.',
        'sort_order': 4,
    },
    {
        'slug': 'computing',
        'title': 'Computing & AI',
        'description': 'From early machines to intelligent systems.',
        'sort_order': 5,
    },
    {
        'slug': 'mixed-knowledge',
        'title': 'Across the Ages',
        'description': 'A balanced challenge drawn from every archive.',
        'sort_order': 6,
    },
)


QUESTIONS = (
    {
        'topic': 'ancient-civilizations',
        'prompt': 'Which river was central to ancient Egyptian civilization?',
        'difficulty': 'easy',
        'correct': 'The Nile',
        'wrong': ('The Tigris', 'The Indus', 'The Danube'),
    },
    {
        'topic': 'ancient-civilizations',
        'prompt': 'Who became the first Roman emperor?',
        'difficulty': 'easy',
        'correct': 'Augustus',
        'wrong': ('Julius Caesar', 'Nero', 'Trajan'),
    },
    {
        'topic': 'ancient-civilizations',
        'prompt': 'Which writing system was developed in ancient Mesopotamia?',
        'difficulty': 'medium',
        'correct': 'Cuneiform',
        'wrong': ('Linear B', 'Runes', 'Hangul'),
    },
    {
        'topic': 'ancient-civilizations',
        'prompt': 'Machu Picchu was built by which civilization?',
        'difficulty': 'easy',
        'correct': 'The Inca',
        'wrong': ('The Maya', 'The Aztec', 'The Olmec'),
    },
    {
        'topic': 'ancient-civilizations',
        'prompt': 'The Peloponnesian War was primarily fought between Athens and which rival city-state?',
        'difficulty': 'medium',
        'correct': 'Sparta',
        'wrong': ('Corinth', 'Thebes', 'Troy'),
    },
    {
        'topic': 'medieval-world',
        'prompt': 'In which kingdom was Magna Carta sealed in 1215?',
        'difficulty': 'medium',
        'correct': 'England',
        'wrong': ('France', 'Castile', 'Scotland'),
    },
    {
        'topic': 'medieval-world',
        'prompt': 'What was the capital of the Byzantine Empire?',
        'difficulty': 'easy',
        'correct': 'Constantinople',
        'wrong': ('Rome', 'Alexandria', 'Antioch'),
    },
    {
        'topic': 'medieval-world',
        'prompt': 'What name was given to the warrior class of feudal Japan?',
        'difficulty': 'easy',
        'correct': 'Samurai',
        'wrong': ('Janissaries', 'Hoplites', 'Legionaries'),
    },
    {
        'topic': 'medieval-world',
        'prompt': 'Which ruler was crowned emperor in Rome on Christmas Day in the year 800?',
        'difficulty': 'medium',
        'correct': 'Charlemagne',
        'wrong': ('William the Conqueror', 'Otto I', 'Frederick Barbarossa'),
    },
    {
        'topic': 'medieval-world',
        'prompt': 'The House of Wisdom was a major center of learning in which city?',
        'difficulty': 'medium',
        'correct': 'Baghdad',
        'wrong': ('Cairo', 'Damascus', 'Cordoba'),
    },
    {
        'topic': 'revolutions',
        'prompt': 'Which prison was stormed on 14 July 1789 during the French Revolution?',
        'difficulty': 'easy',
        'correct': 'The Bastille',
        'wrong': ('The Conciergerie', 'The Louvre', 'The Temple'),
    },
    {
        'topic': 'revolutions',
        'prompt': 'In which year was the United States Declaration of Independence adopted?',
        'difficulty': 'easy',
        'correct': '1776',
        'wrong': ('1765', '1783', '1789'),
    },
    {
        'topic': 'revolutions',
        'prompt': 'Which nation declared independence from France in 1804 after a successful slave revolution?',
        'difficulty': 'medium',
        'correct': 'Haiti',
        'wrong': ('Cuba', 'Jamaica', 'Martinique'),
    },
    {
        'topic': 'revolutions',
        'prompt': 'In which country did the Industrial Revolution begin?',
        'difficulty': 'easy',
        'correct': 'Great Britain',
        'wrong': ('Germany', 'France', 'The United States'),
    },
    {
        'topic': 'revolutions',
        'prompt': 'Who wrote The Communist Manifesto with Friedrich Engels?',
        'difficulty': 'easy',
        'correct': 'Karl Marx',
        'wrong': ('Vladimir Lenin', 'Jean-Jacques Rousseau', 'Adam Smith'),
    },
    {
        'topic': 'inventions',
        'prompt': 'Who received the first United States patent for the telephone?',
        'difficulty': 'medium',
        'correct': 'Alexander Graham Bell',
        'wrong': ('Thomas Edison', 'Nikola Tesla', 'Guglielmo Marconi'),
    },
    {
        'topic': 'inventions',
        'prompt': 'Who introduced the movable-type printing press to Europe in the fifteenth century?',
        'difficulty': 'easy',
        'correct': 'Johannes Gutenberg',
        'wrong': ('Leonardo da Vinci', 'Galileo Galilei', 'Blaise Pascal'),
    },
    {
        'topic': 'inventions',
        'prompt': 'Who discovered penicillin in 1928?',
        'difficulty': 'easy',
        'correct': 'Alexander Fleming',
        'wrong': ('Louis Pasteur', 'Robert Koch', 'Joseph Lister'),
    },
    {
        'topic': 'inventions',
        'prompt': 'Who invented the World Wide Web?',
        'difficulty': 'easy',
        'correct': 'Tim Berners-Lee',
        'wrong': ('Vint Cerf', 'Alan Turing', 'Bill Gates'),
    },
    {
        'topic': 'inventions',
        'prompt': 'Who is famous for major improvements to the steam engine during the Industrial Revolution?',
        'difficulty': 'medium',
        'correct': 'James Watt',
        'wrong': ('Michael Faraday', 'Eli Whitney', 'Alessandro Volta'),
    },
    {
        'topic': 'computing',
        'prompt': 'Who is often described as the first computer programmer?',
        'difficulty': 'easy',
        'correct': 'Ada Lovelace',
        'wrong': ('Grace Hopper', 'Hedy Lamarr', 'Margaret Hamilton'),
    },
    {
        'topic': 'computing',
        'prompt': 'At which research laboratory was the transistor invented in 1947?',
        'difficulty': 'medium',
        'correct': 'Bell Labs',
        'wrong': ('Xerox PARC', 'Los Alamos', 'CERN'),
    },
    {
        'topic': 'computing',
        'prompt': 'Who created the Linux kernel?',
        'difficulty': 'easy',
        'correct': 'Linus Torvalds',
        'wrong': ('Richard Stallman', 'Ken Thompson', 'Dennis Ritchie'),
    },
    {
        'topic': 'computing',
        'prompt': 'Who proposed the imitation game now commonly called the Turing test?',
        'difficulty': 'medium',
        'correct': 'Alan Turing',
        'wrong': ('John von Neumann', 'Claude Shannon', 'Marvin Minsky'),
    },
    {
        'topic': 'computing',
        'prompt': 'Who created the Python programming language?',
        'difficulty': 'easy',
        'correct': 'Guido van Rossum',
        'wrong': ('James Gosling', 'Bjarne Stroustrup', 'Brendan Eich'),
    },
    {
        'topic': 'mixed-knowledge',
        'prompt': 'What is the largest ocean on Earth?',
        'difficulty': 'easy',
        'correct': 'The Pacific Ocean',
        'wrong': ('The Atlantic Ocean', 'The Indian Ocean', 'The Arctic Ocean'),
    },
    {
        'topic': 'mixed-knowledge',
        'prompt': 'Which element has the chemical symbol Au?',
        'difficulty': 'easy',
        'correct': 'Gold',
        'wrong': ('Silver', 'Copper', 'Argon'),
    },
    {
        'topic': 'mixed-knowledge',
        'prompt': 'Which planet is commonly called the Red Planet?',
        'difficulty': 'easy',
        'correct': 'Mars',
        'wrong': ('Venus', 'Jupiter', 'Mercury'),
    },
    {
        'topic': 'mixed-knowledge',
        'prompt': 'Who wrote the novel Nineteen Eighty-Four?',
        'difficulty': 'easy',
        'correct': 'George Orwell',
        'wrong': ('Aldous Huxley', 'Ray Bradbury', 'H. G. Wells'),
    },
    {
        'topic': 'mixed-knowledge',
        'prompt': 'Which organ pumps blood around the human body?',
        'difficulty': 'easy',
        'correct': 'The heart',
        'wrong': ('The liver', 'The lungs', 'The kidneys'),
    },
)


class Command(BaseCommand):
    help = 'Create or update the starter quiz topics and questions.'

    @transaction.atomic
    def handle(self, *args, **options):
        topics = {}
        for values in TOPICS:
            topic, _ = Topic.objects.update_or_create(
                slug=values['slug'],
                defaults={
                    'title': values['title'],
                    'description': values['description'],
                    'sort_order': values['sort_order'],
                    'is_active': True,
                },
            )
            topics[topic.slug] = topic

        created = 0
        updated = 0
        for question_index, values in enumerate(QUESTIONS):
            topic = topics[values['topic']]
            question, was_created = Question.objects.get_or_create(
                topic=topic,
                prompt=values['prompt'],
                defaults={
                    'difficulty': values['difficulty'],
                    'is_active': False,
                },
            )

            question.is_active = False
            question.difficulty = values['difficulty']
            question.save()
            question.choices.all().delete()

            correct_position = (question_index % 4) + 1
            choices = list(values['wrong'])
            choices.insert(correct_position - 1, values['correct'])
            for position, text in enumerate(choices, start=1):
                AnswerChoice.objects.create(
                    question=question,
                    text=text,
                    position=position,
                    is_correct=position == correct_position,
                )

            question.is_active = True
            question.save()
            created += int(was_created)
            updated += int(not was_created)

        self.stdout.write(self.style.SUCCESS(
            f'Seeded {len(topics)} topics and {len(QUESTIONS)} questions '
            f'({created} created, {updated} updated).'
        ))
