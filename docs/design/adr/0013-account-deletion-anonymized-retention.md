# ADR-0013: Account deletion via 5-year anonymized retention with a user-held retrieval code

## Status

Accepted

## Context

SR-034.5 and SR-024 require that, on account deletion (including a GDPR Article 17 erasure request), the user's authentication credentials and personal identifying information are removed while clinical records are **anonymized rather than silently erased**, reconciled with a documented retention policy (SR-024 AC-4, SR-034.5). The retention policy is now decided: when a user requests deletion of their account and data, the data is **retained in anonymized form for 5 years** so the (now-anonymous) data subject can still retrieve their own dataset within that window, after which it is **permanently erased**.

The stakeholder constraint that shapes the design: the user must be able to retrieve their retained dataset using a **single anonymization code** issued at deletion time, and **that code must not be stored anywhere in the system** — only the user holds it. The system must therefore be able to *locate and authorize* retrieval of the correct anonymized dataset from a presented code without ever holding the code in recoverable form. This is the same security posture as password storage (SR-002.4, Argon2id) and credential handling generally (ADR-0011): store a one-way derivation, never the secret.

## Decision

Deletion becomes an **anonymization-and-retention** operation in `SI-IDENTITY` (`U-ID-Erasure`), executed after the SR-034.6 confirmation step:

1. **Sever PII from record data.** The user's authentication credentials and personal identifying information are removed (SR-034.5); the user's clinical/record data is re-keyed to an opaque **anonymized dataset** that carries no identifiers back to the natural person. The email address is released for reuse (SR-034.7).

2. **Generate a high-entropy anonymization code** (>= 128 bits from a CSPRNG) that is the user's sole handle to that anonymized dataset. The code is **sent to the user** (email, at deletion time) and is **never persisted in recoverable form**.

3. **Store only a one-way lookup/verification value, never the code.** The anonymized dataset row stores a **salted hash of the code** (Argon2id / a KDF, consistent with ADR-0011 credential handling) used to *locate-and-authorize* retrieval. On retrieval the user presents the code; the system derives the same value and matches it to the dataset. The code itself is never written to the database, logs, or audit records (the audit entry records that a deletion/retrieval occurred and against which anonymized dataset id, never the code — SR-023, SR-024 AC-3).

4. **Set a 5-year retention deadline** on the anonymized dataset. A scheduled job (`SI-WORKER`) **permanently and irreversibly erases** the dataset once the deadline passes.

5. **Self-service retrieval within 5 years.** A presented valid code authorizes the holder to retrieve the anonymized dataset; the retrieval is audited.

**Security trade-off (explicit and by design):** because the code is never stored, **losing the code makes the anonymized dataset unrecoverable** — there is no recovery, reset, or administrative back-channel. This is the intended privacy property (the operator cannot re-identify or hand over the data subject's dataset without the data subject's code), accepted as the cost of the no-stored-secret guarantee. The salted hash provides locate-and-authorize without enabling brute-force re-identification, given the high-entropy code.

## Consequences

### Positive

- Satisfies SR-024/SR-034.5 (anonymize, do not silently erase) with a concrete, documented retention policy and an automatic erasure endpoint at 5 years (SR-024 AC-4).
- The no-stored-code design means a system or operator compromise cannot re-identify or surrender a deleted user's dataset — a strong GDPR data-minimization and privacy posture (NFR-004, NFR-007).
- Reuses an already-vetted primitive (salted KDF hash, ADR-0011) rather than introducing new crypto.
- Retrieval and erasure are auditable side effects, preserving the audit chain (SR-023).

### Negative

- **Irrecoverable on lost code** — no recovery path by design; this must be made clear to the user at deletion time (UX/consent text).
- A scheduled erasure job and a retention-deadline field add a small amount of lifecycle machinery to `SI-IDENTITY`/`SI-WORKER`.
- "Anonymization" must be implemented carefully (sever all back-references / quasi-identifiers) to be true anonymization and not mere pseudonymization; this is a verification obligation.

### Neutral

- The exact KDF parameters and the precise field-level anonymization mapping are implementation details captured in the persistence design (`U-PER-Crypto`, `U-PER-Models`); this ADR fixes the *mechanism and policy*, not the parameters.

## Alternatives Considered

**Store the code (or a reversible token) server-side.** Rejected: it would let the operator re-identify/retrieve a deleted user's data, defeating the privacy goal and the stakeholder constraint that only the user holds the code.

**Hard-delete everything on request (no retention).** Rejected: violates SR-024 AC-4 / SR-034.5 (clinical records anonymized, not silently erased) and removes the user's ability to retrieve their own dataset within the window.

**Indefinite retention.** Rejected: contrary to GDPR storage-limitation; a bounded 5-year window with automatic erasure is the storage-limitation control.

## References

- Requirements: SR-024, SR-034, SR-023; NFR-004, NFR-007
- Related: ADR-0006, ADR-0011, ADR-0012; sections 06.7, 08.5
