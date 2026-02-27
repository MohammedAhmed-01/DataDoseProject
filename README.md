# 💊 Pharmaceutical Data Enrichment, FDA Validation & Tradename Intelligence Pipeline

A production-ready pharmaceutical data intelligence repository that transforms semi-structured drug product data into a **validated**, **standardized**, and **enrichment-ready** dataset.

This repo includes **two complementary pipelines**:

1. **API / Ingredient Intelligence**

   * Cleans & normalizes product attributes (e.g., dosage form)
   * Extracts unique active ingredients
   * Validates ingredients (local rules → Groq LLM)
   * Enriches clinical/regulatory context using **OpenFDA drug labels**
   * Filters **confirmed FDA-validated APIs**

2. **Tradename Intelligence (Egypt Market-Aware)**

   * Deep cleans trade names using regex rules
   * Preserves **concentration** (e.g., `500mg`, `100mg/ml`, `0.5%`)
   * Validates if the value is a **real brand/trade name** vs. generic/INN
   * Adds **Egypt-specific market confirmation fields** (Egypt presence, local manufacturer, inferred generic)
   * Writes **append-only CSV** containing **only confirmed brand rows**, while preserving original dataset order

---

## 📌 Project Overview

This repository converts a raw drug dataset into:

* A standardized dataset (clean forms/routes)
* A **validated API list** with FDA label enrichment
* A **confirmed-drugs subset** (Groq-confirmed + FDA-found)
* A **validated-tradenames dataset** (brand intelligence, Egypt-aware)
* Structured JSON exports suitable for analytics and Knowledge Graph construction

---

## 🔄 High-Level Workflow

```text
Raw Dataset (CSV)
   ↓
Form Cleaning & Normalization
   ↓
Ingredient Extraction + Validation (Local → Groq)
   ↓
FDA Enrichment (OpenFDA)
   ↓
Confirmed Drug Filtering (is_drug=true AND fda_found=true)
   ↓
Final Outputs (JSON + CSV) for Analytics / Knowledge Graph

            +-----------------------------------------+
            |  Tradename Cleaning & Validation (v5)   |
            |  - Regex cleanup (keep concentration)   |
            |  - Groq validation (Egypt-aware)        |
            |  - Append-only confirmed brand rows     |
            +-----------------------------------------+
```

---

## 🏗 System Architecture

### 1️⃣ Form Normalization Module

Standardizes dosage forms into controlled categories:

| Final Category | Includes                               |
| -------------- | -------------------------------------- |
| `oral_solid`   | tablet, capsule, effervescent, lozenge |
| `oral_liquid`  | syrup, suspension, solution            |
| `injection`    | vial, ampoule, syringe, pen            |
| `drops`        | eye drops, ear drops, nasal drops      |
| `topical`      | cream, ointment, gel, lotion, shampoo  |

**Features**

* Typo correction & abbreviation normalization
* Category consolidation
* Null handling
* Clean `form_clean` generation

---

### 2️⃣ FDA Enrichment Pipeline

#### Step A — Ingredient Validation (Local → Groq)

For each unique ingredient:

* Split combination strings (e.g., `A + B + C`)
* Validate whether it is a **real pharmaceutical API**
* Canonicalize to **WHO INN** naming where possible
* Reject non-drug items (cosmetic, vague supplement, herbal extract)
* Assign a confidence score
* Use local validator first to reduce API calls
* Apply key rotation + rate-limit handling

#### Step B — OpenFDA Enrichment

For validated APIs:

* Query **OpenFDA Drug Label API**
* Extract:

  * Brand names
  * Generic names
  * Manufacturers
  * Dosage forms
  * Warnings
  * Drug interactions
  * Adverse reactions
  * Indications

**Generated Outputs**

* `ingredients_fda_results.json`
* `ingredients_fda_results.csv`

---

### 3️⃣ Confirmed Drug Filtering

Retains only APIs where:

```text
is_drug = true
AND
fda_found = true
```

**Final Outputs**

* `confirmed_drugs.json`
* `confirmed_drugs.csv`

---

### 4️⃣ Tradename Cleaning & Validation (v5 — Egypt Market-Aware)

A dedicated pipeline to clean and validate **trade/brand names**.

