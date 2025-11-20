# fds_django/services/model_utils.py
from typing import Dict, Any, Type
from django.db import models


def filter_model_defaults(model: Type[models.Model], data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return a dict filtered to only concrete fields of the given model.

    - Drops keys that don't exist as model fields
    - Ignores many-to-many and reverse relations
    - Ignores auto-created fields
    """
    field_names = {
        f.name
        for f in model._meta.get_fields()
        if getattr(f, "concrete", False) and not f.many_to_many and not getattr(f, "auto_created", False)
    }
    return {k: v for k, v in data.items() if k in field_names}