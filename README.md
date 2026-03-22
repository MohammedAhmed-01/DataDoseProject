# Pharmaceutical Data Intelligence Pipeline

Turn messy drug product CSVs into validated, FDA-enriched, Egypt-market-aware datasets.

---

## What this does

Raw pharmaceutical records are noisy. Trade names arrive with pack sizes, dosage form tokens, and random numeric prefixes baked in. Active ingredients aren't canonicalized. Nothing is verified against anything.

This pipeline fixes that. Two workflows, run independently or together:

**Ingredient intelligence** — splits combination APIs, validates each against WHO INN standards, queries OpenFDA for label data (brand names, warnings, adverse reactions), and keeps only what's confirmed by both Groq and FDA.

**Tradename intelligence** — strips noise from brand names while keeping the concentrations (e.g., `500mg`, `0.5%`), validates them as real trade names vs. generics, and adds Egypt-specific market context including local manufacturer data.

---

## Features

- Dosage form normalization into controlled categories (`oral_solid`, `injection`, `topical`, and others)
- Ingredient validation via local rules, with Groq LLM as fallback
- OpenFDA enrichment: brand names, warnings, drug interactions, adverse reactions
- Regex-based trade name cleaning that preserves concentrations and discards everything else
- Egypt-market brand validation with manufacturer identification
- Multi-worker execution with resume support and order-safe, append-only output
- Automatic API key rotation and rate-limit handling baked in

---

## Quick start

### 1. Set your API keys

```bash
export GROQ_API_KEY="your_groq_key"
export OPENFDA_API_KEY="your_openfda_key"
```

> ⚠️ Never commit API keys to source control.

### 2. Run FDA enrichment

```python
from fda_enrichment_pipeline import run_full_pipeline

run_full_pipeline()
```

### 3. Run tradename cleaning

```python
from tradename_cleaning_pipeline_v5 import run_full_pipeline

run_full_pipeline(
    start_from=1,
    end_at=3999,
    worker_name="Worker1",
    save_every=10,
    groq_delay=0.3,
)
```

---

## How the pipelines work

### Ingredient & FDA enrichment

```
Raw CSV
  → Form normalization
  → Ingredient extraction & splitting ("A + B + C" → ["A", "B", "C"])
  → Local validation → Groq LLM validation
  → OpenFDA enrichment (brand names, warnings, interactions, adverse reactions)
  → Filter: is_drug=true AND fda_found=true
  → confirmed_drugs.json / confirmed_drugs.csv
```

### Tradename intelligence

```
Raw tradename column
  → Regex deep clean (keep brand + concentration, strip form/pack tokens)
  → Groq Round 1: trade name vs. generic, casing fix, Egypt presence estimate
  → Round 2 (low-confidence trigger): verification pass
  → Round 3 (Egypt confirm): final market presence check
  → Append-only output: dataset_with_validated_tradenames.csv
```

---

## Usage

### Distributed execution (multi-worker)

Large datasets can be split across workers by row range:

```python
# Worker 1: rows 1–1500
run_full_pipeline(start_from=1, end_at=1500, worker_name="Worker1")

# Worker 2: rows 1501–3000
run_full_pipeline(start_from=1501, end_at=3000, worker_name="Worker2")
```

### Merge worker outputs

**Ingredients:**
```python
from fda_enrichment_pipeline import merge_progress_files
merge_progress_files()
```

**Tradenames:**
```python
from tradename_cleaning_pipeline_v5 import merge_all_workers
merge_all_workers()
```

### Filter confirmed FDA-validated drugs

```python
from fda_enrichment_pipeline import filter_confirmed_drugs
filter_confirmed_drugs()
```

### Validate tradename output ordering

Run this before starting a tradename job. It confirms your worker split won't scramble row order:

```python
from tradename_cleaning_pipeline_v5 import test_order
test_order()
```

---

## Input schema

| Column | Type | Description |
|---|---|---|
| `activeingredient` | string | Active ingredients, `+`-separated for combinations |
| `company` | string | Manufacturer or distributor |
| `created` | ISO datetime | Record creation timestamp |
| `form` | string | Raw dosage form (e.g., `syrup`, `tablet`, `vial`) |
| `group` | string | Therapeutic class (e.g., `cold drugs`, `antineoplastic`) |
| `id` | string | Unique product identifier |
| `new_price` | numeric | Retail price |
| `pharmacology` | text | Free-text composition, indications, mechanism |
| `route` | string | Route category (e.g., `oral.solid`, `injection`) |
| `tradename` | string | Raw commercial product label |
| `updated` | ISO datetime | Last update timestamp |

