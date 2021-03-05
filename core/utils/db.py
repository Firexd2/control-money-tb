from core import db


class Field:

    def __init__(self, *args, **kwargs):
        self.default = kwargs.get("default")

    def deserialize(self, value, parent):
        if value is not None:
            return value
        else:
            return self.get_default()

    def serialize(self, value):
        return value

    def get_default(self):
        if callable(self.default):
            return self.default()
        else:
            return self.default


class IntField(Field):

    def deserialize(self, value, parent):
        if value is not None:
            return int(value)
        else:
            return self.get_default()

    def serialize(self, value):
        return value


class StrField(Field):

    def deserialize(self, value, parent):
        if value is not None:
            return str(value)
        else:
            return self.get_default()

    def serialize(self, value):
        return value


class ListField(Field):

    def deserialize(self, value, parent):
        if value is not None:
            return list(value)
        else:
            return self.get_default()

    def serialize(self, value):
        return value


class OneOfManyField(Field):

    def __init__(self, objects, *args, **kwargs):
        super().__init__(objects, *args, **kwargs)
        self.names_to_objects = {o.__name__: o for o in objects}

    def deserialize(self, value, parent):
        if value is not None:
            kw = {k: v for k, v in value.items() if k != "name"}
            instance = self.names_to_objects[value["name"]](**kw)
            instance._parent = parent

            return instance
        else:
            return self.get_default()

    def serialize(self, value):
        if value is not None:
            return value.serialize()


class OneOfOneField(Field):

    def __init__(self, object, *args, **kwargs):
        super().__init__(object, *args, **kwargs)
        self.object = object

    def deserialize(self, value, parent):
        if value is not None:
            kw = {k: v for k, v in value.items() if k != "name"}
            instance = self.object(**kw)
            instance._parent = parent

            return instance
        else:
            return self.get_default()

    def serialize(self, value):
        if value is not None:
            return value.serialize()


class ManyOfOneField(Field):

    def __init__(self, object, *args, **kwargs):
        super().__init__(object, *args, **kwargs)
        self.object = object

    def deserialize(self, value, parent):
        if value is not None:
            r = []
            for item in value:
                kw = {k: v for k, v in item.items() if k != "name"}
                instance = self.object(**kw)
                instance._parent = parent
                r.append(instance)

            return r
        else:
            return self.get_default()

    def serialize(self, value: list):
        if value is not None:
            r = []
            for item in value:
                r.append(item.serialize())

            return r


class ManyOfManyField(Field):

    def __init__(self, objects, *args, **kwargs):
        super().__init__(objects, *args, **kwargs)
        self.names_to_objects = {o.__name__: o for o in objects}

    def deserialize(self, value, parent):
        if value is not None:
            r = []
            for item in value:
                kw = {k: v for k, v in item.items() if k != "name"}
                instance = self.names_to_objects[item["name"]](**kw)
                instance._parent = parent
                r.append(instance)

            return r
        else:
            return self.get_default()

    def serialize(self, value):
        if value is not None:
            value_ = []
            for item in value:
                value_.append(item.serialize())

            return value_


class Model:

    def __init__(self, **kwargs):
        for key, val in self.get_fields():
            instance = val.deserialize(kwargs.get(key), parent=self)
            setattr(self, key, instance)

    def serialize(self):
        result = {"name": self.__class__.__name__}
        for key, val in self.get_fields():
            result[key] = val.serialize(getattr(self, key))

        return result

    @classmethod
    def get_fields(cls):
        mro = list(cls.__mro__)
        mro.reverse()
        for inh_class in mro:
            for k, v in vars(inh_class).items():
                if isinstance(v, Field):
                    yield k, v


class Database(Model):

    class GetObjectException(Exception):
        pass

    cache_objects = {
        "search_by": None,
        "object": None
    }

    @classmethod
    def get_collection(cls):
        return getattr(db, cls.__name__.lower())

    def _get_columns(self) -> dict:
        # TODO: тут надо подумать над vars(self). Ниже костыль с hasattr serialize
        columns = {key: value for key, value in vars(self).items() if key[0] != '_'}
        for key, value in columns.items():
            if hasattr(value, "serialize"):
                columns[key] = columns[key].serialize()
            elif type(value) == list:
                r = []
                for sub_v in value:
                    if hasattr(sub_v, "serialize"):
                        r.append(sub_v.serialize())
                    else:
                        r.append(sub_v)

                columns[key] = r

        return columns

    @classmethod
    def _save_cache(cls, obj) -> None:
        cls.cache_objects["object"][getattr(obj, cls.cache_objects["search_by"])] = obj

    @classmethod
    async def filter(cls, kwargs):

        cursor = cls.get_collection().find(kwargs)
        raw_objs = []
        async for raw_obj in cursor:
            raw_objs.append(raw_obj)

        # пока пытаемся вытащить из кэша, а потом создавать новый объект
        objs = []
        cache_exists = cls.cache_objects.get("search_by", False)
        for raw_obj in raw_objs:
            if cache_exists and raw_obj['id'] in cls.cache_objects["object"]:
                objs.append(cls.cache_objects["object"][raw_obj[cls.cache_objects["search_by"]]])
            else:
                obj = cls(**raw_obj)
                objs.append(obj)

                if cache_exists:
                    cls._save_cache(obj)

        return objs

    @classmethod
    async def get(cls, **kwargs):
        cache_exists = cls.cache_objects.get("search_by", False)
        if cache_exists:
            val_for_cache = kwargs.get(cls.cache_objects["search_by"], None)
            if val_for_cache and val_for_cache in cls.cache_objects["object"]:
                return cls.cache_objects["object"][val_for_cache]

        raw_obj = await cls.get_collection().find_one(kwargs)
        if raw_obj:
            obj = cls(**{k: v for k, v in raw_obj.items()})
            if cache_exists:
                cls._save_cache(obj)

            return obj

    @classmethod
    async def create(cls, data):
        _id = (await cls.get_collection().insert_one(data)).inserted_id

        return await cls.get(_id=_id)

    async def save(self) -> None:
        await self.get_collection().update_one({"_id": self._id}, {'$set': self._get_columns()})

    async def delete(self):
        await self.get_collection().delete_one({"_id": self._id})

    async def refresh(self):
        return await self.get(_id=self._id)
