"""Train and chronologically evaluate the optional adaptive question network."""

import math
import os
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from quiz.adaptive_features import FEATURE_VERSION, history_probability
from quiz.adaptive_training import build_training_rows


class Command(BaseCommand):
    help = 'Train a small PyTorch question-success model from real gameplay history.'

    def add_arguments(self, parser):
        parser.add_argument('--output', help='Checkpoint output path.')
        parser.add_argument('--min-responses', type=int, default=200)
        parser.add_argument('--min-players', type=int, default=8)
        parser.add_argument('--epochs', type=int, default=100)
        parser.add_argument(
            '--include-synthetic',
            action='store_true',
            help='Train on explicitly labeled synthetic responses for experimentation only.',
        )

    def handle(self, *args, **options):
        try:
            import torch
            from quiz.adaptive_network import AdaptiveQuestionNetwork
        except ImportError as error:
            raise CommandError(
                'PyTorch is optional. Install requirements-ml.txt before training.'
            ) from error

        topic_slugs, topic_ids, features, labels, player_ids = build_training_rows(
            include_synthetic=options['include_synthetic'],
        )
        if len(features) < options['min_responses']:
            raise CommandError(
                f'Only {len(features)} eligible real responses are available; '
                f'{options["min_responses"]} are required. No synthetic data was added.'
            )

        split = int(len(features) * 0.8)
        if split == 0 or split == len(features):
            raise CommandError('History must contain both training and validation responses.')
        train_players = set(player_ids[:split])
        if len(train_players) < options['min_players']:
            raise CommandError(
                f'Only {len(train_players)} players are represented in the chronological '
                f'training period; {options["min_players"]} are required.'
            )
        if len(set(labels[:split])) < 2:
            raise CommandError('Training history needs both correct and incorrect responses.')

        torch.manual_seed(42)
        train_topics = torch.tensor(topic_ids[:split], dtype=torch.long)
        train_features = torch.tensor(features[:split], dtype=torch.float32)
        train_labels = torch.tensor(labels[:split], dtype=torch.float32)
        validation_topics = torch.tensor(topic_ids[split:], dtype=torch.long)
        validation_features = torch.tensor(features[split:], dtype=torch.float32)
        validation_labels = torch.tensor(labels[split:], dtype=torch.float32)

        model = AdaptiveQuestionNetwork(topic_count=len(topic_slugs) + 1)
        optimizer = torch.optim.Adam(model.parameters(), lr=0.01, weight_decay=0.001)
        loss_function = torch.nn.BCEWithLogitsLoss()
        best_brier = math.inf
        best_state = None
        best_metrics = None
        stale_epochs = 0

        for _ in range(max(1, options['epochs'])):
            model.train()
            optimizer.zero_grad()
            logits = model(train_topics, train_features)
            loss = loss_function(logits, train_labels)
            loss.backward()
            optimizer.step()

            model.eval()
            with torch.inference_mode():
                predicted = torch.sigmoid(model(validation_topics, validation_features))
                brier = torch.mean((predicted - validation_labels) ** 2).item()
            if brier < best_brier:
                best_brier = brier
                best_state = {
                    key: value.detach().cpu().clone()
                    for key, value in model.state_dict().items()
                }
                best_metrics = self._metrics(predicted.tolist(), labels[split:])
                stale_epochs = 0
            else:
                stale_epochs += 1
                if stale_epochs >= 12:
                    break

        model.load_state_dict(best_state)
        output = Path(
            options['output']
            or os.environ.get('ADAPTIVE_MODEL_PATH')
            or Path(settings.BASE_DIR) / 'var' / (
                'adaptive_question_model_experimental.pt'
                if options['include_synthetic']
                else 'adaptive_question_model.pt'
            )
        )
        output.parent.mkdir(parents=True, exist_ok=True)
        checkpoint = {
            'feature_version': FEATURE_VERSION,
            'experimental': options['include_synthetic'],
            'topic_slugs': topic_slugs,
            'state_dict': best_state,
            'training_examples': split,
            'validation_examples': len(features) - split,
            'metrics': best_metrics,
        }
        torch.save(checkpoint, output)

        history_predictions = [history_probability(row) for row in features[split:]]
        history_metrics = self._metrics(history_predictions, labels[split:])
        self.stdout.write(self.style.SUCCESS('Adaptive model trained and saved.'))
        if options['include_synthetic']:
            self.stdout.write(self.style.WARNING(
                'This checkpoint was trained on generated responses. It is for '
                'experimentation only and is blocked from normal model loading by default.'
            ))
        self.stdout.write(f'Training responses: {len(features)}')
        if options['include_synthetic']:
            self.stdout.write('Training data: generated synthetic experiment only')
        else:
            self.stdout.write('Training data: recorded real gameplay only')
        self.stdout.write(f'Chronological training / validation: {split} / {len(features) - split}')
        self.stdout.write(f'Players in training period: {len(train_players)}')
        self.stdout.write(f'Checkpoint: {output}')
        self.stdout.write('Validation: ' + self._format_metrics(best_metrics))
        self.stdout.write('History baseline: ' + self._format_metrics(history_metrics))
        self.stdout.write(
            'Treat this comparison as experimental; a small or non-representative '
            'history cannot establish generalization.'
        )

    @staticmethod
    def _metrics(predictions, actual):
        count = max(len(actual), 1)
        brier = sum((prediction - truth) ** 2 for prediction, truth in zip(predictions, actual)) / count
        threshold_accuracy = sum(
            int((prediction >= 0.5) == bool(truth))
            for prediction, truth in zip(predictions, actual)
        ) / count
        return {
            'brier_score': brier,
            'threshold_accuracy': threshold_accuracy,
            'mean_predicted_accuracy': sum(predictions) / count,
            'actual_accuracy': sum(actual) / count,
            'examples': len(actual),
        }

    @staticmethod
    def _format_metrics(metrics):
        return (
            f"n={metrics['examples']}, Brier={metrics['brier_score']:.4f}, "
            f"threshold accuracy={metrics['threshold_accuracy']:.3f}, "
            f"mean predicted={metrics['mean_predicted_accuracy']:.3f}, "
            f"actual={metrics['actual_accuracy']:.3f}"
        )
