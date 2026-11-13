"""TC-013.14 — test PostgreSQL containers start from the SOUP-020 reference (SR-028 AC-9)."""

from postgres_image import POSTGRES_IMAGE

SOUP_020_DIGEST = "sha256:9e2cf6287f25c3151f4c9421ccce2b17f3e60061c111a29165e0d2cdd9ff0a97"


def test_pinned_reference_carries_the_soup_020_digest() -> None:
    assert ":16.15@" in POSTGRES_IMAGE
    assert POSTGRES_IMAGE.endswith("@" + SOUP_020_DIGEST)


def test_started_container_image_carries_the_soup_020_digest(pg_container) -> None:
    image = pg_container.get_wrapped_container().image
    assert any(d.endswith(SOUP_020_DIGEST) for d in image.attrs["RepoDigests"])
