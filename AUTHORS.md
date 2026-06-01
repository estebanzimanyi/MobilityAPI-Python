# Authors

MobilityAPI is the result of contributions from several individuals across two phases. The project's lineage starts with **pg_mfserv** (2024), an OGC API – Moving Features prototype that established the Python-server skeleton and the PyMEOS-based MobilityDB integration pattern. **MobilityAPI** (2025–) extends that foundation into a production-grade implementation with a structured resource layout, comprehensive tests, and OGC conformance.

## Founding phase (2024) — as `pg_mfserv`

Affiliated with [Université libre de Bruxelles (ULB)](https://www.ulb.be/).

- **Maxime Schoemans** ([@mschoema](https://github.com/mschoema)) — initial commit, OGC API – Moving Features endpoint design, project skeleton.
- **Victor Morabito** ([@MrMaxime1er](https://github.com/MrMaxime1er)) — main developer of pg_mfserv: column discovery, request/response handling, exception handling, route refactors, feature endpoints (collections, items, temporal geometry, temporal properties).

The pg_mfserv repository is preserved at [`MobilityDB/pg_mfserv`](https://github.com/MobilityDB/pg_mfserv) in archived form.

## Current phase (2025–) — as `MobilityAPI`

Affiliated with [Université libre de Bruxelles (ULB)](https://www.ulb.be/).

- **Sirine Meraoui** ([@sirimeraoui](https://github.com/sirimeraoui)) — current maintainer; structured resource layout (`resource/` tree); test infrastructure; OGC conformance; HTTP-status-code translation; documentation; demo notebooks; AIS dataset integration.

## Acknowledgements

The project benefits from the broader [MEOS ecosystem](https://libmeos.org/), in particular:

- **[PyMEOS](https://github.com/MobilityDB/PyMEOS)** — the Python binding of MEOS that MobilityAPI consumes today.
- **[MobilityDB](https://github.com/MobilityDB/MobilityDB)** — the PostgreSQL extension providing the SQL surface backing MobilityAPI.
- **[OGC API – Moving Features Standard](https://docs.ogc.org/is/22-003r3/22-003r3.html)** — the standard MobilityAPI implements.
