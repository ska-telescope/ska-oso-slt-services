from os import environ
from typing import Any, cast

from pydantic import (
    BaseModel,
    ConfigDict,
    SerializerFunctionWrapHandler,
    model_serializer,
)
from pydantic.config import ExtraValues
from pydantic_core import PydanticUndefined

EXTRA_FIELDS = cast(ExtraValues | None, environ.get("EXTRA_FIELDS"))


class PdmObject(BaseModel):
    """Shared Base Class for all PDM Entities."""

    # https://docs.pydantic.dev/latest/api/config/#pydantic.config.ConfigDict
    model_config = ConfigDict(
        extra=EXTRA_FIELDS,  # Defaults to 'ignore'; can we prefer 'forbid' here?
        # Validate assignments and defaults to help keep ourselves honest:
        validate_assignment=True,
        validate_default=True,
        ser_json_timedelta="float",
    )

    def _is_default(self, key: str) -> bool:
        field_info = self.model_fields[key]
        if field_info.default_factory is not None:
            default = field_info.default_factory()
        elif field_info.default is not PydanticUndefined:
            default = field_info.default
        else:
            default = PydanticUndefined
        return getattr(self, key) == default

    @staticmethod
    def _is_empty(value: Any) -> bool:
        return value in (None, [], {})

    def _exclude_default_nulls_and_empty(
        self, dumped: dict[str, Any]
    ) -> dict[str, Any]:
        """To avoid cluttering JSON output, we want to omit any None, [], {} values
        that are present by default, but preserve any 'empty' values that were deliberately
        set by callers."""
        filtered = {
            key: val
            for key, val in dumped.items()
            if not (self._is_empty(val) and self._is_default(key))
        }
        return filtered

    @model_serializer(mode="wrap")
    def _serialize(
        self, default_serializer: SerializerFunctionWrapHandler
    ) -> dict[str, Any]:
        dumped = default_serializer(self)
        without_nulls = self._exclude_default_nulls_and_empty(dumped)
        return without_nulls


import json
from os import PathLike
from typing import Type


class OpenAPICodec:
    """
    OpenAPICodec serialises and deserialises PDM Entities to and from
    JSON.
    """

    @staticmethod
    def loads(klass: Type[PdmObject], json_data: str) -> PdmObject:
        return klass.model_validate_json(json_data)

    @staticmethod
    def dumps(entity: PdmObject) -> str:
        return entity.model_dump_json()

    @staticmethod
    def load_from_file(klass: Type[PdmObject], path: PathLike[str]):
        """
        Load an instance of a generated class from disk.

        :param klass: the class to create from the file
        :param path: the path to the file
        :return: an instance of class
        """
        with open(path, "r", encoding="utf-8") as json_file:
            json_data = json_file.read()
            return OpenAPICodec.loads(klass, json_data)


CODEC = OpenAPICodec()
