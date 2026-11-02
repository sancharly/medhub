"""TASK-178 / CR-002 AC-11: object-store migration script, with two in-memory stores.

The script is operator tooling in ``backend/scripts``; it is loaded by path, as that directory
is not a package. No network, no database and no boto3 call is made.
"""

from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path
from typing import Any

import pytest
from botocore.stub import ANY, Stubber

SCRIPT = Path(__file__).resolve().parents[2] / "scripts" / "migrate_object_store.py"
spec = importlib.util.spec_from_file_location("migrate_object_store", SCRIPT)
assert spec is not None and spec.loader is not None
mos = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mos
spec.loader.exec_module(mos)


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class FakeStore:
    """Dict-backed store with the three calls the script uses."""

    def __init__(self, objects: dict[str, bytes] | None = None, corrupt_on_put: bool = False):
        self.objects = dict(objects or {})
        self.corrupt_on_put = corrupt_on_put
        self.puts: list[tuple[str, str]] = []

    def get(self, key: str) -> bytes | None:
        return self.objects.get(key)

    def put(self, key: str, data: bytes, content_type: str) -> None:
        self.puts.append((key, content_type))
        self.objects[key] = data + b"x" if self.corrupt_on_put else data

    def keys(self) -> list[str]:
        return sorted(self.objects)


def row(key: str, data: bytes, content_type: str = "application/pdf") -> mos.Row:
    return mos.Row(storage_key=key, checksum=digest(data), content_type=content_type)


def test_all_copied() -> None:
    source = FakeStore({"a": b"one", "b": b"two"})
    target = FakeStore()
    report = mos.migrate([row("a", b"one"), row("b", b"two")], source, target)
    assert (report.copied, report.already_present, report.missing, report.mismatched) == (
        ["a", "b"],
        [],
        [],
        [],
    )
    assert target.objects == {"a": b"one", "b": b"two"}
    assert target.puts == [("a", "application/pdf"), ("b", "application/pdf")]
    assert report.orphans == []
    assert report.ok


def test_already_present_is_not_rewritten() -> None:
    source = FakeStore({"a": b"one"})
    target = FakeStore({"a": b"one"})
    report = mos.migrate([row("a", b"one")], source, target)
    assert report.already_present == ["a"]
    assert report.copied == []
    assert target.puts == []
    assert report.ok


def test_already_present_needs_no_source_object() -> None:
    report = mos.migrate([row("a", b"one")], FakeStore(), FakeStore({"a": b"one"}))
    assert report.already_present == ["a"]
    assert report.ok


def test_missing_in_source() -> None:
    report = mos.migrate([row("a", b"one")], FakeStore(), FakeStore())
    assert report.missing == ["a"]
    assert report.copied == []
    assert not report.ok


def test_source_checksum_mismatch_is_not_written() -> None:
    source = FakeStore({"a": b"tampered"})
    target = FakeStore()
    report = mos.migrate([row("a", b"one")], source, target)
    assert report.mismatched == ["a"]
    assert target.objects == {}
    assert not report.ok


def test_mismatch_after_write() -> None:
    source = FakeStore({"a": b"one"})
    report = mos.migrate([row("a", b"one")], source, FakeStore(corrupt_on_put=True))
    assert report.mismatched == ["a"]
    assert report.copied == []
    assert not report.ok


def test_target_with_wrong_bytes_is_overwritten_from_source() -> None:
    source = FakeStore({"a": b"one"})
    target = FakeStore({"a": b"stale"})
    report = mos.migrate([row("a", b"one")], source, target)
    assert report.copied == ["a"]
    assert target.objects["a"] == b"one"


def test_orphans_reported_only() -> None:
    source = FakeStore({"a": b"one", "stray": b"zzz"})
    target = FakeStore()
    report = mos.migrate([row("a", b"one")], source, target)
    assert report.orphans == ["stray"]
    assert "stray" not in target.objects
    assert report.ok


def test_rerun_reports_everything_already_present() -> None:
    source = FakeStore({"a": b"one", "b": b"two"})
    target = FakeStore()
    rows = [row("a", b"one"), row("b", b"two")]
    mos.migrate(rows, source, target)
    again = mos.migrate(rows, source, target)
    assert again.already_present == ["a", "b"]
    assert again.copied == []


@pytest.mark.parametrize(
    ("objects", "expected"),
    [({"a": b"one"}, 0), ({}, 1), ({"a": b"bad"}, 1)],
)
def test_exit_codes(objects: dict[str, bytes], expected: int) -> None:
    report = mos.migrate([row("a", b"one")], FakeStore(objects), FakeStore())
    assert mos.exit_code(report) == expected


