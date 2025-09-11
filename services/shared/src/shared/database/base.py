from datetime import datetime
from typing import override, Dict, Any, Union
from sqlalchemy import DateTime, Select, inspect, func, Column, select
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, Load, RelationshipProperty
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.sql import ColumnElement
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from pydantic import BaseModel
from asyncpg.exceptions import ForeignKeyViolationError, UniqueViolationError


class Base(DeclarativeBase):
    id: Mapped[int] = mapped_column("id", autoincrement=True, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.now())

    def dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
    
    @classmethod
    def relations(cls):
        return inspect(cls).relationships.items()

    @classmethod
    def columns(cls):
        return {_column.name for _column in inspect(cls).c}

    @classmethod
    def table(cls):
        return cls.__table__
    
    @override
    def __repr__(self) -> str:
        return str(self.dict())


    @classmethod
    async def count(cls, session: AsyncSession, /) -> int:
        return await session.scalar(func.count(cls.id))

    @classmethod
    def get_select_in_load(cls) -> list[Load]:
        return []

    @classmethod
    def get_options(cls) -> list[Load]:
        return cls.get_select_in_load()

    @classmethod
    def get_relationships(cls) -> Dict[str, RelationshipProperty[Any]]:
        mapper = inspect(cls)
        relations = {rel[0]: rel[1] for rel in mapper.relationships.items()}
        return relations

    @classmethod
    def get_foreign_columns(cls) -> Dict[str, Column]:
        relations = cls.get_relationships()
        foreign_cols = {}
        for rel in relations:
            relationship_property: RelationshipProperty = relations[rel]
            for fk in relationship_property.remote_side:
                fk: Column = fk
                foreign_cols[rel] = fk.name

        return foreign_cols

    @classmethod
    async def create(
        cls,
        session: AsyncSession,
        data: Union[BaseModel, Dict],
        /,
        *,
        commit: bool = True,
    ):
        try:
            payload = data
            if isinstance(data, BaseModel):
                payload = data.model_dump(
                    exclude_none=True, exclude_unset=True, by_alias=False
                )

            obj: Base = cls(**payload)

            session.add(obj)

            if commit:
                await session.commit()

            return obj
        except IntegrityError as e:
            await session.rollback()

            if e.orig.sqlstate == UniqueViolationError.sqlstate:
                raise ValueError("Unique Constraint is Violated")
            elif e.orig.sqlstate == ForeignKeyViolationError.sqlstate:
                raise ValueError("Foreig Key Constraint is violated")

            raise e

    @classmethod
    async def get_one(
        cls,
        session: AsyncSession,
        val: Any,
        /,
        *,
        field: InstrumentedAttribute | str | None = None,
        where_clause: list[ColumnElement[bool]] = None,
    ):
        options = cls.get_options()

        if field is None:
            field = cls.id

        where_base = [field == val]

        if where_clause:
            where_base.extend(where_clause)

        statement: Select = select(cls).where(*where_base)

        if options:
            statement = statement.options(*options)

        result = await session.scalar(statement)

        return result
