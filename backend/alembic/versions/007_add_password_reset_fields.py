"""Add password reset token fields to users table

Revision ID: 007_add_password_reset_fields
Revises: 006_add_database_indexes
Create Date: 2026-04-19 10:00:00+00:00
"""

from alembic import op
import sqlalchemy as sa

revision = "007_add_password_reset_fields"
down_revision = "006_add_database_indexes"
branch_labels = None
depends_on = None


def upgrade():
    """Add password reset fields to users table"""
    
    # Add password_reset_token column
    try:
        op.add_column('users', sa.Column('password_reset_token', sa.String(), nullable=True, unique=True, index=True))
    except Exception as e:
        print(f"Column password_reset_token already exists or error: {e}")
    
    # Add password_reset_token_expires column
    try:
        op.add_column('users', sa.Column('password_reset_token_expires', sa.DateTime(), nullable=True))
    except Exception as e:
        print(f"Column password_reset_token_expires already exists or error: {e}")


def downgrade():
    """Remove password reset fields from users table"""
    try:
        op.drop_column('users', 'password_reset_token_expires')
    except:
        pass
    
    try:
        op.drop_column('users', 'password_reset_token')
    except:
        pass
