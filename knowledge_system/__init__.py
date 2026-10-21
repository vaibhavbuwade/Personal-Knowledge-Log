"""
knowledge_system package initialization.
Includes Python 3.14 compatibility adjustment for Django template BaseContext copy.
"""

try:
    from django.template.context import BaseContext

    def _base_context_copy(self):
        duplicate = self.__class__.__new__(self.__class__)
        duplicate.__dict__.update(self.__dict__)
        duplicate.dicts = self.dicts[:]
        return duplicate

    BaseContext.__copy__ = _base_context_copy
except Exception:
    pass
