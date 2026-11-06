# Hugging Face Space configuration

These cards are the Space Release Compiler output from Packet 6
(2026-08-29). They are plans: no card in this directory configures or
publishes a Space by itself. Other Spaces publish from their own repositories
(the Packet 6 path was `szl-holdings/immune` workflow Mirror khipu Hub,
`secrets.HF_TOKEN`). The one Space this repository publishes is its own,
`SZLHOLDINGS/a11oy-factory`, and only through an operator dispatch of
`.github/workflows/hf-sync.yml` (see the root README).

## Canonical six plus factory bind

| Space | Planned visibility (2026-08-29) | Honesty |
| --- | --- | --- |
| SZLHOLDINGS/README | public | KEEP |
| SZLHOLDINGS/a11oy | public | flagship |
| SZLHOLDINGS/killinchu | public | KEEP (synthetic only) |
| SZLHOLDINGS/lyte-services | public hologram | BIND_AS_A11OY_PACKAGE · not a flagship |
| SZLHOLDINGS/szl-model-inference-lab | public | KEEP |
| SZLHOLDINGS/evidence-studio | public hologram | merge sink · one writer |
| SZLHOLDINGS/a11oy-factory | public hologram | compiler · not a second flagship |

The table is the plan, not observed Hub state. Observed 2026-11-06 (Hub
API): `a11oy`, `killinchu` and `szl-model-inference-lab` are public and
RUNNING; `README` and `a11oy-factory` are private; `lyte-services` and
`evidence-studio` do not exist on the Hub.

## Factory bind

`SZLHOLDINGS/a11oy-factory` is **BIND_AS_A11OY_PACKAGE**. It is not a second
flagship and not a new product name.

## Hub mutation

- Packet 6 counted 27 Spaces.
- Live org page on 2026-08-29 listed 36+.
- This factory does not scrape Hub and does not change visibility.
- GDW-X / gdw-frontier stays MODELED observability, not a Hub app.
- Research 404s stay GitHub repos, not empty Spaces.
