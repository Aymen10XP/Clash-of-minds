import json

from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import KnowledgeMatch, MatchInvitation, MatchParticipant


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
