"""Initial schema.

Revision ID: 0001
Revises:
Create Date: 2026-06-20
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- Native PostgreSQL ENUM types ---
    usertype = postgresql.ENUM(
        "DOCTOR", "PATIENT", "ADMIN", "SYSADMIN", name="usertype", create_type=False
    )
    usertype.create(op.get_bind(), checkfirst=True)

    accountstatus = postgresql.ENUM(
        "INACTIVE", "ACTIVE", "DEACTIVATED", "DELETED", name="accountstatus", create_type=False
    )
    accountstatus.create(op.get_bind(), checkfirst=True)

    membershipsource = postgresql.ENUM("AUTO", "MANUAL", name="membershipsource", create_type=False)
    membershipsource.create(op.get_bind(), checkfirst=True)

    appointmentstate = postgresql.ENUM(
        "PENDING", "CONFIRMED", "DECLINED", name="appointmentstate", create_type=False
    )
    appointmentstate.create(op.get_bind(), checkfirst=True)

    consentsourcetype = postgresql.ENUM(
        "MANUAL", "APPOINTMENT", name="consentsourcetype", create_type=False
    )
    consentsourcetype.create(op.get_bind(), checkfirst=True)

    auditoutcome = postgresql.ENUM("SUCCESS", "FAILURE", name="auditoutcome", create_type=False)
    auditoutcome.create(op.get_bind(), checkfirst=True)

    # --- account ---
    op.create_table(
        "account",
        sa.Column("id", sa.UUID(), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=True),
        sa.Column(
            "user_type",
            postgresql.ENUM(
                "DOCTOR", "PATIENT", "ADMIN", "SYSADMIN", name="usertype", create_type=False
            ),
            nullable=False,
        ),
        sa.Column(
            "status",
            postgresql.ENUM(
                "INACTIVE",
                "ACTIVE",
                "DEACTIVATED",
                "DELETED",
                name="accountstatus",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("first_name", sa.String(), nullable=True),
        sa.Column("surname", sa.String(), nullable=True),
        sa.Column("date_of_birth", sa.Date(), nullable=True),
        sa.Column("password_changed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("fhir_extensions", postgresql.JSONB(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_account_email"),
    )
    op.create_index("ix_account_email", "account", ["email"])

    # --- group ---
    op.create_table(
        "group",
        sa.Column("id", sa.UUID(), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column(
            "auto_user_type",
            postgresql.ENUM(
                "DOCTOR", "PATIENT", "ADMIN", "SYSADMIN", name="usertype", create_type=False
            ),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # --- module_registry ---
    op.create_table(
        "module_registry",
        sa.Column("id", sa.UUID(), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("module_key", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("version", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("module_key", name="uq_module_registry_module_key"),
    )

    # --- group_membership ---
    op.create_table(
        "group_membership",
        sa.Column("group_id", sa.UUID(), nullable=False),
        sa.Column("account_id", sa.UUID(), nullable=False),
        sa.Column(
            "source",
            postgresql.ENUM("AUTO", "MANUAL", name="membershipsource", create_type=False),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["group_id"], ["group.id"], name="fk_group_membership_group_id"),
        sa.ForeignKeyConstraint(
            ["account_id"], ["account.id"], name="fk_group_membership_account_id"
        ),
        sa.PrimaryKeyConstraint("group_id", "account_id"),
    )

    # --- group_module_enablement ---
    op.create_table(
        "group_module_enablement",
        sa.Column("group_id", sa.UUID(), nullable=False),
        sa.Column("module_id", sa.UUID(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["group_id"], ["group.id"], name="fk_group_module_enablement_group_id"
        ),
        sa.ForeignKeyConstraint(
            ["module_id"],
            ["module_registry.id"],
            name="fk_group_module_enablement_module_id",
        ),
        sa.PrimaryKeyConstraint("group_id", "module_id"),
    )

    # --- appointment ---
    op.create_table(
        "appointment",
        sa.Column("id", sa.UUID(), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("doctor_id", sa.UUID(), nullable=False),
        sa.Column("patient_id", sa.UUID(), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "state",
            postgresql.ENUM(
                "PENDING", "CONFIRMED", "DECLINED", name="appointmentstate", create_type=False
            ),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["doctor_id"], ["account.id"], name="fk_appointment_doctor_id"),
        sa.ForeignKeyConstraint(["patient_id"], ["account.id"], name="fk_appointment_patient_id"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_appointment_doctor_id", "appointment", ["doctor_id"])
    op.create_index("ix_appointment_patient_id", "appointment", ["patient_id"])

    # --- clinical_entry ---
    op.create_table(
        "clinical_entry",
        sa.Column("id", sa.UUID(), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("patient_id", sa.UUID(), nullable=False),
        sa.Column("author_doctor_id", sa.UUID(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["patient_id"], ["account.id"], name="fk_clinical_entry_patient_id"
        ),
        sa.ForeignKeyConstraint(
            ["author_doctor_id"],
            ["account.id"],
            name="fk_clinical_entry_author_doctor_id",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # --- attachment ---
    op.create_table(
        "attachment",
        sa.Column("id", sa.UUID(), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("clinical_entry_id", sa.UUID(), nullable=False),
        sa.Column("patient_id", sa.UUID(), nullable=False),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("content_type", sa.String(), nullable=False),
        sa.Column("size", sa.BigInteger(), nullable=False),
        sa.Column("storage_key", sa.String(), nullable=False),
        sa.Column("checksum", sa.String(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["clinical_entry_id"],
            ["clinical_entry.id"],
            name="fk_attachment_clinical_entry_id",
        ),
        sa.ForeignKeyConstraint(["patient_id"], ["account.id"], name="fk_attachment_patient_id"),
        sa.PrimaryKeyConstraint("id"),
    )

    # --- consent_grant ---
    op.create_table(
        "consent_grant",
        sa.Column("id", sa.UUID(), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("patient_id", sa.UUID(), nullable=False),
        sa.Column("doctor_id", sa.UUID(), nullable=False),
        sa.Column(
            "source_type",
            postgresql.ENUM("MANUAL", "APPOINTMENT", name="consentsourcetype", create_type=False),
            nullable=False,
        ),
        sa.Column("appointment_id", sa.UUID(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["patient_id"], ["account.id"], name="fk_consent_grant_patient_id"),
        sa.ForeignKeyConstraint(["doctor_id"], ["account.id"], name="fk_consent_grant_doctor_id"),
        sa.ForeignKeyConstraint(
            ["appointment_id"],
            ["appointment.id"],
            name="fk_consent_grant_appointment_id",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_consent_grant_patient_doctor_active",
        "consent_grant",
        ["patient_id", "doctor_id", "active"],
    )

    # --- audit_log ---
    # actor_id is NOT a FK — actor may be unknown for pre-auth events (SR-023)
    op.create_table(
        "audit_log",
        sa.Column("id", sa.UUID(), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("actor_id", sa.UUID(), nullable=True),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("target_type", sa.String(), nullable=True),
        sa.Column("target_id", sa.String(), nullable=True),
        sa.Column(
            "outcome",
            postgresql.ENUM("SUCCESS", "FAILURE", name="auditoutcome", create_type=False),
            nullable=False,
        ),
        sa.Column("ip", sa.String(), nullable=True),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # --- anonymized_dataset ---
    op.create_table(
        "anonymized_dataset",
        sa.Column("id", sa.UUID(), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("code_hash", sa.String(), nullable=False),
        sa.Column("payload", postgresql.JSONB(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("retention_deadline", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("anonymized_dataset")
    op.drop_table("audit_log")
    op.drop_index("ix_consent_grant_patient_doctor_active", table_name="consent_grant")
    op.drop_table("consent_grant")
    op.drop_table("attachment")
    op.drop_table("clinical_entry")
    op.drop_index("ix_appointment_patient_id", table_name="appointment")
    op.drop_index("ix_appointment_doctor_id", table_name="appointment")
    op.drop_table("appointment")
    op.drop_table("group_module_enablement")
    op.drop_table("group_membership")
    op.drop_table("module_registry")
    op.drop_table("group")
    op.drop_index("ix_account_email", table_name="account")
    op.drop_table("account")

    # Drop enum types
    for name in [
        "auditoutcome",
        "consentsourcetype",
        "appointmentstate",
        "membershipsource",
        "accountstatus",
        "usertype",
    ]:
        sa.Enum(name=name).drop(op.get_bind(), checkfirst=True)
