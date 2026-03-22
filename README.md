# Pharmaceutical Data Intelligence Pipeline

Validate, enrich, and standardize drug product data — from raw noisy CSVs to FDA-confirmed, Egypt-market-aware brand intelligence.

---

## What This Does

This pipeline takes messy pharmaceutical product records and produces clean, validated, analytics-ready datasets. It handles two complementary workflows:

**API / Ingredient Intelligence** — validates active ingredients against WHO INN standards, enriches them with OpenFDA label data, and outputs only FDA-confirmed APIs.

**Tradename Intelligence** — deep-cleans brand names (preserving concentration values), validates them as real trade names vs. generics, and adds Egypt-market context.

---

## Features

- Normalizes dosage forms into controlled categories (`oral_solid`, `injection`, `topical`, etc.)
- Validates ingredients via local rules first, then Groq LLM fallback
- Enriches confirmed APIs with brand names, warnings, interactions, and adverse reactions from OpenFDA
- Cleans trade names using regex while preserving concentrations (e.g., `500mg`, `100mg/ml`, `0.5%`)
- Validates brand names in Egypt market context with manufacturer identification
- Multi-worker execution with resume support and append-only, order-safe output
- Automatic API key rotation and rate-limit resilience

---

## Quick Start

### 1. Set your API keys

```bash
export GROQ_API_KEY="your_groq_key"
export OPENFDA_API_KEY="your_openfda_key"
```

> ⚠️ Never commit API keys to source control.

### 2. Run the FDA enrichment pipeline

```python
from fda_enrichment_pipeline import run_full_pipeline

run_full_pipeline()
```

### 3. Run the tradename pipeline

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

## Pipeline Workflows

### Workflow 1 — Ingredient & FDA Enrichment

```
Raw CSV
  → Form normalization
  → Ingredient extraction & splitting (e.g., "A + B + C" → ["A", "B", "C"])
  → Local validation → Groq LLM validation
  → OpenFDA enrichment (brand names, warnings, interactions, adverse reactions)
  → Filter: is_drug=true AND fda_found=true
  → confirmed_drugs.json / confirmed_drugs.csv
```

### Workflow 2 — Tradename Intelligence

```
Raw tradename column
  → Regex deep clean (keep brand + concentration, strip form/pack tokens)
  → Groq validation Round 1: trade name vs. generic, casing fix, Egypt presence estimate
  → Round 2 (low-confidence trigger): verification pass
  → Round 3 (Egypt confirm): final market presence check
  → Append-only output: dataset_with_validated_tradenames.csv
```

---

## Usage

### Distributed execution (multi-worker)

Split large datasets across workers by row range:

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

### Validate tradename output ordering (recommended before a run)

```python
from tradename_cleaning_pipeline_v5 import test_order
test_order()
```

---

## Input Schema

Your input CSV must contain these columns:

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

## Output Files

| File | Description |
|---|---|
| `ingredients_fda_results.json` | All validated ingredients with FDA enrichment |
| `ingredients_fda_results.csv` | Same data, tabular format |
| `confirmed_drugs.json` | Subset where `is_drug=true` AND `fda_found=true` |
| `confirmed_drugs.csv` | Same, tabular |
| `dataset_with_validated_tradenames.csv` | Original rows + tradename enrichment columns (confirmed brands only) |
| `tradenames_validated.json` | Tradename validation results per product |

### Enriched ingredient record (JSON)

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

### Tradename enrichment columns (added to output CSV)

| Column | Type | Description |
|---|---|---|
| `tradename_cleaned` | string | Brand + concentration only (noise removed) |
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

## Form Normalization Reference

Raw dosage form strings are standardized into these categories:

| Category | Includes |
|---|---|
| `oral_solid` | tablet, capsule, effervescent, lozenge |
| `oral_liquid` | syrup, suspension, solution |
| `injection` | vial, ampoule, syringe, pen |
| `drops` | eye drops, ear drops, nasal drops |
| `topical` | cream, ointment, gel, lotion, shampoo |

---

## Tradename Cleaning Examples

The regex cleaner preserves the brand name and concentration while stripping everything else:

| Input | Output |
|---|---|
| `Abilify 15mg 30 F.C.tabs.` | `Abilify 15mg` |
| `Abramox 100mg/ml Syrup` | `Abramox 100mg/ml` |
| `A1 Cream 100 Gm` | `A1` |
| `1 2 3 (one Two Three) Syrup 120 Ml` | *(discarded — no valid brand)* |

---

## Troubleshooting

### Rate limit errors from Groq or OpenFDA

The pipeline handles these automatically with retry-after delays and key rotation. If you see persistent failures, increase `groq_delay`:

```python
run_full_pipeline(groq_delay=1.0)
```

### Output rows appear out of order

Run the order validation check before starting:

```python
from tradename_cleaning_pipeline_v5 import test_order
test_order()
```

The pipeline guarantees original dataset ordering in all outputs.

### Ingredient not found in OpenFDA

This is expected for some valid APIs. The ingredient will have `fda_found=false` and will be excluded from `confirmed_drugs` output. Check `ingredients_fda_results.json` for the full record with validation status and confidence score.

### Worker outputs missing after merge

Ensure all workers completed successfully and their progress files are in the expected directory before calling `merge_progress_files()` or `merge_all_workers()`.

---

## Roadmap

- ATC classification mapping
- RxNorm integration
- SNOMED CT alignment
- WHO Drug Dictionary linking
- Adverse reaction frequency scoring
- REST API / microservice wrapper

---

## License

MIT