---

## Output files

| File | Description |
|---|---|
| `ingredients_fda_results.json` | All validated ingredients with FDA enrichment |
| `ingredients_fda_results.csv` | Same data, tabular |
| `confirmed_drugs.json` | Only ingredients where `is_drug=true` AND `fda_found=true` |
| `confirmed_drugs.csv` | Same, tabular |
| `dataset_with_validated_tradenames.csv` | Original rows + tradename columns (confirmed brands only, original order preserved) |
| `tradenames_validated.json` | Per-product tradename validation results |

### Enriched ingredient record

```json
{
  "fluorouracil": {
    "ingredient": "fluorouracil",
    "is_drug": true,
    "canonical_name": "fluorouracil",
    "fda_found": true,
    "brand_names": ["Adrucil", "Efudex"],
    "warnings": ["..."],
    "adverse_reactions": ["..."]
  }
}
```

### Tradename enrichment columns

| Column | Type | Description |
|---|---|---|
| `tradename_cleaned` | string | Brand + concentration only (noise stripped) |
| `tradename_corrected` | string | Spelling/casing-corrected brand name |
| `tradename_is_valid` | bool | Confirmed as a real trade/brand name |
| `tradename_is_generic` | bool | Detected as a generic/INN name |
| `tradename_confidence` | float | Final confidence score (0.0–1.0) |
| `tradename_correction_note` | string | Corrections applied + Egypt-market reasoning |
| `tradename_egypt_market` | bool | Confirmed/likely present in Egypt |
| `tradename_egypt_manufacturer` | string | Local manufacturer/distributor (if identified) |
| `tradename_generic_name` | string | Inferred INN/generic (if available) |
| `tradename_verified` | bool | True when a verification round confirms the result |
| `tradename_groq_rounds` | int | Number of Groq rounds executed (1–3) |

---

## Form normalization reference

| Category | Includes |
|---|---|
| `oral_solid` | tablet, capsule, effervescent, lozenge |
| `oral_liquid` | syrup, suspension, solution |
| `injection` | vial, ampoule, syringe, pen |
| `drops` | eye drops, ear drops, nasal drops |
| `topical` | cream, ointment, gel, lotion, shampoo |

---

## Tradename cleaning examples

The cleaner keeps the brand name and concentration. Everything else — form tokens, pack sizes, number words — gets stripped. If nothing valid remains, the row is discarded.

| Input | Output |
|---|---|
| `Abilify 15mg 30 F.C.tabs.` | `Abilify 15mg` |
| `Abramox 100mg/ml Syrup` | `Abramox 100mg/ml` |
| `A1 Cream 100 Gm` | `A1` |
| `1 2 3 (one Two Three) Syrup 120 Ml` | *(discarded — no valid brand)* |

---

## Troubleshooting

### Persistent rate limit failures

The pipeline handles retries and key rotation automatically. If you're still seeing failures, slow down the request cadence:

```python
run_full_pipeline(groq_delay=1.0)
```

### Output rows are out of order

Run `test_order()` before splitting workers. Original dataset ordering is guaranteed in all outputs, but the check will catch misconfigurations before they cost you a full run:

```python
from tradename_cleaning_pipeline_v5 import test_order
test_order()
```

### Ingredient missing from `confirmed_drugs`

This is normal for valid APIs, especially older generics. The ingredient will have `fda_found=false` and won't appear in the confirmed subset. Check `ingredients_fda_results.json` for the full record — the confidence score and validation notes are there.

### Worker outputs missing after merge

All workers must finish and save their progress files before you call `merge_progress_files()` or `merge_all_workers()`. Check that each worker's output directory contains a complete progress file before merging.

---

## Roadmap

- ATC classification mapping
- RxNorm and SNOMED CT integration
- WHO Drug Dictionary linking
- Adverse reaction frequency scoring
- REST API wrapper

---

## License

MIT
