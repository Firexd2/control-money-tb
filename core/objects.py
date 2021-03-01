from typing import Optional

from core.cache import user_cache
from core.utils.commands import c
from core.utils.common import ConvType
from core.utils.db import Database, Field, IntField, StrField


class User(Database):
    _id = Field()
    id = IntField()
    first_name = StrField()
    last_name = StrField()
    username = StrField()
    client_name = StrField()

    _conv: Optional[ConvType] = None

    cache_objects = {"search_by": "id", "object": user_cache}

    def get_commands(self):
        return c("Внести трату", "test")