def test_summary_has_the_counts_and_no_content(capsys: pytest.CaptureFixture[str]) -> None:
    report = mos.migrate([row("a", b"one")], FakeStore({"a": b"one", "o": b"x"}), FakeStore())
    mos.print_report(report)
    out = capsys.readouterr().out
    assert "copied: 1" in out
    assert "already-present-and-matching: 0" in out
    assert "missing-in-source: 0" in out
    assert "checksum-mismatch: 0" in out
    assert "read-or-write-error: 0" in out
    assert "orphans-in-source: 1" in out


def test_missing_environment_exits_2(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "DATABASE_URL",
        "SOURCE_ENDPOINT",
        "SOURCE_ACCESS_KEY",
        "SOURCE_SECRET_KEY",
        "SOURCE_BUCKET",
        "OBJECT_STORE_ENDPOINT",
        "OBJECT_STORE_ACCESS_KEY",
        "OBJECT_STORE_SECRET_KEY",
        "OBJECT_STORE_BUCKET",
    ):
        monkeypatch.delenv(name, raising=False)
    assert mos.main([]) == 2


def test_empty_database_with_source_objects_fails(capsys: pytest.CaptureFixture[str]) -> None:
    """A run against the wrong database (no rows, objects in the source) must not look fine."""
    report = mos.migrate([], FakeStore({"a": b"one", "b": b"two"}), FakeStore())
    assert report.orphans == ["a", "b"]
    assert not report.ok
    assert mos.exit_code(report) == 1
    mos.print_report(report)
    assert "no attachment rows" in capsys.readouterr().out


def test_empty_database_and_empty_source_is_fine() -> None:
    report = mos.migrate([], FakeStore(), FakeStore())
    assert report.ok
    assert mos.exit_code(report) == 0


