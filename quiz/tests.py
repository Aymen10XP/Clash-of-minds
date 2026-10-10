from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from accounts.models import User

from .models import AnswerChoice, Question, Topic, TopScoreResponse, TopScoreRun


class QuizModelTests(TestCase):
    def setUp(self):
        self.topic = Topic.objects.create(
            slug='ancient-civilizations',
            title='Ancient Civilizations',
        )
        self.question = Question.objects.create(
            topic=self.topic,
            prompt='Which river was central to ancient Egyptian civilization?',
            difficulty=Question.Difficulty.EASY,
        )

    def add_four_choices(self):
        choices = []
        for position, text in enumerate(('Nile', 'Tigris', 'Indus', 'Danube'), start=1):
            choices.append(AnswerChoice.objects.create(
                question=self.question,
                text=text,
                position=position,
                is_correct=position == 1,
            ))
        return choices

    def test_question_requires_a_topic_category(self):
        question = Question(
            prompt='This question must belong to a category.',
            difficulty=Question.Difficulty.MEDIUM,
        )

        with self.assertRaises(ValidationError) as error:
            question.save()

        self.assertIn('topic', error.exception.message_dict)

    def test_question_requires_four_choices_before_activation(self):
        self.question.is_active = True

        with self.assertRaises(ValidationError):
            self.question.save()

    def test_question_with_four_choices_and_one_correct_answer_can_activate(self):
        choices = self.add_four_choices()
        self.question.is_active = True
        self.question.save()

        self.assertTrue(self.question.is_active)
        self.assertEqual(len(choices), 4)
        self.assertEqual(self.question.choices.filter(is_correct=True).count(), 1)

    def test_question_rejects_a_fifth_choice(self):
        self.add_four_choices()

        with self.assertRaises(ValidationError):
            AnswerChoice.objects.create(
                question=self.question,
                text='Amazon',
                position=4,
            )

    def test_question_rejects_a_second_correct_choice(self):
        AnswerChoice.objects.create(
            question=self.question,
            text='Nile',
            position=1,
            is_correct=True,
        )

        with self.assertRaises(ValidationError):
            AnswerChoice.objects.create(
                question=self.question,
                text='Tigris',
                position=2,
                is_correct=True,
            )


class TopScoreModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='player',
            email='player@example.com',
            password='secure-test-password',
            country='TN',
        )
        self.topic = Topic.objects.create(slug='inventions', title='Inventions')
        self.question = Question.objects.create(
            topic=self.topic,
            prompt='Who is associated with the practical incandescent light bulb?',
        )
        self.correct_choice = AnswerChoice.objects.create(
            question=self.question,
            text='Thomas Edison',
            position=1,
            is_correct=True,
        )
        self.wrong_choice = AnswerChoice.objects.create(
            question=self.question,
            text='Isaac Newton',
            position=2,
        )
        AnswerChoice.objects.create(question=self.question, text='Ada Lovelace', position=3)
        AnswerChoice.objects.create(question=self.question, text='Louis Pasteur', position=4)
        self.question.is_active = True
        self.question.save()
        self.run = TopScoreRun.objects.create(user=self.user)

    def test_response_derives_correctness_from_selected_choice(self):
        response = TopScoreResponse.objects.create(
            run=self.run,
            question=self.question,
            selected_choice=self.correct_choice,
            sequence=1,
            response_time_ms=2_500,
        )

        self.assertTrue(response.is_correct)

    def test_response_rejects_choice_from_another_question(self):
        other_question = Question.objects.create(
            topic=self.topic,
            prompt='Which invention enabled long-distance voice communication?',
        )
        other_choice = AnswerChoice.objects.create(
            question=other_question,
            text='Telephone',
            position=1,
            is_correct=True,
        )

        with self.assertRaises(ValidationError):
            TopScoreResponse.objects.create(
                run=self.run,
                question=self.question,
                selected_choice=other_choice,
                sequence=1,
                response_time_ms=1_000,
            )

    def test_timeout_response_has_no_choice_and_is_incorrect(self):
        response = TopScoreResponse.objects.create(
            run=self.run,
            question=self.question,
            selected_choice=None,
            sequence=1,
            response_time_ms=10_000,
        )

        self.assertFalse(response.is_correct)

    def test_completed_run_requires_end_metadata(self):
        self.run.status = TopScoreRun.Status.FINISHED

        with self.assertRaises(ValidationError):
            self.run.save()

        self.run.end_reason = TopScoreRun.EndReason.WRONG_ANSWER
        self.run.ended_at = timezone.now()
        self.run.score = 7
        self.run.save()

        self.assertEqual(self.run.score, 7)


