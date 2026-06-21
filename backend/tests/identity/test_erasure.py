"""TASK-035: Erasure service tests."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import fakeredis
import pytest

from app.api.errors import AuthorizationError, UnauthenticatedError
from app.auth.password import PasswordService
from app.auth.session import SessionService
from app.db.models.account import Account, AccountStatus, UserType
from app.db.models.anonymized_dataset import AnonymizedDataset
from app.identity.erasure import ErasureService


def _make_account(user_type: UserType = UserType.PATIENT) -> Account:
    return Account(
        id=uuid.uuid4(),
        email="user@example.com",
        user_type=user_type,
        status=AccountStatus.ACTIVE,
    )


def _build_svc(account: Account | None) -> ErasureService:
    mock_repo = MagicMock()
    mock_repo.get_by_id.return_value = account

    mock_dataset_repo = MagicMock()

    # Make add() set an id on the dataset
    def fake_add(dataset):
        dataset.id = uuid.uuid4()
        return dataset

    mock_dataset_repo.add.side_effect = fake_add

    r = fakeredis.FakeRedis()
    session_svc = SessionService(r)
    pw_svc = PasswordService()
    mock_audit = MagicMock()

    return ErasureService(mock_repo, mock_dataset_repo, session_svc, pw_svc, mock_audit)


def test_sysadmin_can_erase_any_account() -> None:
    actor = _make_account(UserType.SYSADMIN)
    target = _make_account(UserType.PATIENT)
    svc = _build_svc(target)
    result = svc.delete(actor, target.id)
    assert result.retrieval_code is not None
    assert target.status == AccountStatus.DELETED


def test_erase_severs_pii() -> None:
    actor = _make_account(UserType.SYSADMIN)
    target = _make_account(UserType.PATIENT)
    target.first_name = "Alice"
    target.surname = "Smith"
    svc = _build_svc(target)
    svc.delete(actor, target.id)
    assert target.first_name is None
    assert target.surname is None
    assert "deleted.invalid" in target.email


def test_erase_severs_password_hash() -> None:
    actor = _make_account(UserType.SYSADMIN)
    target = _make_account(UserType.PATIENT)
    target.password_hash = "$argon2id$secret"
    svc = _build_svc(target)
    svc.delete(actor, target.id)
    assert target.password_hash is None


def test_erase_generates_retrieval_code() -> None:
    actor = _make_account(UserType.SYSADMIN)
    target = _make_account(UserType.PATIENT)
    svc = _build_svc(target)
    result = svc.delete(actor, target.id)
    assert len(result.retrieval_code) > 20


def test_erase_stores_argon2id_hash_not_plaintext() -> None:
    actor = _make_account(UserType.SYSADMIN)
    target = _make_account(UserType.PATIENT)
    mock_repo = MagicMock()
    mock_repo.get_by_id.return_value = target
    mock_dataset_repo = MagicMock()
    stored_datasets: list[AnonymizedDataset] = []

    def capture_add(dataset):
        dataset.id = uuid.uuid4()
        stored_datasets.append(dataset)
        return dataset

    mock_dataset_repo.add.side_effect = capture_add

    r = fakeredis.FakeRedis()
    svc = ErasureService(
        mock_repo, mock_dataset_repo, SessionService(r), PasswordService(), MagicMock()
    )

    result = svc.delete(actor, target.id)

    assert len(stored_datasets) == 1
    ds = stored_datasets[0]
    # Hash must be Argon2id, not the raw code
    assert ds.code_hash.startswith("$argon2id$")
    assert result.retrieval_code not in ds.code_hash


def test_erase_audits_deletion_and_anonymization() -> None:
    actor = _make_account(UserType.SYSADMIN)
    target = _make_account(UserType.PATIENT)
    mock_repo = MagicMock()
    mock_repo.get_by_id.return_value = target
    mock_dataset_repo = MagicMock()

    def fake_add(dataset):
        dataset.id = uuid.uuid4()
        return dataset

    mock_dataset_repo.add.side_effect = fake_add

    r = fakeredis.FakeRedis()
    mock_audit = MagicMock()
    svc = ErasureService(
        mock_repo, mock_dataset_repo, SessionService(r), PasswordService(), mock_audit
    )

    svc.delete(actor, target.id)
    calls = str(mock_audit.record.call_args_list)
    assert "ACCOUNT_DELETED" in calls
    assert "DATA_ANONYMIZED" in calls


def test_patient_can_erase_own_account() -> None:
    target = _make_account(UserType.PATIENT)
    svc = _build_svc(target)
    result = svc.delete(target, target.id)  # self-erasure
    assert result.dataset_id is not None


def test_non_sysadmin_cannot_erase_other_account() -> None:
    actor = _make_account(UserType.PATIENT)
    target = _make_account(UserType.PATIENT)
    svc = _build_svc(target)
    with pytest.raises(AuthorizationError):
        svc.delete(actor, target.id)


def test_retrieve_anonymized_valid_code() -> None:
    pw_svc = PasswordService()

    raw_code = "valid-retrieval-code-abc123"
    stored_hash = pw_svc.hash(raw_code)

    ds = AnonymizedDataset(
        id=uuid.uuid4(),
        code_hash=stored_hash,
        payload={},
        retention_deadline=datetime.now(UTC) + timedelta(days=1825),
    )
    mock_dataset_repo = MagicMock()
    mock_dataset_repo.list.return_value = [ds]

    r = fakeredis.FakeRedis()
    svc = ErasureService(MagicMock(), mock_dataset_repo, SessionService(r), pw_svc, MagicMock())

    result = svc.retrieve_anonymized(raw_code)
    assert result.id == ds.id


def test_retrieve_anonymized_wrong_code_raises() -> None:
    pw_svc = PasswordService()
    ds = AnonymizedDataset(
        id=uuid.uuid4(),
        code_hash=pw_svc.hash("correct-code"),
        payload={},
        retention_deadline=datetime.now() + timedelta(days=1825),
    )
    mock_dataset_repo = MagicMock()
    mock_dataset_repo.list.return_value = [ds]

    r = fakeredis.FakeRedis()
    svc = ErasureService(MagicMock(), mock_dataset_repo, SessionService(r), pw_svc, MagicMock())

    with pytest.raises(UnauthenticatedError):
        svc.retrieve_anonymized("wrong-code")
