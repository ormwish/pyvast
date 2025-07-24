from .registry import register_adapter, get_adapter
from .mock import MockAdapter
register_adapter('mock', MockAdapter)
__all__ = ['register_adapter','get_adapter','MockAdapter']
