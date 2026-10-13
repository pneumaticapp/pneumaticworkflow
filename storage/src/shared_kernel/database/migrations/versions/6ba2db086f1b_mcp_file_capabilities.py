"""Add MCP upload mappings, recovery journal and hashed download tickets."""

# Project convention omits return annotations on procedures.
# mypy: disable-error-code="no-untyped-def"

import sqlalchemy as sa
from alembic import op

revision = '6ba2db086f1b'
down_revision = '5ba2db086f1a'
branch_labels = None
depends_on = None


def upgrade():
    """Create MCP tables without changing existing file records."""
    op.create_table(
        'mcp_uploads',
        sa.Column('session_id', sa.String(128), primary_key=True),
        sa.Column('connection_id', sa.String(128), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('file_id', sa.String(), nullable=False, unique=True),
        sa.Column('fingerprint', sa.String(64), nullable=False),
        sa.Column(
            'cleanup_checked_at', sa.DateTime(timezone=True), nullable=True
        ),
    )
    op.create_index(
        'ix_mcp_uploads_cleanup_checked_at',
        'mcp_uploads',
        ['cleanup_checked_at'],
    )
    op.create_table(
        'mcp_download_tickets',
        sa.Column('token_hash', sa.String(64), primary_key=True),
        sa.Column('connection_id', sa.String(128), nullable=False),
        sa.Column('authorization_id', sa.String(128), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column(
            'file_id',
            sa.String(),
            sa.ForeignKey('files.file_id'),
            nullable=False,
        ),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        'ix_mcp_download_tickets_expires_at',
        'mcp_download_tickets',
        ['expires_at'],
    )
    op.create_table(
        'mcp_upload_attempts',
        sa.Column('session_id', sa.String(128), primary_key=True),
        sa.Column('connection_id', sa.String(128), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('account_id', sa.Integer(), nullable=False),
        sa.Column('file_id', sa.String(), nullable=False, unique=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            'cleanup_checked_at', sa.DateTime(timezone=True), nullable=True
        ),
    )
    op.create_index(
        'ix_mcp_upload_attempts_created_at',
        'mcp_upload_attempts',
        ['created_at'],
    )
    op.create_index(
        'ix_mcp_upload_attempts_cleanup_checked_at',
        'mcp_upload_attempts',
        ['cleanup_checked_at'],
    )


def downgrade():
    """Remove MCP-only state."""
    op.drop_table('mcp_upload_attempts')
    op.drop_table('mcp_download_tickets')
    op.drop_table('mcp_uploads')
