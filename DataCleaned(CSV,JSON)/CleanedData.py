"""
================================================================================
FILTER CONFIRMED DRUGS
================================================================================
Filter the merged JSON to keep only entries where:
  - is_drug   = true  (confirmed by Groq as a drug)
  - fda_found = true  (found in OpenFDA)

Outputs:
  - confirmed_drugs.json
  - confirmed_drugs.csv
================================================================================
"""

import json
import os
import pandas as pd

# ==============================================================================
# Settings
# ==============================================================================
BASE_DIR = "/content/drive/MyDrive/DataDoseDepi/JsonFinal"

INPUT_JSON = os.path.join(BASE_DIR, "File.json")  # merged file
OUTPUT_JSON = os.path.join(BASE_DIR, "confirmed_drugs.json")
OUTPUT_CSV = os.path.join(BASE_DIR, "confirmed_drugs.csv")


# ==============================================================================
# Filter
# ==============================================================================
def filter_confirmed_drugs(input_json=None, output_json=None, output_csv=None):
    input_json = input_json or INPUT_JSON
    output_json = output_json or OUTPUT_JSON
    output_csv = output_csv or OUTPUT_CSV

    # Read file
    print(f"📂 Reading: {input_json}")
    with open(input_json, "r", encoding="utf-8") as f:
        data = json.load(f)

    total = len(data)
    print(f"📋 Total ingredients in file: {total:,}")

    # Detect structure automatically
    # Type 1 (clean output): { "is_drug": true, "fda_found": true, ... }
    # Type 2 (progress file): { "status":"done", "groq_validation":{...}, "fda_data":{...} }
    first = next(iter(data.values()))
    is_progress_file = ("groq_validation" in first) or ("status" in first)

    if is_progress_file:
        print("📁 Type: Progress file — converting to clean structure...")
        converted = {}
        for ingredient, entry in data.items():
            if entry.get("status") != "done":
                continue

            groq = entry.get("groq_validation") or {}
            fda = entry.get("fda_data") or {}

            converted[ingredient] = {
                "ingredient": ingredient,
                "is_drug": groq.get("is_drug", False),
                "canonical_name": groq.get("canonical_name"),
                "fda_search_term": groq.get("fda_search_term"),
                "groq_confidence": groq.get("confidence", 0.0),
                "rejection_reason": groq.get("rejection_reason"),
                "fda_found": fda.get("found", False),
                "brand_names": fda.get("brand_names", []),
                "generic_names": fda.get("generic_names", []),
                "manufacturers": fda.get("manufacturers", []),
                "dosage_forms": fda.get("dosage_forms", []),
                "warnings": fda.get("warnings", []),
                "drug_interactions": fda.get("drug_interactions", []),
                "adverse_reactions": fda.get("adverse_reactions", []),
                "indications": fda.get("indications", []),
            }

        data = converted
        print(f"   ✅ Converted entries: {len(data):,}")
    else:
        print("📁 Type: Clean output file")

    # Apply filter
    confirmed = {
        ingredient: rec
        for ingredient, rec in data.items()
        if rec.get("is_drug") is True and rec.get("fda_found") is True
    }

    rejected_not_drug = sum(1 for r in data.values() if not r.get("is_drug"))
    rejected_not_found = sum(
        1 for r in data.values()
        if r.get("is_drug") and not r.get("fda_found")
    )

    print("\n📊 Results:")
    print(f"   ✅ is_drug=true  + fda_found=true  : {len(confirmed):,}  (saved)")
    print(f"   ❌ is_drug=false                    : {rejected_not_drug:,}  (removed)")
    print(f"   ⚠️  is_drug=true  + fda_found=false : {rejected_not_found:,}  (removed)")

    # Save JSON
    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(confirmed, f, ensure_ascii=False, indent=2)
    print(f"\n💾 JSON saved: {output_json}  ({len(confirmed):,} drugs)")

    # Save CSV
    rows = []
    for ingredient, rec in confirmed.items():
        rows.append({
            "ingredient": ingredient,
            "canonical_name": rec.get("canonical_name", ""),
            "groq_confidence": rec.get("groq_confidence", ""),
            "fda_search_term": rec.get("fda_search_term", ""),
            "brand_names": " | ".join(rec.get("brand_names", [])),
            "generic_names": " | ".join(rec.get("generic_names", [])),
            "manufacturers": " | ".join(rec.get("manufacturers", [])),
            "dosage_forms": " | ".join(rec.get("dosage_forms", [])),
            "warnings_count": len(rec.get("warnings", [])),
            "interactions_count": len(rec.get("drug_interactions", [])),
            "adverse_count": len(rec.get("adverse_reactions", [])),
            "indications_count": len(rec.get("indications", [])),
            "first_warning": rec["warnings"][0] if rec.get("warnings") else "",
            "first_interaction": rec["drug_interactions"][0] if rec.get("drug_interactions") else "",
            "first_adverse": rec["adverse_reactions"][0] if rec.get("adverse_reactions") else "",
            "first_indication": rec["indications"][0] if rec.get("indications") else "",
        })

    pd.DataFrame(rows).to_csv(output_csv, index=False, encoding="utf-8")
    print(f"💾 CSV saved: {output_csv}  ({len(rows):,} rows)")
    print("\n🎉 Done!")
    return confirmed


# ==============================================================================
# Entry point
# ==============================================================================
if __name__ == "__main__":
    filter_confirmed_drugs()
