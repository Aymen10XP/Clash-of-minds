"""Compare recorded adaptive runs with the randomized selection control."""

from collections import defaultdict

from django.core.management.base import BaseCommand
from django.db.models import Count, Q

from quiz.models import TopScoreRun


class Command(BaseCommand):
    help = 'Report accuracy and completion by recorded question-selection mode.'

    def add_arguments(self, parser):
        parser.add_argument('--minimum-runs', type=int, default=30)

    def handle(self, *args, **options):
        modes = (
            TopScoreRun.SelectionMode.RANDOM_CONTROL,
            TopScoreRun.SelectionMode.HISTORY,
            TopScoreRun.SelectionMode.NEURAL,
            TopScoreRun.SelectionMode.SYNTHETIC,
        )
        rows = TopScoreRun.objects.filter(selection_mode__in=modes).annotate(
            response_count=Count('responses', distinct=True),
            correct_count=Count(
                'responses',
                filter=Q(responses__is_correct=True),
                distinct=True,
            ),
        ).values(
            'selection_mode', 'status', 'response_count', 'correct_count',
        )
        groups = defaultdict(list)
        for row in rows:
            groups[row['selection_mode']].append(row)

        for mode in modes:
            runs = groups[mode]
            total_runs = len(runs)
            completed = sum(row['status'] == TopScoreRun.Status.FINISHED for row in runs)
            responses = sum(row['response_count'] for row in runs)
            correct = sum(row['correct_count'] for row in runs)
            run_accuracies = [
                row['correct_count'] / row['response_count']
                for row in runs if row['response_count']
            ]
            mean_run_accuracy = (
                sum(run_accuracies) / len(run_accuracies) if run_accuracies else 0.0
            )
            response_accuracy = correct / responses if responses else 0.0
            completion_rate = completed / total_runs if total_runs else 0.0
            if mode == TopScoreRun.SelectionMode.SYNTHETIC:
                sample = 'synthetic-only descriptive results; not real-world evidence'
            else:
                sample = (
                    'sufficient for a cautious comparison'
                    if total_runs >= options['minimum_runs']
                    else 'too small to interpret'
                )
            self.stdout.write(
                f'{mode}: runs={total_runs}, responses={responses}, '
                f'mean_run_accuracy={mean_run_accuracy:.3f}, '
                f'response_accuracy={response_accuracy:.3f}, '
                f'completion_rate={completion_rate:.3f}; {sample}'
            )

        self.stdout.write(
            'Compare adaptive groups with random_control only after each reaches '
            f"{options['minimum_runs']} runs. This observational summary is not a causal claim."
        )
        self.stdout.write(
            'synthetic is generated demonstration data; do not compare it with real-player '
            'groups or report it as observed player performance.'
        )