class SeedQuizCommandTests(TestCase):
    def test_seed_command_is_complete_and_idempotent(self):
        call_command('seed_quiz', verbosity=0)
        call_command('seed_quiz', verbosity=0)

        self.assertEqual(Topic.objects.count(), 6)
        self.assertEqual(Question.objects.count(), 30)
        self.assertEqual(Question.objects.filter(is_active=True).count(), 30)

        for question in Question.objects.prefetch_related('choices'):
            self.assertEqual(question.choices.count(), 4)
            self.assertEqual(question.choices.filter(is_correct=True).count(), 1)
import json



class TopScoreApiTests(TestCase):
    def setUp(self):
        call_command('seed_quiz', verbosity=0)
        self.user = User.objects.create_user(
            username='api-player',
            email='api-player@example.com',
            password='secure-test-password',
            country='TN',
        )

    def post_json(self, path, data=None):
        return self.client.post(
            path,
            data=json.dumps(data or {}),
            content_type='application/json',
        )

    def start_run(self):
        self.client.force_login(self.user)
        response = self.post_json('/api/quiz/top-score/start/')
        self.assertEqual(response.status_code, 201)
        return response.json()

    def test_start_requires_authentication(self):
        response = self.post_json('/api/quiz/top-score/start/')

        self.assertEqual(response.status_code, 401)

    def test_start_returns_four_choices_without_revealing_correctness(self):
        payload = self.start_run()

        self.assertEqual(len(payload['question']['choices']), 4)
        self.assertNotIn('isCorrect', payload['question']['choices'][0])
        self.assertEqual(payload['timeLimitMs'], 10_000)

    def test_correct_answer_increments_score_and_returns_next_question(self):
        payload = self.start_run()
        question = Question.objects.get(pk=payload['question']['id'])
        correct_choice = question.choices.get(is_correct=True)

        response = self.post_json(
            f"/api/quiz/top-score/{payload['runId']}/answer/",
            {'questionId': question.pk, 'choiceId': correct_choice.pk},
        )

        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertTrue(result['correct'])
        self.assertFalse(result['gameOver'])
        self.assertEqual(result['score'], 1)
        self.assertNotEqual(result['question']['id'], question.pk)

    def test_wrong_answer_ends_run(self):
        payload = self.start_run()
        question = Question.objects.get(pk=payload['question']['id'])
        wrong_choice = question.choices.filter(is_correct=False).first()

        response = self.post_json(
            f"/api/quiz/top-score/{payload['runId']}/answer/",
            {'questionId': question.pk, 'choiceId': wrong_choice.pk},
        )

        result = response.json()
        self.assertFalse(result['correct'])
        self.assertTrue(result['gameOver'])
        self.assertEqual(result['endReason'], TopScoreRun.EndReason.WRONG_ANSWER)
        self.assertEqual(
            TopScoreRun.objects.get(client_run_id=payload['runId']).status,
            TopScoreRun.Status.FINISHED,
        )

    def test_empty_choice_records_timeout(self):
        payload = self.start_run()

        response = self.post_json(
            f"/api/quiz/top-score/{payload['runId']}/answer/",
            {'questionId': payload['question']['id'], 'choiceId': None},
        )

        self.assertTrue(response.json()['timedOut'])
        self.assertLessEqual(TopScoreResponse.objects.get().response_time_ms, 10_000)
