#!/usr/bin/env bash
# Prints the head revision of an Alembic versions directory, read from the migration files.
# Accepts `revision = "x"`, `revision: str = 'x'` and a tuple `down_revision` (a merge). Exits 1,
# printing why on stderr, when there is not exactly one head or when the number of revisions found
# differs from the number of migration files (a form this parser does not understand).
# Used by smoke-test.sh (PRB-062); tested by infra/tests/test_alembic_head.py.
set -uo pipefail
DIR="${1:?usage: alembic-head.sh <versions dir>}"
FILES=$(ls "$DIR"/[0-9]*.py 2>/dev/null | wc -l | tr -d ' ')
RESULT=$(awk '
    function quoted(line,   out, m) {
        out = ""
        while (match(line, /["\x27][^"\x27]+["\x27]/)) {
            m = substr(line, RSTART + 1, RLENGTH - 2)
            out = out " " m
            line = substr(line, RSTART + RLENGTH)
        }
        return out
    }
    /^revision[ \t]*(:[^=]*)?=/ { split(quoted($0), a, " "); if (a[1] != "") { rev[a[1]] = 1; n++ } }
    /^down_revision[ \t]*(:[^=]*)?=/ { c = split(quoted($0), a, " "); for (i = 1; i <= c; i++) down[a[i]] = 1 }
    END {
        for (r in rev) if (!(r in down)) { heads++; head = r }
        print n + 0, heads + 0, head
    }' "$DIR"/[0-9]*.py)
read -r FOUND HEADS HEAD <<<"$RESULT"
if [ "$FOUND" != "$FILES" ]; then
    echo "found $FOUND revisions in $FILES migration files" >&2
    exit 1
fi
if [ "$HEADS" != "1" ]; then
    echo "expected one head revision, found $HEADS" >&2
    exit 1
fi
echo "$HEAD"
