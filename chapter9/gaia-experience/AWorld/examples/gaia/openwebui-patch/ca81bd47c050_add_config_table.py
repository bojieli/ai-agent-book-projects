"""Add config table

Revision ID: ca81bd47c050
Revises: 7e5b5dc7342b
Create Date: 2024-08-25 15:26:35.241684

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = "ca81bd47c050"
down_revision: Union[str, None] = "7e5b5dc7342b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    op.create_table(
        "config",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("version", sa.Integer, nullable=False),
        sa.Column(
            "created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=True,
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )
    init_gaia_config()

def downgrade():
    op.drop_table("config")


def init_gaia_config():
    import json
    prompt_suggestions = None
    with open(
        "/app/aworld/examples/gaia/GAIA/2023/validation/metadata.jsonl",
        "r",
        encoding="utf-8",
    ) as f:
        data_set = [json.loads(line) for line in f]

        prompt_suggestions = [
            {
                "title": [
                    i["task_id"],
                    i["Question"][:100],
                ],
                "content": json.dumps({"task_id": i["task_id"]}),
            }
            for i in data_set
        ]

    conn = op.get_bind()
    conn.execute(
        text("INSERT INTO config (id, data, version) VALUES (1, :data, 0)"),
        {"data": json.dumps({"ui": {"prompt_suggestions": prompt_suggestions}})},
    )
    print(f">>> patch gaia_agent: add prompt_suggestions success!")

