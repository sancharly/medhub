# TASK-116 — Clinical data re-keying into the anonymized dataset (remediation)

- **Phase:** 9 — Integration, system testing, compliance hardening
- **Software item / unit:** SI-IDENTITY (`U-ID-Erasure`, extends TASK-035/035a); also touches
  SI-WORKER (`U-WK-RetentionErase`, TASK-036) for the object-store cleanup addition
- **Implements:** ADR-0013 (clinical/attachment re-keying — the field-level anonymization mapping the ADR
  explicitly leaves as an implementation detail); SR-024 AC-4; closes the deferred acceptance criterion in
  TASK-035a
- **Depends on:** TASK-035a (defines the deferral this task closes), TASK-036 (retention-erase worker this
  task extends), TASK-045 (attachment upload / `ObjectStorageClient`, already merged). `ClinicalRepository`
  and `AttachmentRepository` already exist (TASK-044/045) — no dependency needed on their creation.
- **Branch:** `feature/clinical-data-rekeying`
- **Status:** Not started
- **Source:** `TASK-035a-erasure-retrieval-delivery.md` — deferred AC: "Clinical data is anonymized/re-keyed
  into the dataset (not silently dropped)." The original deferral reason ("no ClinicalEntry repo
  available") is stale — `ClinicalRepository`/`AttachmentRepository` exist and are used elsewhere.

## Objective

`ErasureService._erase()` (`backend/app/identity/erasure.py:67-131`) severs Account PII and creates an
`AnonymizedDataset` row, but the `payload` only ever contains
`{"original_user_type": ..., "erasure_requested_at": ...}` — no clinical content is queried or copied.
This violates ADR-0013's decision that "the user's clinical/record data is re-keyed to an opaque
anonymized dataset that carries no identifiers back to the natural person," not silently dropped.

This task implements that re-keying: for an erased patient, copy their `ClinicalEntry` and `Attachment`
records into `AnonymizedDataset.payload` per the field-level mapping below, delete the original rows and
object-storage binaries once the copy is committed, and extend TASK-036's retention-erase worker so the
re-keyed object-storage binaries are cleaned up when a dataset is permanently erased at the 5-year
deadline.

**This task does not change ADR-0013's decided mechanism** (sever PII, high-entropy retrieval code,
salted-hash-only storage, 5-year retention, self-service retrieval, scheduled permanent erasure). It only
fills in the field-level anonymization mapping, which ADR-0013 itself explicitly defers to implementation
(its "Neutral" consequences section: *"the precise field-level anonymization mapping are implementation
details... this ADR fixes the mechanism and policy, not the parameters"*).

## Interfaces to honor

- `ClinicalRepository.list_for_patient_ordered(patient_id)` (`backend/app/db/repositories/clinical_repo.py`)
  — query the patient's clinical entries.
- `AttachmentRepository.list_for_clinical_entry(clinical_entry_id)`
  (`backend/app/db/repositories/attachment_repo.py`) — query attachments per entry.
- `ObjectStorageClient` (`backend/app/core/object_storage.py`) — `get_object`/`put_object`/`delete_object`,
  already used by `AttachmentService` (`backend/app/attachments/service.py`), reused here for binary
  copy/delete.
- `AnonymizedDataset.payload` (`backend/app/db/models/anonymized_dataset.py`) — existing JSONB column;
  extended, not replaced. No new table, no migration.
- `ErasureService._erase()` — the integration point; gains new constructor dependencies
  (`ClinicalRepository`, `AttachmentRepository`, `ObjectStorageClient`) and a new private helper for
  re-keying.
- TASK-036's retention-erase worker (the daily Celery Beat job that deletes `AnonymizedDataset` rows past
  `retention_deadline`) — extended to also delete re-keyed object-storage binaries.

## Field-level anonymization mapping

### `ClinicalEntry` → payload

| Field | Disposition |
|---|---|
| `id` | Severed — no original id preserved in the payload |
| `patient_id` | Severed — never appears in the payload, not even hashed (a hash of a UUID FK is trivially reversible against the account table) |
| `author_doctor_id` | **Dropped entirely.** ADR-0013's bar is "no identifiers back to the natural person" (the patient); doctor-id + timestamp is a realistic quasi-identifier that could help re-link to the patient, and no current consumer of the retrieved payload needs the treating doctor's identity. |
| `occurred_at` | Generalized to month granularity (e.g. `"2026-05"`), never the exact timestamp — exact timestamps are a classic quasi-identifier when combined with any external record |
| `description` | Retained verbatim (decrypted, stored as a plain JSON string) — this is the clinical content the acceptance criterion exists to preserve |

