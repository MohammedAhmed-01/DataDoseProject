# 💊 Pharmaceutical Data Enrichment & FDA Validation Pipeline

A production-ready pharmaceutical data intelligence pipeline that:

* Cleans and normalizes raw drug datasets
* Standardizes dosage forms into controlled categories
* Validates active pharmaceutical ingredients (APIs) using LLM (Groq)
* Enriches drug data from OpenFDA
* Filters confirmed FDA-validated drugs
* Produces structured JSON & CSV outputs for analytics and Knowledge Graph construction

---

# 📌 Project Overview

This repository transforms semi-structured pharmaceutical product data into a validated, enriched, and analytics-ready dataset.

## 🔄 High-Level Workflow

```text
Raw Dataset
   ↓
Form Cleaning & Normalization
   ↓
Ingredient Validation (Groq API)
   ↓
FDA Enrichment (OpenFDA API)
   ↓
Confirmed Drug Filtering
   ↓
Final Structured Outputs (JSON + CSV)
```

---

# 🏗 System Architecture

## 1️⃣ Form Normalization Module

Standardizes dosage forms into controlled categories:

| Final Category | Includes                               |
| -------------- | -------------------------------------- |
| `oral_solid`   | tablet, capsule, effervescent, lozenge |
| `oral_liquid`  | syrup, suspension, solution            |
| `injection`    | vial, ampoule, syringe, pen            |
| `drops`        | eye drops, ear drops, nasal drops      |
| `topical`      | cream, ointment, gel, lotion, shampoo  |

### Features

* Typo correction
* Abbreviation normalization
* Category consolidation
* Null handling
* Clean `form_clean` column generation

---

## 2️⃣ FDA Enrichment Pipeline

### Step A — Ingredient Validation (Groq API)

Each unique ingredient is:

* Canonicalized to WHO INN standard
* Validated as a pharmaceutical API
* Rejected if cosmetic, supplement, herbal extract, or non-drug
* Assigned a confidence score
* Optimized using local validation before API calls
* Protected by smart API key rotation & rate-limit handling

---

### Step B — OpenFDA Enrichment

For validated APIs:

* Searches OpenFDA Drug Label API
* Extracts:

  * Brand names
  * Generic names
  * Manufacturers
  * Dosage forms
  * Warnings
  * Drug interactions
  * Adverse reactions
  * Indications

### Generated Outputs

* `ingredients_fda_results.json`
* `ingredients_fda_results.csv`

---

## 3️⃣ Confirmed Drug Filtering

Filters dataset to retain only entries where:

```text
is_drug = true
AND
fda_found = true
```

### Final Outputs

* `confirmed_drugs.json`
* `confirmed_drugs.csv`

---

# 🗂 Dataset Schema (Data Dictionary)

| Column               | Type         | Description                                                                                              |
| -------------------- | ------------ | -------------------------------------------------------------------------------------------------------- |
| **activeingredient** | string       | Active pharmaceutical ingredients. Multiple APIs separated by `+`.                                       |
| **company**          | string       | Manufacturer or distributor. May contain supply chain relationships (e.g., `Company A > Distributor B`). |
| **created**          | ISO datetime | Record creation timestamp.                                                                               |
| **form**             | string       | Raw dosage form before normalization (e.g., syrup, tablet, vial).                                        |
| **group**            | string       | Therapeutic or product classification (e.g., cold drugs, antineoplastic).                                |
| **id**               | string       | Unique internal product identifier.                                                                      |
| **new_price**        | numeric      | Retail price of the product.                                                                             |
| **pharmacology**     | text         | Description including composition, indications, mechanism of action.                                     |
| **route**            | string       | Route of administration (`oral.solid`, `oral.liquid`, `injection`, `topical`).                           |
| **tradename**        | string       | Commercial product name.                                                                                 |
| **updated**          | ISO datetime | Last update timestamp.                                                                                   |

---

# 🔎 Example Record

## Input

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

## Processing Steps

1. Ingredient splitting:

   * `pseudoephedrine`
   * `paracetamol`
   * `chlorpheniramine`
2. INN canonicalization
3. OpenFDA enrichment
4. Controlled form mapping → `oral_liquid`
5. Structured JSON output generation

---

# 📁 Output Structure

## Enriched Ingredient JSON

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

## Confirmed Drugs JSON

Contains only FDA-validated pharmaceutical APIs.

---

# ⚙️ Usage

## Run Full Pipeline

```python
from fda_enrichment_pipeline import run_full_pipeline
run_full_pipeline()
```

## Distributed Execution (Multi-Worker)

```python
run_full_pipeline(start_from=1, end_at=1500, worker_name="Worker1")
```

## Merge Worker Outputs

```python
merge_progress_files()
```

## Filter Confirmed Drugs

```python
filter_confirmed_drugs()
```

---

# 🔐 Security Best Practices

⚠️ Never commit API keys into public repositories.

Use environment variables:

```bash
export GROQ_API_KEY="your_key"
export OPENFDA_API_KEY="your_key"
```

---

# 🚀 Production Features

* Local validation to minimize API usage
* Automatic API key rotation
* Rate-limit resilience
* Resume support (progress tracking)
* Multi-worker execution
* Clean Knowledge Graph export
* Automatic structure detection (progress vs clean file)

---

# 📈 Use Cases

* Pharmaceutical Knowledge Graph construction
* Drug interaction modeling
* Regulatory intelligence
* Clinical search engines
* Drug normalization pipeline
* Pharmacovigilance analysis

---

# 🧩 Future Enhancements

* ATC classification mapping
* RxNorm integration
* SNOMED CT alignment
* WHO Drug Dictionary linking
* Automated therapeutic class classification
* Adverse reaction frequency scoring
* REST API interface

---

# 👨‍💻 Author

**Pharmaceutical Data Intelligence Pipeline**
Designed for scalable drug validation and enrichment workflows.

> "البحث عن منفذ لخروج السيد رامبو"
