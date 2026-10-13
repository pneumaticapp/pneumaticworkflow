"""sync_files_orm

Revision ID: 5ba2db086f1a
Revises: 4ba2db086f19
Create Date: 2026-05-26 23:14:00.000000

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '5ba2db086f1a'
down_revision: Union[str, None] = '4ba2db086f19'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Remove the redundant ix_files_id index
    op.drop_index('ix_files_id', table_name='files')
    
    # Drop the primary key constraint on 'id'
    op.drop_constraint('files_pkey', 'files', type_='primary')
    
    # Drop the 'id' column entirely
    op.drop_column('files', 'id')
    
    # Make file_id the primary key
    op.create_primary_key('files_pkey', 'files', ['file_id'])
    
    # The ix_files_file_id index is redundant as it is now a PK, but PostgreSQL handles unique PKs anyway.
    # We'll drop the unique index created previously to avoid redundancy
    op.drop_index('ix_files_file_id', table_name='files')


def downgrade() -> None:
    # Re-create the unique index on file_id
    op.create_index('ix_files_file_id', 'files', ['file_id'], unique=True)
    
    # Drop the new primary key on file_id
    op.drop_constraint('files_pkey', 'files', type_='primary')
    
    # Add back the 'id' column
    op.add_column('files', sa.Column('id', sa.Integer(), nullable=False, autoincrement=True))
    
    # Make 'id' the primary key again
    op.create_primary_key('files_pkey', 'files', ['id'])
    
    # Re-create the index on 'id'
    op.create_index('ix_files_id', 'files', ['id'], unique=False)
