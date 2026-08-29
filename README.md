---
title: A11oy Factory
emoji: ⚖️
colorFrom: yellow
colorTo: gray
sdk: docker
app_port: 7860
pinned: false
license: apache-2.0
short_description: A11oy vertical factory control plane — Decision Cell Compiler, Lyte admitted, frontier N1–N8.
---

# A11oy Factory

Public source for the **A11oy vertical factory control plane**.

This is **not a second flagship** and not a new product name. It binds as an A11oy package: one Decision Cell Compiler, seven vertical cells, owner-approved green light.

| Surface | State |
| --- | --- |
| GitHub | [szl-holdings/a11oy-factory](https://github.com/szl-holdings/a11oy-factory) · public |
| Hugging Face Space | `SZLHOLDINGS/a11oy-factory` · Docker prepared, **not live** until `HF_TOKEN` is set |
| a-11-oy.com | **not certified** by this repository |
| Lyte | admitted protected design-partner cell |
| Killinchu | only public synthetic reference |
| Formulas | locked-8 · never grant authority |

## Owner order

`AO-2026-08-29-001` is APPROVED.

- Admission freeze lifted for factory internals
- `szl-holdings/nexus` classified `A11OY_INCUBATOR_PACKAGE`
- Frontier N1–N8 open
- Production certificate of a-11-oy.com remains closed

## Run

```bash
npm ci
npm run typecheck
npm run build
npm run dev
```

Auth is off. Database is PGLite in preview, Neon when `DATABASE_URL` is set.

## Hugging Face

This README is a Docker Space card. Publishing the Space requires a Hub token this runtime does not have.

1. Create Space `SZLHOLDINGS/a11oy-factory` (Docker, port 7860)
2. Add GitHub secret `HF_TOKEN`
3. Run workflow **Sync Hugging Face Space**

Until that token exists, Hub visibility is unchanged.

## Honest contract

`GET /api/a11oy/v1/honest` · `GET /api/a11oy/v1/admission` · `GET /readyz` returns 503 while `production_ready` is false.
