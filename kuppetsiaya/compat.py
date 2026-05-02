from copy import copy

from django.template.context import BaseContext


def _copy_base_context(self):
    duplicate = self.__class__.__new__(self.__class__)
    duplicate.__dict__ = self.__dict__.copy()
    duplicate.dicts = self.dicts[:]
    return duplicate


def apply_compat_patches():
    sample_context = BaseContext()
    try:
        copy(sample_context)
    except AttributeError as exc:
        if "dicts" not in str(exc):
            raise
        BaseContext.__copy__ = _copy_base_context
