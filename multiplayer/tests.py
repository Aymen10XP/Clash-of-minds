import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from quiz.models import AnswerChoice, Question, Topic

from .models import KnowledgeMatch, MatchInvitation, MatchParticipant, MatchRound


class MultiplayerApiTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.alice = user_model.objects.create_user(
            username='alice',
            email='alice@example.com',
            password='test-password-47',
            country='TN',
        )
        self.bob = user_model.objects.create_user(
            username='bob',
            email='bob@example.com',
            password='test-password-47',
            country='US',
        )
        self.charlie = user_model.objects.create_user(
            username='charlie',
            email='charlie@example.com',
            password='test-password-47',
            country='FR',
        )
        self.topic = Topic.objects.create(slug='duel-test', title='Duel Test')
        self.question = Question.objects.create(
            topic=self.topic,
            prompt='Which answer wins this test round?',
            difficulty=Question.Difficulty.EASY,
        )
        for position, text in enumerate(('Correct', 'Wrong A', 'Wrong B', 'Wrong C'), start=1):
            AnswerChoice.objects.create(
                question=self.question,
                text=text,
                position=position,
                is_correct=position == 1,
            )
        self.question.is_active = True
        self.question.save()

    def post_json(self, path, data=None):
        return self.client.post(
            path,
            data=json.dumps(data or {}),
            content_type='application/json',
        )

    def test_player_search_requires_authentication_and_excludes_current_user(self):
        anonymous = self.client.get('/api/multiplayer/players/?q=bo')
        self.assertEqual(anonymous.status_code, 401)

        self.client.force_login(self.alice)
        response = self.client.get('/api/multiplayer/players/?q=bo')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['players'], [{
            'id': self.bob.pk,
            'username': 'bob',
            'country': 'US',
        }])

    def test_invitation_acceptance_creates_one_match_with_two_participants(self):
        self.client.force_login(self.alice)
        sent = self.post_json('/api/multiplayer/invitations/send/', {'recipientId': self.bob.pk})
        self.assertEqual(sent.status_code, 201)
        invitation_id = sent.json()['invitation']['id']

        self.client.force_login(self.bob)
        accepted = self.post_json(
            f'/api/multiplayer/invitations/{invitation_id}/respond/',
            {'action': 'accept'},
        )

        self.assertEqual(accepted.status_code, 200)
        self.assertEqual(accepted.json()['match']['status'], KnowledgeMatch.Status.WAITING)
        self.assertEqual(KnowledgeMatch.objects.count(), 1)
        self.assertEqual(MatchParticipant.objects.count(), 2)
        self.assertSetEqual(
            set(MatchParticipant.objects.values_list('player_id', flat=True)),
            {self.alice.pk, self.bob.pk},
        )

    def test_reverse_pending_invitation_is_rejected(self):
        MatchInvitation.objects.create(sender=self.alice, recipient=self.bob)
        self.client.force_login(self.bob)

        response = self.post_json(
            '/api/multiplayer/invitations/send/',
            {'recipientId': self.alice.pk},
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(MatchInvitation.objects.count(), 1)

    def test_only_recipient_can_accept_invitation(self):
        invitation = MatchInvitation.objects.create(sender=self.alice, recipient=self.bob)
        self.client.force_login(self.charlie)

        response = self.post_json(
            f'/api/multiplayer/invitations/{invitation.pk}/respond/',
            {'action': 'accept'},
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(KnowledgeMatch.objects.exists())

    def test_match_starts_when_both_players_are_ready(self):
        invitation = MatchInvitation.objects.create(
            sender=self.alice,
            recipient=self.bob,
            status=MatchInvitation.Status.ACCEPTED,
        )
        match = KnowledgeMatch.objects.create(invitation=invitation)
        MatchParticipant.objects.create(
            match=match,
            player=self.alice,
            seat=MatchParticipant.Seat.HOST,
        )
        MatchParticipant.objects.create(
            match=match,
            player=self.bob,
            seat=MatchParticipant.Seat.GUEST,
        )

        self.client.force_login(self.alice)
        first = self.post_json(f'/api/multiplayer/matches/{match.pk}/ready/')
        self.assertEqual(first.json()['match']['status'], KnowledgeMatch.Status.WAITING)

        self.client.force_login(self.bob)
        second = self.post_json(f'/api/multiplayer/matches/{match.pk}/ready/')

        self.assertEqual(second.status_code, 200)
        self.assertEqual(second.json()['match']['status'], KnowledgeMatch.Status.ACTIVE)
        match.refresh_from_db()
        self.assertIsNotNone(match.started_at)
        self.assertEqual(match.rounds.filter(status=MatchRound.Status.ACTIVE).count(), 1)

    def test_nonparticipant_cannot_open_or_ready_match(self):
        invitation = MatchInvitation.objects.create(
            sender=self.alice,
            recipient=self.bob,
            status=MatchInvitation.Status.ACCEPTED,
        )
        match = KnowledgeMatch.objects.create(invitation=invitation)
        MatchParticipant.objects.create(match=match, player=self.alice, seat='host')
        MatchParticipant.objects.create(match=match, player=self.bob, seat='guest')
        self.client.force_login(self.charlie)

        detail = self.client.get(f'/api/multiplayer/matches/{match.pk}/')
        ready = self.post_json(f'/api/multiplayer/matches/{match.pk}/ready/')

        self.assertEqual(detail.status_code, 404)
        self.assertEqual(ready.status_code, 404)

    def create_active_match(self):
        invitation = MatchInvitation.objects.create(
            sender=self.alice,
            recipient=self.bob,
            status=MatchInvitation.Status.ACCEPTED,
        )
        match = KnowledgeMatch.objects.create(
            invitation=invitation,
            status=KnowledgeMatch.Status.ACTIVE,
            started_at=timezone.now(),
        )
        MatchParticipant.objects.create(match=match, player=self.alice, seat='host', is_ready=True)
        MatchParticipant.objects.create(match=match, player=self.bob, seat='guest', is_ready=True)
        MatchRound.objects.create(match=match, question=self.question, sequence=1)
        return match

    def test_players_receive_same_question_with_different_choice_order(self):
        match = self.create_active_match()
        self.client.force_login(self.alice)
        alice_round = self.client.get(f'/api/multiplayer/matches/{match.pk}/').json()['match']['currentRound']
        self.client.force_login(self.bob)
        bob_round = self.client.get(f'/api/multiplayer/matches/{match.pk}/').json()['match']['currentRound']

        self.assertEqual(alice_round['question']['id'], bob_round['question']['id'])
        alice_choices = [choice['id'] for choice in alice_round['question']['choices']]
        bob_choices = [choice['id'] for choice in bob_round['question']['choices']]
        self.assertSetEqual(set(alice_choices), set(bob_choices))
        self.assertNotEqual(alice_choices, bob_choices)

    def test_first_correct_answer_removes_opponent_heart(self):
        match = self.create_active_match()
        correct_choice = self.question.choices.get(is_correct=True)
        self.client.force_login(self.alice)

        response = self.post_json(
            f'/api/multiplayer/matches/{match.pk}/answer/',
            {'questionId': self.question.pk, 'choiceId': correct_choice.pk},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()['match']
        bob = next(player for player in payload['participants'] if player['id'] == self.bob.pk)
        self.assertEqual(bob['hearts'], 2)
        self.assertEqual(payload['currentRound']['sequence'], 2)

    def test_match_ends_when_a_player_loses_all_hearts(self):
        match = self.create_active_match()
        self.client.force_login(self.alice)

        payload = None
        for _ in range(3):
            active_round = MatchRound.objects.get(match=match, status=MatchRound.Status.ACTIVE)
            correct_choice = active_round.question.choices.get(is_correct=True)
            response = self.post_json(
                f'/api/multiplayer/matches/{match.pk}/answer/',
                {'questionId': active_round.question_id, 'choiceId': correct_choice.pk},
            )
            payload = response.json()['match']

        self.assertEqual(payload['status'], KnowledgeMatch.Status.COMPLETED)
        self.assertEqual(payload['winnerId'], self.alice.pk)
        self.assertEqual(payload['endReason'], KnowledgeMatch.EndReason.HEARTS)
        bob = next(player for player in payload['participants'] if player['id'] == self.bob.pk)
        self.assertEqual(bob['hearts'], 0)

    def test_two_wrong_answers_advance_without_heart_loss(self):
        match = self.create_active_match()
        wrong_choices = list(self.question.choices.filter(is_correct=False)[:2])
        self.client.force_login(self.alice)
        first = self.post_json(
            f'/api/multiplayer/matches/{match.pk}/answer/',
            {'questionId': self.question.pk, 'choiceId': wrong_choices[0].pk},
        )
        self.assertTrue(first.json()['match']['currentRound']['hasAnswered'])

        self.client.force_login(self.bob)
        second = self.post_json(
            f'/api/multiplayer/matches/{match.pk}/answer/',
            {'questionId': self.question.pk, 'choiceId': wrong_choices[1].pk},
        )

        payload = second.json()['match']
        self.assertEqual(payload['currentRound']['sequence'], 2)
        self.assertTrue(all(player['hearts'] == 3 for player in payload['participants']))

    def test_expired_timer_uses_remaining_hearts_to_choose_winner(self):
        match = self.create_active_match()
        match.started_at = timezone.now() - timedelta(minutes=6)
        match.save(update_fields=('started_at',))
        MatchParticipant.objects.filter(match=match, player=self.bob).update(hearts=2)
        self.client.force_login(self.bob)

        response = self.client.get(f'/api/multiplayer/matches/{match.pk}/')

        payload = response.json()['match']
        self.assertEqual(payload['status'], KnowledgeMatch.Status.COMPLETED)
        self.assertEqual(payload['winnerId'], self.alice.pk)
        self.assertEqual(payload['endReason'], KnowledgeMatch.EndReason.TIME)

    def test_expired_timer_is_draw_when_hearts_are_equal(self):
        match = self.create_active_match()
        match.started_at = timezone.now() - timedelta(minutes=6)
        match.save(update_fields=('started_at',))
        self.client.force_login(self.alice)

        payload = self.client.get(f'/api/multiplayer/matches/{match.pk}/').json()['match']

        self.assertEqual(payload['status'], KnowledgeMatch.Status.COMPLETED)
        self.assertIsNone(payload['winnerId'])
