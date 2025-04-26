# utils.py

from typing import Callable, Iterable, Optional, TypeVar

T = TypeVar('T')

def find(predicate: Callable[[T], bool], iterable: Iterable[T]) -> Optional[T]:
    for element in iterable:
        if predicate(element):
            return element
    return None