**Known limitation (explicitly not solved by this task):** free-text `description` may itself contain
embedded identifiers (e.g. a clinician typed a family member's name into a note). NLP-based redaction of
free text is out of scope — a much larger, separate feature. State this limitation in the erasure
confirmation flow's documentation if not already covered elsewhere; do not claim the payload is scrubbed
of all possible embedded identifiers.

### `Attachment` → payload (nested under its parent entry)

| Field | Disposition |
|---|---|
| `id`, `clinical_entry_id`, `patient_id` | Severed; the entry/attachment grouping is preserved structurally (attachments nested inside their parent entry's JSON object) instead of via a live FK |
| `filename` | Severed/genericized — original filenames routinely embed patient name or MRN (e.g. `SmithJ_CT_20260512.dcm`) |
| `content_type`, `size`, `checksum` | Retained as-is — not identifying, needed to interpret the binary |
| `storage_key` | The binary is **copied** to a new, non-patient-derived key (`anonymized/{dataset_id}/{uuid4()}`) via `ObjectStorageClient`; the new key is what's stored in the payload. The original key (format `attachments/{patient_id}/{uuid4()}/{filename}` per `backend/app/attachments/service.py:78`, which embeds `patient_id` directly) is deleted once the copy is verified. |
| `dicom_metadata` | Filtered through a strict **allow-list** (e.g. `Modality`, `StudyDescription`, `BodyPartExamined`), never retained wholesale — DICOM tags routinely carry `PatientName`/`PatientID`/`InstitutionName` even in files already believed "de-identified" |

### Payload location

Extend the existing `AnonymizedDataset.payload` JSONB — no new table, no migration. `retrieve_anonymized`
already reads the payload whole; there is no query requirement to filter/join clinical entries
independently of their dataset, so a new table would add migration/repository/FK-cascade complexity for
zero query benefit.

Example resulting payload shape:

```json
{
  "original_user_type": "PATIENT",
  "erasure_requested_at": "2026-07-01T12:00:00+00:00",
  "clinical_entries": [
    {
      "occurred_at_month": "2026-05",
      "description": "Follow-up for hypertension, BP stable at 128/82...",
      "attachments": [
        {
          "content_type": "application/dicom",
          "size": 4213112,
          "storage_key": "anonymized/9f1c.../a83e....dcm",
          "checksum": "sha256:...",
          "dicom_metadata": {"Modality": "CT", "BodyPartExamined": "CHEST"}
        }
      ]
    }
  ]
}
```

No `id`, `patient_id`, or `author_doctor_id` anywhere in the structure.

## Implementation detail

- **Deletion of originals (required for genuine anonymization, not optional cleanup):** leaving the
  original `ClinicalEntry`/`Attachment` rows in place would mean the full clinical record stays directly
  queryable via `patient_id` against the still-existing (renamed, not deleted) Account row — completely
  bypassing the retrieval-code gate ADR-0013 relies on as the *only* path to this data post-erasure. That
  is renaming, not anonymizing. Therefore: after the `AnonymizedDataset` row is created and **committed**
  with the full re-keyed payload, delete (in FK order — `Attachment` rows before `ClinicalEntry` rows) the
  originals for that patient. Delete the original object-storage binaries only after their copies are
  confirmed, and only after the DB transaction commits successfully — this ordering avoids data loss if
  any step fails partway (a failed transaction must never leave copies-only-partial with originals already
  gone).
- Extend `ErasureService.__init__` with `clinical_repo: ClinicalRepository`, `attachment_repo:
  AttachmentRepository`, `object_storage: ObjectStorageClient`.
- Add a private helper, e.g. `_rekey_clinical_data(patient_id) -> list[dict]`, called from `_erase()`
  before/alongside the existing payload construction:
  1. `self._clinical_repo.list_for_patient_ordered(patient_id)`.
  2. Per entry, `self._attachment_repo.list_for_clinical_entry(entry.id)`.
  3. Build the field-mapped dict per the tables above; copy each attachment binary to a new object-store
     key via a `_rekey_attachment_binary` helper.
  4. Return the nested list; `_erase()` assigns it into `payload["clinical_entries"]`.
  5. After the `AnonymizedDataset` is committed, delete the original `Attachment` rows, then the original
     `ClinicalEntry` rows, then the original object-storage keys.
- **Object-storage cleanup at permanent-erasure time:** locate TASK-036's retention-erase worker (the
  daily Celery Beat task that finds `AnonymizedDataset` rows past `retention_deadline` and deletes them)
  and extend it so that, before/alongside deleting the DB row, it iterates the dataset's payload
  (`clinical_entries[].attachments[].storage_key`) and calls `ObjectStorageClient.delete_object` for each
  re-keyed key, using the same per-dataset failure isolation the worker already has. TASK-036's own audit
  note anticipated exactly this follow-up: "object-store binaries not handled (vacuous until 035 re-key)."

## Tests (write first — TDD, CLAUDE.md §4)

Per this repo's audit history, mock-only tests are the recurring root cause of false-confidence
"Completed" tasks. The tests for this task **must exercise real `ClinicalRepository`/`AttachmentRepository`
queries against a real DB session** (following `backend/tests/db/test_repositories.py`'s fixture pattern),
not `MagicMock()` for those two repos — a broken join or a wrong FK filter must actually fail the test.

New/extended tests (likely `backend/tests/identity/test_erasure.py` plus a real-DB fixture):

- **Positive — data preserved:** after erasing a patient with a seeded `ClinicalEntry` + `Attachment`,
  `AnonymizedDataset.payload["clinical_entries"]` contains the entry's `description` and the attachment's
  `content_type`/`size`/`checksum`.
- **Negative — patient identifier absent:** the patient's UUID string does not appear anywhere in
  `json.dumps(payload)`.
- **Negative — doctor identifier absent:** the doctor's UUID string does not appear anywhere in
  `json.dumps(payload)`.
- **Negative — original storage key absent:** the original `storage_key` (which embeds `patient_id`) is
  not present in the payload and no longer resolves in the (fake/test) object store; a new key holds the
  same bytes.
- **Negative — timestamp generalized:** `occurred_at` appears only as a month-granularity string, never a
  full ISO timestamp.
- **Originals deleted:** after erasure, `ClinicalRepository.list_for_patient(patient_id)` and
  `AttachmentRepository.list_for_clinical_entry(...)` for the erased entries return empty.
- Extend `backend/tests/workers/test_retention_erase.py`: a dataset whose payload references re-keyed
  `storage_key`s past its deadline → after the sweep, those keys no longer exist in the fake object store.

Each test names the SR-024/ADR-0013 requirement it verifies.

## Acceptance criteria

- [ ] Clinical entries and attachments for an erased patient are copied into `AnonymizedDataset.payload`
  with the field-level mapping above; no clinical content is silently dropped (SR-024 AC-4, ADR-0013).
- [ ] No patient or doctor identifier (UUID, name, original filename, original storage key) appears
  anywhere in the anonymized payload.
- [ ] Original `ClinicalEntry`/`Attachment` DB rows and original object-storage binaries are deleted only
  after the re-keyed copy is committed successfully.
- [ ] TASK-036's retention-erase worker deletes re-keyed object-storage binaries when it permanently
  erases a dataset past its 5-year deadline.
- [ ] Known limitations (free-text content may embed identifiers; `ConsentGrant`/`Appointment` rows retain
  `patient_id`/`doctor_id` FKs to the renamed account — see "Known limitations" below) are documented, not
  silently left unaddressed.

## Known limitations (explicitly out of scope for this task)

- **Free-text content:** `description` is retained verbatim; a clinician-entered identifier embedded in
  free text (e.g. a family member's name) survives anonymization. This is a pre-existing characteristic of
  free-text clinical notes, not something re-keying is expected to fix.
- **Residual relational linkage:** `ConsentGrant` and `Appointment` rows still carry `patient_id`/
  `doctor_id` foreign keys to the renamed (not deleted) Account after erasure. TASK-035a's deferred
  acceptance criterion was specifically about *clinical* data, so this task is scoped to `ClinicalEntry`/
  `Attachment` only. This residual linkage is a related but separate gap and is **not** solved by this
  task — flagged here so it is not mistaken for solved.

## Definition of Done

- [ ] Lint + type-check pass (`ruff`, `mypy`)
- [ ] Real-DB-backed tests (not mock-only for `ClinicalRepository`/`AttachmentRepository`) cover every
  positive/negative case above; full backend suite green
- [ ] Traceability matrix row added (ADR-0013 / SR-024 → TASK-116 → tests) in
  `docs/design/traceability-matrix.md`
- [ ] Security review completed — confirm no identifier leakage via the negative-assertion tests above
- [ ] **Once this task's acceptance criteria and Definition of Done are met, TASK-035a's deferred
  acceptance-criteria checkbox — "Clinical data is anonymized/re-keyed into the dataset (not silently
  dropped)" — is checked off in `docs/implementation-plan/phase-2-auth-identity/TASK-035a-erasure-retrieval-delivery.md`,
  and TASK-035a's entry is re-confirmed as fully Completed with no remaining deferred items.**
