"""The one PostgreSQL image every test that starts a database container uses.

SR-028 AC-9: the real-database and migration tests run against the shipped PostgreSQL
(SOUP-020), so their evidence applies to the deployed version. This reference must equal
the ``postgres`` service image in ``infra/docker-compose.yml`` (checked by TASK-213).

It lives beside ``conftest.py`` rather than in ``tests/`` because the DICOM module tests
have their own ``tests`` package, which shadows ``backend/tests`` on ``sys.path``. It is
not copied into the image (the Dockerfile copies only named directories).
"""

POSTGRES_IMAGE = (
    "postgres:16.15@sha256:9e2cf6287f25c3151f4c9421ccce2b17f3e60061c111a29165e0d2cdd9ff0a97"
)
