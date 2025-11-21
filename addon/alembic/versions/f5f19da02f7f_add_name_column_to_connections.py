"""add_name_column_to_connections

Revision ID: f5f19da02f7f
Revises: 
Create Date: 2025-11-18 20:30:12.643498

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f5f19da02f7f'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Rename table connections to backends
    op.rename_table('connections', 'backends')
    
    # Rename column backend to type, add name column, drop is_active and model
    with op.batch_alter_table('backends', schema=None) as batch_op:
        batch_op.add_column(sa.Column('name', sa.String(), nullable=True))
        batch_op.drop_column('is_active')
        batch_op.drop_column('model')
        batch_op.alter_column('backend', new_column_name='type', existing_type=sa.String(), nullable=False)
    
    # Rename connection_id to backend_id in model_configs, update FK
    with op.batch_alter_table('model_configs', schema=None) as batch_op:
        batch_op.alter_column('connection_id', new_column_name='backend_id', existing_type=sa.Integer(), nullable=False)
        
        # Recreate FK to point to backends
        batch_op.create_foreign_key(
            'model_configs_backend_id_fkey',
            'backends',
            ['backend_id'],
            ['id']
        )


def downgrade() -> None:
    """Downgrade schema."""
    # Revert backend_id to connection_id in model_configs
    with op.batch_alter_table('model_configs', schema=None) as batch_op:
        batch_op.alter_column('backend_id', new_column_name='connection_id', existing_type=sa.Integer(), nullable=False)
        
        # Recreate FK to point to connections
        batch_op.create_foreign_key(
            'model_configs_connection_id_fkey',
            'connections',
            ['connection_id'],
            ['id']
        )
    
    # Revert backends table changes
    with op.batch_alter_table('backends', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_active', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('model', sa.String(), nullable=True))
        batch_op.drop_column('name')
        batch_op.alter_column('type', new_column_name='backend', existing_type=sa.String(), nullable=False)
    
    # Rename table back to connections
    op.rename_table('backends', 'connections')
