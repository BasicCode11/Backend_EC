"""update_address_coordinates_precision

Revision ID: 2e0e9d9d9174
Revises: a52cca9e33b2
Create Date: 2025-10-28 16:29:05.906395

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2e0e9d9d9174'
down_revision = 'a52cca9e33b2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Both longitude and latitude should be DECIMAL(10, 7)
    # This provides 3 digits before decimal and 7 after
    # DECIMAL(10,7) range: -999.9999999 to 999.9999999
    # This is sufficient for:
    # - Longitude: -180 to 180 degrees
    # - Latitude: -90 to 90 degrees
    # - Precision: 7 decimal places = ~1.1cm accuracy
    
    # Note: If your existing table has different precision, this ensures both are DECIMAL(10,7)
    pass  # Both columns are already correctly defined as DECIMAL(10,7) in the initial migration


def downgrade() -> None:
    pass  # No changes needed
