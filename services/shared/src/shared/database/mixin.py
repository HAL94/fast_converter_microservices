from abc import ABC
from typing import ClassVar, Self
from pydantic import BaseModel
from .base import Base
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql.elements import ColumnElement
from sqlalchemy.ext.asyncio import AsyncSession


class BaseModelDatabaseMixin(BaseModel, ABC):
    model: ClassVar[type[Base]]

    @classmethod
    async def create(
        cls,
        session: AsyncSession,
        data: BaseModel,
        /,
        *,
        commit: bool = True,
        return_as_base: bool = False,        
    ):
        try:
            result = await cls.model.create(session, data, commit=commit)
            if commit:
                await session.commit()

            if return_as_base:
                return result
            
            return cls.model_validate(result, from_attributes=True)
        except Exception as e:
            raise e

    @classmethod
    async def get_one(
        cls,
        session: AsyncSession,
        val,
        /,
        *,
        field: InstrumentedAttribute | None = None,
        where_clause: list[ColumnElement[bool]] | None = None,
        return_as_base: bool = False,
    ) -> Self | type[Base]:
        result: Base = await cls.model.get_one(
            session, val, field=field, where_clause=where_clause
        )
        if not result:
            return None

        if return_as_base:
            return result
        return cls.model_validate(result, from_attributes=True)
