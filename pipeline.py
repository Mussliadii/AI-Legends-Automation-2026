import os
import json
import glob
import pandas as pd
from extractor import InvoiceExtractor
from validator import InvoiceValidator

def process_batch(data_dir: str, limit: int = None, output_dir: str = "output"):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    print("=== Starting AI Legends 2026 Automated Pipeline ===")
    
    db_path = os.path.join(data_dir, "master_invoices_database.db")
    api_key = "API_KEY" 
    
    try:
        extractor = InvoiceExtractor(api_key=api_key)
        validator = InvoiceValidator(db_path=db_path)
    except Exception as e:
        print(f"Failed to initialize systems: {e}")
        return

    all_files = []
    for ext in ('*.jpg', '*.png', '*.jpeg', '*.pdf'):
        all_files.extend(glob.glob(os.path.join(data_dir, ext)))
    all_files.sort()
    
    if limit:
        all_files = all_files[:limit]
        print(f"Limiting execution to the first {limit} files for testing.")

    results = []

    for file_path in all_files:
        filename = os.path.basename(file_path)
        print(f"\n[>] Processing {filename}...")
        try:
            # Phase 1: Data Extraction
            extracted_data = extractor.extract(file_path)
            
            # Phase 2: Data Validation
            validation_result = validator.validate(extracted_data)
            
            # Combine Results
            record = {
                "file_name": filename,
                "invoice_number": extracted_data.invoice_number,
                "vendor_name": extracted_data.vendor_name,
                "invoice_date": extracted_data.invoice_date,
                "category": extracted_data.category,
                "grand_total": extracted_data.grand_total,
                "decision": validation_result["decision"],
                "errors": "; ".join(validation_result["errors"]),
                "warnings": "; ".join(validation_result["warnings"]),
                "vendor_match": validation_result["vendor_match"],
                "match_score": validation_result["vendor_match_score"]
            }
            results.append(record)
            print(f"    --> Decision: {record['decision']}")
            
        except Exception as e:
            print(f"    [!] Failed to process {filename}: {e}")
            results.append({
                "file_name": filename,
                "decision": "ERROR",
                "errors": str(e)
            })

    # Export Results
    if results:
        df = pd.DataFrame(results)
        csv_path = os.path.join(output_dir, "batch_results.csv")
        json_path = os.path.join(output_dir, "batch_results.json")
        df.to_csv(csv_path, index=False, encoding='utf-8')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
            
        print(f"\n=== Pipeline Completed ===")
        print(f"Total processed: {len(results)}")
        print("Decision Summary:")
        print(df['decision'].value_counts().to_string())
        print(f"\nDetailed results saved to '{csv_path}' and '{json_path}'")

if __name__ == "__main__":
    # Test with a limit of 5 files initially
    process_batch(data_dir="Data", limit=10)
