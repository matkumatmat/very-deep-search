# Package: cover crops and soil organic carbon

Contract: quota 3 (3 per source); sources: CROSSREF.
Over-gather ratio: 1.5.

## Contents

- README.md
- contract.json
- evidence/apsoil-2008.json
- evidence/geoderma-2024.json
- evidence/soil-2024.json
- excluded-from-final.md
- final.jsonl
- manifest.jsonl
- merged.jsonl
- needs-richer-check.jsonl

Not provided: disputes.md.

## Counts

final pass records: 3
manifest rows: 3
evidence files: 3

## Reproduce

From this directory, with vds.py available:

    vds.py validate final.jsonl --root .

Then run each record's reverify commands and compare against its evidence file under evidence/.