#### 4.1 Deep Cleaning Rules (Regex)

Preserves:

* ✅ Brand name
* ✅ Concentration (e.g., `500mg`, `250mcg`, `100mg/ml`, `0.5%`)

Removes:

* ❌ dosage form tokens (tabs, caps, syrup, cream, etc.)
* ❌ pack sizes/counts (e.g., `20 tabs`, `120 ml`, `100 gm`)
* ❌ leading numeric sequences (e.g., `1 2 3`)
* ❌ number words (one/two/three)
* ❌ USP/BP/N/A fragments

Examples:

* `Abilify 15mg 30 F.C.tabs.` → `Abilify 15mg`
* `Abramox 100mg/ml Syrup` → `Abramox 100mg/ml`
* `A1 Cream 100 Gm` → `A1`
* `1 2 3 (one Two Three) Syrup 120 Ml` → `""` (discarded)

#### 4.2 Groq Validation (3-Round Egypt-Aware Strategy)

The pipeline uses Egypt market context in prompts and supports double/triple verification:

* **Round 1 (Validate):** detect trade name vs generic, fix typos/casing, estimate Egypt presence
* **Round 2 (Verify):** triggered on low confidence or corrections
* **Round 3 (Egypt Confirm):** final market presence check (Egypt registry / pharmacy lists patterns)

Egypt-specific enrichment fields:

* `tradename_egypt_market` (bool)
* `tradename_egypt_manufacturer` (string)
* `tradename_generic_name` (string, when inferred)

#### 4.3 Append-Only Confirmed Output (Order-Safe)

**Key production guarantees (v5):**

* Output CSV contains **only confirmed rows** (`is_tradename=true`)
* Output CSV is **append-only** per batch
* Row ordering is preserved exactly as original dataset ordering
* Worker splitting uses an **ordered unique list** (first appearance order)

**Outputs**

* `dataset_with_validated_tradenames.csv` (append-only)
* `tradenames_validated.json`

---

## 🗂 Dataset Schema (Data Dictionary)

> **Core dataset columns** (input CSV)

| Column               | Type         | Description                                                                                   |
| -------------------- | ------------ | --------------------------------------------------------------------------------------------- |
| **activeingredient** | string       | Active pharmaceutical ingredients. Multiple APIs separated by `+`.                            |
| **company**          | string       | Manufacturer/distributor. May include supply chain links (e.g., `Company A > Distributor B`). |
| **created**          | ISO datetime | Record creation timestamp.                                                                    |
| **form**             | string       | Raw dosage form before normalization (e.g., syrup, tablet, vial).                             |
| **group**            | string       | Therapeutic / product class (e.g., cold drugs, antineoplastic).                               |
| **id**               | string       | Unique internal product identifier.                                                           |
| **new_price**        | numeric      | Retail price of the product.                                                                  |
| **pharmacology**     | text         | Composition / indications / mechanism of action and other text fields.                        |
| **route**            | string       | Route category (e.g., `oral.solid`, `oral.liquid`, `injection`, `topical`).                   |
| **tradename**        | string       | Commercial product label as provided (noisy).                                                 |
| **updated**          | ISO datetime | Last update timestamp.                                                                        |

---

## 🧾 Tradename Enrichment Columns (Added by Tradename Pipeline)

These columns are appended to the tradename output CSV for confirmed brand rows:

| Column                         | Type   | Description                                                     |
| ------------------------------ | ------ | --------------------------------------------------------------- |
| `tradename_cleaned`            | string | Cleaned trade name (brand + concentration only).                |
| `tradename_corrected`          | string | Corrected trade name spelling/casing (concentration preserved). |
| `tradename_is_valid`           | bool   | True if confirmed as trade/brand name.                          |
| `tradename_is_generic`         | bool   | True if the value is a generic/INN name, not a brand.           |
| `tradename_confidence`         | float  | Final confidence score (0.0–1.0).                               |
| `tradename_correction_note`    | string | Summary note: corrections + Egypt-market reasoning.             |
| `tradename_egypt_market`       | bool   | Confirmed/likely present in Egypt.                              |
| `tradename_egypt_manufacturer` | string | Manufacturer/distributor in Egypt (if identified).              |
| `tradename_generic_name`       | string | Generic/INN inferred (if available).                            |
| `tradename_verified`           | bool   | True when verification confirms final output.                   |
| `tradename_groq_rounds`        | int    | Number of Groq rounds executed (1–3).                           |

