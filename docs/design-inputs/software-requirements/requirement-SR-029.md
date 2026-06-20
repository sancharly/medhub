# SR-029 Account lockout after failed login attempts

## Summary

The system shall lock a user account after 5 consecutive failed login attempts for 30 minutes, aligned with IEC 62443-3-3:2013 SR 1.8 (Unsuccessful login attempts) at Security Level 2.

## Description

Unlimited login attempts enable automated brute-force and credential-stuffing attacks. This requirement specifies the lockout trigger, duration, reset conditions, and audit obligations that limit the effectiveness of such attacks. The lockout threshold is set to 5 (rather than a stricter 3) to accommodate the higher rate of input errors typical in clinical environments while still providing effective protection. The lockout duration of 30 minutes provides a meaningful deterrent without requiring administrator intervention during time-critical clinical workflows.

## Acceptance Criteria

1. After **5 consecutive failed login attempts** on a single account, the account is locked. Attempts with an incorrect password and attempts with a non-existent username are treated identically to prevent username enumeration.
2. The lockout duration is **30 minutes** from the moment of the fifth failure. After the period elapses, the account is automatically re-enabled.
3. A system administrator can unlock an account manually before the 30-minute period ends.
4. The failed-attempt counter resets to zero on a successful login.
5. Each lockout event is recorded in the audit log (per SR-023) with: username (or attempted username), source IP address, and timestamp.
6. The login error message presented to the user does not distinguish between "account locked" and "invalid credentials" during the lockout period, to avoid disclosing account existence to an attacker.

## Origin Requirement

Derived from: Non-Functional Requirement NFR-007 "Cybersecurity".

## Risk Analysis

### Rationale

IEC 62443-3-3 SR 1.8 (SL 2) requires the system to limit login attempts to prevent automated guessing of credentials. Without a lockout mechanism, a patient's or clinician's account is vulnerable to brute-force and credential-stuffing attacks that could expose PHI or allow unauthorized clinical actions.

### Potential Risks

- **Security:** Absence of lockout allows unlimited automated credential guessing against accounts holding PHI.
- **Availability:** An overly aggressive threshold (e.g., 3 attempts) could lock out legitimate clinicians during time-critical care, creating a patient safety risk.
- **Compliance:** Lack of documented lockout policy conflicts with IEC 62443 SL 2 and MDR/FDA cybersecurity expectations.

### Control Measures

- Threshold of 5 attempts balances security with clinical-workflow usability; the 30-minute automatic re-enable avoids permanent denial-of-service without administrator action.
- Administrator manual unlock (criterion 3) provides an escape for genuine clinical emergencies.
- Audit logging of every lockout event (criterion 5) enables anomaly detection and forensic investigation.
- Error message non-disclosure (criterion 6) prevents attackers from learning valid usernames.

## Status

Approved

## Version History

Version 1.0 - Initial creation; split from combined SR-025