def test_printed_lines_carry_attachment_id_or_hash_not_the_storage_key(
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Storage keys hold the patient id and file name (possible PHI); they are never printed."""
    key = "attachments/patient-123/uuid/secret-name.pdf"
    rows = [
        mos.Row(storage_key=key, checksum=digest(b"one"), content_type="x", attachment_id="att-1")
    ]
    orphan_key = "attachments/patient-999/uuid/other.txt"
    report = mos.migrate(rows, FakeStore({orphan_key: b"z"}), FakeStore())
    mos.print_report(report)
    out = capsys.readouterr().out
    assert "MISSING att-1" in out
    assert f"ORPHAN {hashlib.sha256(orphan_key.encode()).hexdigest()[:12]}" in out
    for secret in ("patient-123", "secret-name", "patient-999", "other.txt"):
        assert secret not in out


# --- TASK-196: moving attachments to a store under another SSE key, by copy --------------------


class KeyedStore(FakeStore):
    """A store whose objects can be read only with the key it was started with (SeaweedFS: 500)."""

    def __init__(self, key: str, objects: dict[str, bytes] | None = None, volume_key: str = ""):
        super().__init__(objects)
        self.key = key
        self.volume_key = volume_key or key  # the key the stored bytes were written under
        self.fail_put_after: int | None = None

    def get(self, key: str) -> bytes | None:
        if key in self.objects and self.key != self.volume_key:
            raise RuntimeError("InternalError 500")
        return super().get(key)

    def put(self, key: str, data: bytes, content_type: str) -> None:
        if self.fail_put_after is not None and len(self.puts) >= self.fail_put_after:
            raise RuntimeError("connection reset")
        super().put(key, data, content_type)


def _attachments() -> tuple[dict[str, bytes], list[Any]]:
    data = {
        "a/small.pdf": b"one",
        "a/empty.txt": b"",
        "b/large.bin": bytes(range(256)) * 4096,  # 1 MiB
        "c/clinical.png": b"\x89PNG" + b"x" * 100,
    }
    return data, [row(k, v) for k, v in data.items()]


def test_copy_to_a_store_under_the_new_key_keeps_every_byte_and_changes_nothing_in_the_source() -> (
    None
):
    data, rows = _attachments()
    source = KeyedStore("old-key", data)
    target = KeyedStore("new-key")
    before = dict(source.objects)
    report = mos.migrate(rows, source, target)
    assert report.ok and len(report.copied) == len(data)
    assert target.objects == data and source.objects == before
    assert not hasattr(mos.Store, "delete")  # the protocol has no way to delete from either store


def test_a_source_started_with_the_wrong_key_is_reported_by_id_and_writes_nothing(
    capsys: pytest.CaptureFixture[str],
) -> None:
    data, rows = _attachments()
    rows = [
        mos.Row(r.storage_key, r.checksum, r.content_type, f"att-{i}") for i, r in enumerate(rows)
    ]
    source = KeyedStore("not-the-volume-key", data, volume_key="old-key")
    target = KeyedStore("new-key")
    report = mos.migrate(rows, source, target)
    assert not report.ok and mos.exit_code(report) == 1
    assert sorted(report.errors) == sorted(data) and target.objects == {}
    mos.print_report(report)
    out = capsys.readouterr().out
    assert "read-or-write-error: 4" in out and "ERROR att-0" in out and "SOURCE_SSE_KEY" in out
    assert "small.pdf" not in out and "a/" not in out


def test_an_interrupted_copy_is_resumed_and_a_failure_does_not_stop_the_other_objects() -> None:
    data, rows = _attachments()
    source = KeyedStore("old-key", data)
    target = KeyedStore("new-key")
    target.fail_put_after = 2
    first = mos.migrate(rows, source, target)
    assert len(first.copied) == 2 and len(first.errors) == 2 and mos.exit_code(first) == 1
    target.fail_put_after = None
    second = mos.migrate(rows, source, target)
    assert len(second.already_present) == 2 and len(second.copied) == 2 and second.ok
    third = mos.migrate(rows, source, target)
    assert len(third.already_present) == 4 and third.copied == [] and third.ok
    assert target.objects == data


def test_a_target_store_on_the_wrong_volume_key_is_an_error_not_a_silent_overwrite() -> None:
    data, rows = _attachments()
    target = KeyedStore("new-key", {"a/small.pdf": b"stale"}, volume_key="another-key")
    report = mos.migrate(rows, KeyedStore("old-key", data), target)
    assert "a/small.pdf" in report.errors and not report.ok


def test_every_object_is_verified_after_the_copy() -> None:
    """Negative control: a copy that is not read back and compared would pass this silently."""
    data, rows = _attachments()
    report = mos.migrate(rows, KeyedStore("old-key", data), FakeStore(corrupt_on_put=True))
    assert len(report.mismatched) == len(data) and report.copied == [] and not report.ok


# --- S3Store adapter, with botocore's Stubber (no network) -------------------------------------


def _store() -> tuple[Any, Stubber]:
    store = mos.S3Store("http://127.0.0.1:1", "ak", "sk", "bkt")
    return store, Stubber(store._client)


def test_s3store_put_requests_aes256_and_content_type() -> None:
    store, stubber = _store()
    stubber.add_response(
        "put_object",
        {},
        {
            "Bucket": "bkt",
            "Key": "k",
            "Body": ANY,
            "ContentType": "application/pdf",
            "ServerSideEncryption": "AES256",
        },
    )
    with stubber:
        store.put("k", b"data", "application/pdf")
        stubber.assert_no_pending_responses()


@pytest.mark.parametrize("code", ["NoSuchKey", "404", "NotFound"])
def test_s3store_get_maps_missing_object_to_none(code: str) -> None:
    store, stubber = _store()
    stubber.add_client_error("get_object", service_error_code=code)
    with stubber:
        assert store.get("k") is None


def test_s3store_get_reraises_other_errors() -> None:
    from botocore.exceptions import ClientError

    store, stubber = _store()
    stubber.add_client_error("get_object", service_error_code="AccessDenied")
    with stubber, pytest.raises(ClientError):
        store.get("k")


def test_s3store_get_returns_bytes() -> None:
    import io

    from botocore.response import StreamingBody

    store, stubber = _store()
    stubber.add_response(
        "get_object", {"Body": StreamingBody(io.BytesIO(b"abc"), 3)}, {"Bucket": "bkt", "Key": "k"}
    )
    with stubber:
        assert store.get("k") == b"abc"


def test_s3store_keys_paginates() -> None:
    store, stubber = _store()
    stubber.add_response(
        "list_objects_v2",
        {"Contents": [{"Key": "a"}], "IsTruncated": True, "NextContinuationToken": "t"},
        {"Bucket": "bkt"},
    )
    stubber.add_response(
        "list_objects_v2",
        {"Contents": [{"Key": "b"}], "IsTruncated": False},
        {"Bucket": "bkt", "ContinuationToken": "t"},
    )
    with stubber:
        assert store.keys() == ["a", "b"]
