#!/usr/bin/env python3
"""
compare_responses.py

Compares VLM responses against ground-truth labels.

Metrics
-------
- Per-field accuracy: exact match for scalar/categorical fields, Jaccard-F1
  for list-valued fields (order-insensitive set overlap).
- Macro-averaged overall accuracy across all 21 leaf fields.
- Corpus BLEU-1 through BLEU-4 computed on flattened "field=value" token
  sequences, treating each JSON as a token bag the way BLEU treats sentences.

Usage
-----
    python compare_responses.py [--labels DIR] [--responses DIR]

Defaults: ../labels and ../responses relative to this script.
"""

import argparse
import json
import math
import os
from collections import Counter


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_LABELS_DIR = os.path.join(SCRIPT_DIR, '..', 'labels')
DEFAULT_RESPONSES_DIR = os.path.join(SCRIPT_DIR, '..', 'responses')

# Paths into the nested JSON for each leaf field (tuple = key chain)
SCALAR_FIELDS = [
    ('Scene',),
    ('TimeOfDay',),
    ('Weather',),
    ('RoadConditions',),
    ('LaneInformation', 'NumberOfLanes'),
    ('LaneInformation', 'LaneMarkings'),
    ('TrafficSigns', 'TrafficSignsVisibility'),
    ('Vehicles', 'TotalNumber'),
    ('Directionality',),
    ('Visibility', 'General'),
    ('Ego-Vehicle', 'Direction'),
    ('Ego-Vehicle', 'Maneuver'),
    ('CameraCondition',),
    ('Severity',),
]

