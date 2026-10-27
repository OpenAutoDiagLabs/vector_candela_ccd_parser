"""Structdt → StructElement 转换器"""
from typing import Any

from ..base import BaseTransformer
from ...compat import Structdt, Name, Tuv
from ...models.containers import StructElement
from ...models.base import ByteOrder, DisplayFormat, Encoding, Quantity
from ...registry import ObjectRegistry


class StructdtTransformer(BaseTransformer):
    """将 Structdt（结构体数据类型）转换为 StructElement"""

    priority = 50
    handles_type = Structdt

    def match(self, raw_obj: Any) -> bool:
        return isinstance(raw_obj, Structdt)

    def transform(self, raw_obj: Structdt, registry: ObjectRegistry,
                  warnings: list, strict: bool = True) -> StructElement:
        name = raw_obj.name or Name(
            tuv=[Tuv(lang="en-US", value="Struct Data Type"),
                 Tuv(lang="zh-CN", value="结构体数据类型")]
        )

        from ..transformer_registry import TransformerRegistry
        tr = TransformerRegistry()

        children = []
        for item in raw_obj.items:
            inner_element = tr.transform_one(item, registry, warnings, strict)
            if inner_element is not None:
                children.append(inner_element)

        return StructElement(
            id=raw_obj.oid,
            name=name,
            description=raw_obj.desc,
            qualifier=raw_obj.qual,
            children=tuple(children),
        )