---

## 🔎 Example Record

### Input

```json
{
  "activeingredient": "pseudoephedrine+paracetamol+chlorpheniramine",
  "company": "hikma",
  "form": "syrup",
  "group": "cold drugs",
  "new_price": 32,
  "route": "oral.liquid",
  "tradename": "1 2 3 syrup 120 ml"
}
```

### Processing Summary

1. Ingredient splitting → `pseudoephedrine`, `paracetamol`, `chlorpheniramine`
2. INN canonicalization via local rules/Groq
3. OpenFDA enrichment for validated APIs
4. Form mapping → `oral_liquid`
5. Tradename cleaning → may become empty (`""`) if it is non-informative

---

## 📁 Output Structure

### Enriched Ingredient JSON (OpenFDA)

```json
{
  "fluorouracil": {
    "ingredient": "fluorouracil",
    "is_drug": true,
    "canonical_name": "fluorouracil",
    "fda_found": true,
    "brand_names": ["..."],
    "warnings": ["..."],
    "adverse_reactions": ["..."]
  }
}
```

### Confirmed Drugs JSON

Contains only APIs that are both:

* Groq-confirmed (`is_drug=true`)
* Found in OpenFDA (`fda_found=true`)

---

## ⚙️ Usage

> The examples below assume you are running in Google Colab, with your dataset located in Google Drive.

### 1) Run FDA Enrichment Pipeline

```python
from fda_enrichment_pipeline import run_full_pipeline
run_full_pipeline()
```

### 2) Distributed Execution (Multi-Worker) — Ingredients

```python
run_full_pipeline(start_from=1, end_at=1500, worker_name="Worker1")
```

### 3) Merge Ingredient Worker Outputs

```python
merge_progress_files()
```

### 4) Filter Confirmed FDA-Validated Drugs

```python
filter_confirmed_drugs()
```

---

## 🏷️ Tradename Pipeline Usage (v5)

### Run Full Tradename Pipeline

```python
from tradename_cleaning_pipeline_v5 import run_full_pipeline

run_full_pipeline(
    start_from=1,
    end_at=3999,
    worker_name="User",
    save_every=10,
    groq_delay=0.3,
)
```

### Validate Ordering Before Running (Recommended)

```python
from tradename_cleaning_pipeline_v5 import test_order

test_order()
```

### Merge All Workers (Final Tradename Consolidation)

```python
from tradename_cleaning_pipeline_v5 import merge_all_workers

merge_all_workers()
```

---

## 🔐 Security Best Practices

⚠️ **Never commit API keys into public repositories.**

Recommended approach:

* Store keys in environment variables (or Colab secrets)
* Load them in runtime

```bash
export GROQ_API_KEY="your_key"
export OPENFDA_API_KEY="your_key"
```

---

## 🚀 Production Features

* Local validation to minimize LLM/API usage
* Automatic API key rotation
* Rate-limit resilience (retry-after + cooldown)
* Resume support (progress tracking JSON)
* Multi-worker execution support (range-based splitting)
* Clean Knowledge Graph export (flat JSON per ingredient)
* Automatic structure detection (progress vs clean output)
* Tradename: append-only confirmed CSV output + strict order preservation

---

## 📈 Use Cases

* Pharmaceutical Knowledge Graph construction
* Drug interaction modeling
* Regulatory intelligence and labeling analytics
* Clinical search engines
* Drug entity resolution (INN ↔ brand)
* Pharmacovigilance analysis
* Egypt market brand validation and normalization

---

## 🧩 Future Enhancements

* ATC classification mapping
* RxNorm integration
* SNOMED CT alignment
* WHO Drug Dictionary linking
* Automated therapeutic class classification
* Adverse reaction frequency scoring
* REST API wrapper / microservice deployment

---

## 👨‍💻 Author

**Pharmaceutical Data Intelligence Pipeline**
Designed for scalable drug validation, FDA enrichment, and tradename intelligence workflows.

> "البحث عن منفذ لخروج السيد رامبو"
