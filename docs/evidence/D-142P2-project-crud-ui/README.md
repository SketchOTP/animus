# D-142P2 — Animus UI Project CRUD Wiring

Wires D-142P1 project editor to governance API (`POST /projects`, `POST /projects/{id}/update`).

## Verification

```bash
pytest -q tests/test_command_center_d140.py tests/test_command_center_d141.py tests/test_command_center_d142p2.py
```