LIST_FIELDS = [
    ('LaneInformation', 'SpecialLanes'),
    ('TrafficSigns', 'TrafficSignsTypes'),
    ('Vehicles', 'VehicleTypes'),
    ('Vehicles', 'InMotion'),
    ('Vehicles', 'States'),
    ('Pedestrians',),
    ('Visibility', 'SpecificImpairments'),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_nested(d, path):
    for key in path:
        if not isinstance(d, dict) or key not in d:
            return None
        d = d[key]
    return d


def jaccard_f1(pred, ref):
    """Set-based F1 between two lists (treats duplicates as a single item)."""
    p, r = set(pred or []), set(ref or [])
    if not p and not r:
        return 1.0
    tp = len(p & r)
    precision = tp / len(p) if p else 0.0
    recall = tp / len(r) if r else 0.0
    denom = precision + recall
    return 2 * precision * recall / denom if denom else 0.0


def flatten_tokens(obj, prefix=''):
    """Flatten a JSON object into 'fieldpath=value' string tokens."""
    tokens = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            tokens.extend(flatten_tokens(v, prefix=f'{prefix}{k}.'))
    elif isinstance(obj, list):
        for item in obj:
            tokens.extend(flatten_tokens(item, prefix=prefix))
    else:
        tokens.append(f'{prefix.rstrip(".")}={obj}')
    return tokens


def ngram_counts(tokens, n):
    return Counter(tuple(tokens[i:i + n]) for i in range(max(0, len(tokens) - n + 1)))


def corpus_bleu(responses, labels, max_n=4):
    """
    Corpus BLEU on flattened token sequences.

    Each JSON is converted to an ordered list of 'field=value' tokens.
    n-gram precision is computed with clipping (standard BLEU), and the
    brevity penalty is applied over the whole corpus.
    """
    clipped = [Counter() for _ in range(max_n)]
    total_pred = [0] * max_n
    total_pred_len = 0
    total_ref_len = 0

    for resp, label in zip(responses, labels):
        pred_tok = flatten_tokens(resp)
        ref_tok = flatten_tokens(label)
        total_pred_len += len(pred_tok)
        total_ref_len += len(ref_tok)

        for n in range(1, max_n + 1):
            pc = ngram_counts(pred_tok, n)
            rc = ngram_counts(ref_tok, n)
            for ngram, cnt in pc.items():
                clipped[n - 1][ngram] += min(cnt, rc.get(ngram, 0))
            total_pred_len += 0  # already counted above
            total_pred[n - 1] += sum(pc.values())

    bp = (1.0 if total_pred_len >= total_ref_len
          else math.exp(1 - total_ref_len / total_pred_len))

    precisions = []
    scores = {}
    for n in range(1, max_n + 1):
        denom = total_pred[n - 1]
        p = sum(clipped[n - 1].values()) / denom if denom else 0.0
        precisions.append(p)
        scores[f'BLEU-{n}'] = bp * p

    if all(p > 0 for p in precisions):
        scores['BLEU'] = bp * math.exp(sum(math.log(p) for p in precisions) / max_n)
    else:
        scores['BLEU'] = 0.0

    return scores, precisions, bp


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description='Compare VLM responses to ground-truth labels.')
    parser.add_argument('--labels', default=DEFAULT_LABELS_DIR)
    parser.add_argument('--responses', default=DEFAULT_RESPONSES_DIR)
    args = parser.parse_args()

    label_files = sorted(
        [f for f in os.listdir(args.labels) if f.endswith('.json')]
    )
    resp_files = sorted(
        [f for f in os.listdir(args.responses) if f.endswith('.json')],
        key=lambda x: int(x.split('_')[-1].split('.')[0])
    )

    n = min(len(label_files), len(resp_files))
    print(f'Pairs evaluated : {n}  '
          f'(responses: {len(resp_files)}, labels: {len(label_files)})')
    print()

    labels, responses = [], []
    skipped = 0
    for i in range(n):
        with open(os.path.join(args.responses, resp_files[i]), encoding='utf-8') as f:
            raw = json.load(f)
        try:
            parsed = json.loads(raw) if isinstance(raw, str) else raw
            if not parsed:
                raise ValueError('empty')
        except (json.JSONDecodeError, ValueError):
            skipped += 1
            continue
        with open(os.path.join(args.labels, label_files[i]), encoding='utf-8') as f:
            labels.append(json.load(f))
        responses.append(parsed)

    if skipped:
        print(f'Skipped {skipped} malformed/empty response(s).')
        print()

    # --- Per-field scores ---
    scalar_scores: dict[str, list[float]] = {'.'.join(p): [] for p in SCALAR_FIELDS}
    list_scores: dict[str, list[float]] = {'.'.join(p): [] for p in LIST_FIELDS}

    for resp, label in zip(responses, labels):
        for path in SCALAR_FIELDS:
            key = '.'.join(path)
            scalar_scores[key].append(
                1.0 if get_nested(resp, path) == get_nested(label, path) else 0.0
            )
        for path in LIST_FIELDS:
            key = '.'.join(path)
            scalar_scores_key = '.'.join(path)
            list_scores['.'.join(path)].append(
                jaccard_f1(get_nested(resp, path), get_nested(label, path))
            )

    # --- Print table ---
    COL = 46
    header = f"{'Field':<{COL}} {'Score':>8}  {'Metric'}"
    print(header)
    print('-' * len(header))

    all_avgs = []
    for field_dict, metric in [(scalar_scores, 'exact-match'), (list_scores, 'Jaccard-F1')]:
        for key, scores in field_dict.items():
            avg = sum(scores) / len(scores)
            all_avgs.append(avg)
            print(f'{key:<{COL}} {avg:>8.4f}  {metric}')

    print('-' * len(header))
    overall = sum(all_avgs) / len(all_avgs)
    print(f"{'Overall macro-average':<{COL}} {overall:>8.4f}")
    print()

    # --- BLEU ---
    bleu_scores, precisions, bp = corpus_bleu(responses, labels)
    print('Corpus BLEU  (flattened field=value token sequences)')
    print(f'  Brevity penalty : {bp:.4f}')
    for i, p in enumerate(precisions, 1):
        print(f'  BLEU-{i} precision: {p:.4f}')
    print()
    for name, score in bleu_scores.items():
        marker = '  <<<' if name == 'BLEU' else ''
        print(f'  {name:<8}: {score:.4f}{marker}')


if __name__ == '__main__':
    main()
