# State Contract — kb-creator owns `state.kb`

Reference: C-13a frozen contract (`.jr-orchestrator-state.json` v2, §4.2 I/O matrix).

---

## 1. Schema slice

kb-creator is the **sole writer** of the `kb` object inside `.jr-orchestrator-state.json`.
It NEVER touches `step`, `owner`, `roadmap`, `skills`, or `agents`.

```json
{
  "version": 2,
  "kb": {
    "created_by": "kb-creator",
    "source": "ingest | interactive",
    "discovery": {
      "problem":      "<one-sentence description of the core problem being solved>",
      "system_type":  "<web_app | api | cli | mobile | saas_multi_tenant | ...>",
      "domain":       "<business domain, e.g. ecommerce, fintech, logistics>",
      "scale":        "<single_user | team | public_multi_user | multi_tenant>",
      "stack":        "<primary technologies, e.g. FastAPI + React + Postgres>",
      "needs_infra":  true
    },
    "files": [
      "knowledge-base/01_vision_y_objetivos.md",
      "knowledge-base/02_descripcion_general.md",
      "..."
    ]
  }
}
```

Fields:
| Field | Type | Description |
|---|---|---|
| `created_by` | string | Always `"kb-creator"` — identifies the writer. |
| `source` | enum | How the KB was built: `"ingest"` (Mode A) or `"interactive"` (Mode B). |
| `discovery` | object | Six-field project discovery (see §3). |
| `files` | string[] | Paths of every `knowledge-base/*.md` written (canonical + optional extras). |

---

## 2. Conditional write algorithm

Run this hook **after** `knowledge-base/` is fully written, before returning to the user.

```
1. Check project root for `.jr-orchestrator-state.json`
   ├─ ABSENT  → no-op. Do NOT create the file. Done.
   ├─ PRESENT, version != 2 → surface one-line note:
   │    "State file is not v2, skipping state update."
   │    Continue. Done.
   └─ PRESENT, version == 2 → update ONLY state.kb:
        • Set created_by: "kb-creator"
        • Set source: (see §3 Mode→source mapping)
        • Set discovery: (see §4 inference / ask rules)
        • Set files: list of all knowledge-base/*.md paths written
        Write the file back. Done.
```

**Why never create**: the orchestrator (jr-orchestrator) is the sole creator of the state file (C-13a D3). kb-creator updating-only avoids two writers racing to create it.

**Why strictly conditional**: kb-creator is a public standalone skill. Forcing a state file on every direct invocation would regress standalone projects and pollute non-orchestrated repos.

---

## 3. Mode → `source` mapping

| Existing mode | `state.kb.source` | Rationale |
|---|---|---|
| **Mode A** (silent, from `docs/`) | `"ingest"` | KB built from existing user-supplied documents — maps to the contract's "ingest" definition. |
| **Mode B** (interactive, from scratch) | `"interactive"` | KB built via strategic Q&A discovery — maps to the contract's "interactive". |

**Dominant-origin rule (mixed runs)**: a run that started from `docs/` (Mode A trigger) resolves to `"ingest"` even if some gaps were later clarified by questions. The origin of the bulk of the content determines `source`. A pure from-scratch run is always `"interactive"`. The enum is frozen at `ingest | interactive`; no third value is introduced.

---

## 4. Discovery-field population

### Mode B (interactive) — ASKED

All six fields are obtained from the user's strategic Q&A answers. Map question → field:

| Discovery field | Sourced from |
|---|---|
| `problem` | P1 (Visión y problema raíz) |
| `system_type` | P0-sys (¿Qué tipo de sistema es?) — see `strategic-questions.md` §P0-sys |
| `domain` | P3 (Actores principales → business domain inferred) |
| `scale` | P0-scale (¿A qué escala opera?) — see `strategic-questions.md` §P0-scale |
| `stack` | P4 (Restricciones técnicas no negociables → stack) |
| `needs_infra` | P4 sub-questions (Cloud, on-prem, DB, queues → boolean) |

After collecting answers, record the values in `state.kb.discovery` before returning.

### Mode A (ingest) — INFERRED from source docs

Mode A is fire-and-forget (no questions). Inference rules per field:

| Field | Infer from | Signal to look for |
|---|---|---|
| `problem` | `01_vision_y_objetivos.md` (generated) | Vision / objective statement — the first declarative sentence about what the system solves. |
| `system_type` | `02_descripcion_general.md` (generated) | Architecture / overview section — keywords: "web app", "REST API", "CLI", "mobile", "SaaS", "multi-tenant". |
| `domain` | `03_actores_y_roles.md` + `06_funcionalidades.md` | Business domain implied by actor names + feature groupings (ecommerce → products/cart/checkout; fintech → transactions/ledger). |
| `scale` | `03_actores_y_roles.md` + any scale/RBAC mentions | "single user" / "team" / "public" / "multi-tenant" — infer from actor count, RBAC complexity, or scale keywords in the docs. |
| `stack` | `02_descripcion_general.md` | Technology names (frameworks, languages, database, external services). |
| `needs_infra` | `02_descripcion_general.md` + `08_arquitectura_propuesta.md` | Boolean: `true` if docs mention Docker, a database, Redis, message queues, cron jobs, or specific deployment infra. |

### Low-confidence rule (Mode A)

**Never invent** a confident discovery value. When a field cannot be inferred with reasonable confidence:

1. Set a best-effort value clearly marked as uncertain (e.g. `"web_app (inferred, low confidence)"`).
2. Add an entry to `10_preguntas_abiertas.md`:
   ```
   [DISCOVERY] `<field>` could not be inferred with confidence from the source docs.
   Please confirm: <what you need to know>.
   ```
3. Continue — never block Mode A on a single uncertain field.
