"""Capability handling for test fixtures only; production errors are never caught."""
import os
import unittest


def symlink_or_skip(link, target, *, target_is_directory=False):
    try:
        link.symlink_to(target, target_is_directory=target_is_directory)
    except OSError as exc:
        if os.name == 'nt' and getattr(exc, 'winerror', None) == 1314:
            raise unittest.SkipTest('Windows fixture requires symlink privilege (WinError 1314)') from exc
        raise
