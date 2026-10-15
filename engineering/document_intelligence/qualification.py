"""Exact per-object comparisons; never a renderer or engineering approval issuer.

A manifest declares independently prepared reference expectations. Matching bytes
prove only that named payloads match those expectations, not that the reference,
physical layout, interpretation, or source scope is complete or correct.
"""
import hashlib
import json
import re

MAX_OBJECTS = 50000
IDENTITIES = {'source_sha256', 'reference_sha256', 'parser_sha256'}
OBJECT_FIELDS = {'object_id', 'kind', 'source_locator', 'reference_locator',
                 'payload_sha256', 'critical_numeric'}
KINDS = {'paragraph', 'table_cell', 'formula', 'image', 'embedded_object'}


def _hash(value):
    if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{64}', value):
        raise ValueError('INVALID_QUALIFICATION_HASH')


def _object(value, *, observation=False):
    expected = OBJECT_FIELDS | IDENTITIES if observation else OBJECT_FIELDS
    if not isinstance(value, dict) or set(value) != expected:
        raise ValueError('INVALID_QUALIFICATION_OBJECT')
    for key, limit in [('object_id', 200), ('source_locator', 2000), ('reference_locator', 2000)]:
        text = value[key]
        if (not isinstance(text, str) or not text.strip() or len(text) > limit
                or any(ord(char) < 32 for char in text)):
            raise ValueError('INVALID_QUALIFICATION_LOCATOR')
    if not isinstance(value['kind'],str) or value['kind'] not in KINDS or type(value['critical_numeric']) is not bool:
        raise ValueError('INVALID_QUALIFICATION_OBJECT_TYPE')
    _hash(value['payload_sha256'])
    if observation:
        for key in IDENTITIES:
            _hash(value[key])


def qualify_document(manifest, observations):
    """Compare source-bound reference payload digests with declared observations.

    Callers must separately verify the source files and acquire trustworthy
    reference/review records. No caller-supplied PASS or acceptance flag is read.
    Missing, stale, different, repeated or foreign observations cannot close gaps.
    """
    if (not isinstance(manifest, dict) or set(manifest) != IDENTITIES | {'schema', 'objects'}
            or type(manifest['schema']) is not int or manifest['schema'] != 1):
        raise ValueError('INVALID_QUALIFICATION_MANIFEST')
    for key in IDENTITIES:
        _hash(manifest[key])
    expected = manifest['objects']
    if (not isinstance(expected, list) or not 1 <= len(expected) <= MAX_OBJECTS
            or not isinstance(observations, list) or len(observations) > MAX_OBJECTS):
        raise ValueError('QUALIFICATION_OBJECT_COUNT_LIMIT')
    targets = {}
    for item in expected:
        _object(item)
        identity = item['object_id']
        if identity in targets:
            raise ValueError('DUPLICATE_QUALIFICATION_OBJECT')
        targets[identity] = item
    actual = {}
    for item in observations:
        _object(item, observation=True)
        identity = item['object_id']
        if identity not in targets or identity in actual:
            raise ValueError('DUPLICATE_OR_FOREIGN_QUALIFICATION_OBSERVATION')
        actual[identity] = item
    records, missing, mismatches, numeric = [], [], [], []
    for identity in sorted(targets):
        target = targets[identity]
        observed = actual.get(identity)
        reasons = []
        if observed is None:
            missing.append(identity)
            reasons.append('OBSERVATION_MISSING')
        else:
            if any(observed[key] != manifest[key] for key in IDENTITIES):
                reasons.append('IDENTITY_MISMATCH')
            for key in sorted(OBJECT_FIELDS - {'object_id'}):
                if observed[key] != target[key]:
                    reasons.append(key.upper() + '_MISMATCH')
            if reasons:
                mismatches.append(identity)
                if target['critical_numeric']:
                    numeric.append(identity)
        records.append(dict(object_id=identity, kind=target['kind'],
                            source_locator=target['source_locator'],
                            reference_locator=target['reference_locator'],
                            status='MISSING' if observed is None else 'MISMATCH' if reasons else 'MATCHED',
                            reasons=reasons))
    matched = not missing and not mismatches
    body = json.dumps(manifest, sort_keys=True, ensure_ascii=False, separators=(',', ':')).encode()
    return dict(schema='ENGINEER_OS_DOCUMENT_REFERENCE_COMPARISON_V1',
                **{key: manifest[key] for key in sorted(IDENTITIES)},
                manifest_sha256=hashlib.sha256(body).hexdigest(),
                status='READY_FOR_INDEPENDENT_REVIEW' if matched else 'BLOCK',
                comparison_status='PASS' if matched else 'BLOCK',
                scope='EXACT_REFERENCE_PAYLOAD_COMPARISON_ONLY',
                expected_objects=len(expected), matched_objects=len(expected)-len(missing)-len(mismatches),
                unaccounted_objects=missing, mismatched_objects=mismatches,
                critical_numeric_mismatches=numeric, objects=records,
                document_completeness='NOT_QUALIFIED', qualified_scope=[],
                reference_authority_verified=False, visual_semantics_verified=False,
                acceptance_granted=False, engineering_verified=False)
