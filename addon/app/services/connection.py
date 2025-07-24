from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..db import Connection as ConnectionModel
from ..models import Connection, ConnectionCreate, ConnectionUpdate


def mask_api_key(api_key: str | None) -> str | None:
    if not api_key:
        return None
    if len(api_key) <= 8:
        return "********"
    return f"{api_key[:4]}...{api_key[-4:]}"


class ConnectionService:
    @staticmethod
    async def get_connections(db: AsyncSession, mask_key: bool = True) -> list[Connection]:
        """Get all connections from the database."""
        result = await db.execute(select(ConnectionModel))
        connections = result.scalars().all()
        validated_connections = []
        for connection in connections:
            conn_model = Connection.model_validate(connection)
            if mask_key:
                conn_model.api_key = mask_api_key(conn_model.api_key)
            validated_connections.append(conn_model)
        return validated_connections

    @staticmethod
    async def create_connection(
        db: AsyncSession, connection_create: ConnectionCreate
    ) -> Connection:
        """Create a new connection."""
        # Ensure only one connection is active at a time
        if len((await ConnectionService.get_connections(db))) == 0:
            db_connection = ConnectionModel(
                **connection_create.model_dump(), is_active=True
            )
        else:
            db_connection = ConnectionModel(
                **connection_create.model_dump(), is_active=False
            )

        db.add(db_connection)
        await db.commit()
        await db.refresh(db_connection)
        validated_connection = Connection.model_validate(db_connection)
        validated_connection.api_key = mask_api_key(validated_connection.api_key)
        return validated_connection

    @staticmethod
    async def update_connection(
        db: AsyncSession, connection_id: int, connection_update: ConnectionUpdate
    ) -> Connection:
        """Update a connection."""
        update_data = connection_update.model_dump(exclude_unset=True)
        if not update_data:
            # No fields to update
            result = await db.execute(
                select(ConnectionModel).where(ConnectionModel.id == connection_id)
            )
            connection = result.scalar_one()
            return Connection.model_validate(connection)

        await db.execute(
            update(ConnectionModel)
            .where(ConnectionModel.id == connection_id)
            .values(**update_data)
        )
        await db.commit()

        result = await db.execute(
            select(ConnectionModel).where(ConnectionModel.id == connection_id)
        )
        updated_connection = result.scalar_one()

        validated_connection = Connection.model_validate(updated_connection)
        validated_connection.api_key = mask_api_key(validated_connection.api_key)
        return validated_connection

    @staticmethod
    async def delete_connection(db: AsyncSession, connection_id: int) -> None:
        """Delete a connection."""
        result = await db.execute(
            select(ConnectionModel).where(ConnectionModel.id == connection_id)
        )
        connection = result.scalar_one_or_none()
        if connection:
            await db.delete(connection)
            await db.commit()

    @staticmethod
    async def set_active_connection(db: AsyncSession, connection_id: int) -> Connection:
        """Set a connection as active."""
        # Deactivate all other connections
        await db.execute(update(ConnectionModel).values(is_active=False))

        # Activate the selected connection
        await db.execute(
            update(ConnectionModel)
            .where(ConnectionModel.id == connection_id)
            .values(is_active=True)
        )
        await db.commit()

        result = await db.execute(
            select(ConnectionModel).where(ConnectionModel.id == connection_id)
        )
        updated_connection = result.scalar_one()

        validated_connection = Connection.model_validate(updated_connection)
        validated_connection.api_key = mask_api_key(validated_connection.api_key)
        return validated_connection

    @staticmethod
    async def get_active_connection(db: AsyncSession, mask_key: bool = True) -> Connection | None:
        """Get the active connection."""
        result = await db.execute(
            select(ConnectionModel).where(ConnectionModel.is_active.is_(True))
        )
        connection = result.scalar_one_or_none()
        if connection:
            validated_connection = Connection.model_validate(connection)
            if mask_key:
                validated_connection.api_key = mask_api_key(validated_connection.api_key)
            return validated_connection
        return None 