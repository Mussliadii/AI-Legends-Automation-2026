import sqlite3
import datetime
from thefuzz import fuzz
from typing import Dict, List, Any
import json
from extractor import InvoiceData, LineItem

class InvoiceValidator:
    def __init__(self, db_path: str):
        self.db_path = db_path
        
    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def validate(self, invoice: InvoiceData) -> Dict[str, Any]:
        """
        Validates the InvoiceData against business rules and the master database.
        Returns a dictionary containing the final decision and error details.
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        errors = []
        warnings = []
        
        # ----------------------------------------------------
        # 1. AMOUNT_MISMATCH (Mathematical Validation)
        # ----------------------------------------------------
        calculated_total = 0
        for item in invoice.line_items:
            expected_line_total = item.qty * item.unit_price
            if abs(expected_line_total - item.total) > 0.01:
                errors.append(f"AMOUNT_MISMATCH: Line item '{item.item_name}' mismatch. Qty({item.qty}) x Price({item.unit_price}) != Total({item.total})")
            calculated_total += item.total
            
        if abs(calculated_total - invoice.grand_total) > 0.01:
            errors.append(f"AMOUNT_MISMATCH: Grand Total mismatch. Calculated: {calculated_total}, On Invoice: {invoice.grand_total}")

        # ----------------------------------------------------
        # 2. INVALID_DATE (Date Validation)
        # ----------------------------------------------------
        try:
            inv_date = datetime.datetime.strptime(invoice.invoice_date, "%Y-%m-%d")
            if invoice.due_date:
                due_date = datetime.datetime.strptime(invoice.due_date, "%Y-%m-%d")
                if due_date < inv_date:
                    errors.append(f"INVALID_DATE: Due date ({invoice.due_date}) is earlier than invoice date ({invoice.invoice_date})")
        except ValueError:
            errors.append("INVALID_DATE: Invalid date format (must be YYYY-MM-DD)")

        # ----------------------------------------------------
        # 3. UNREGISTERED_VENDOR & BANK_ACCOUNT_MISMATCH
        # ----------------------------------------------------
        cursor.execute("SELECT ID, Name, Bank, Account FROM Vendors")
        vendors = cursor.fetchall()
        
        best_match = None
        highest_score = 0
        
        # Search for vendor using Fuzzy Matching
        for v in vendors:
            v_id, v_name, v_bank, v_account = v
            score = fuzz.ratio(invoice.vendor_name.lower(), v_name.lower())
            if score > highest_score:
                highest_score = score
                best_match = v
                
        # If match score is below 80%, consider unregistered
        is_vendor_registered = False
        if highest_score < 80:
            warnings.append(f"UNREGISTERED_VENDOR: Vendor '{invoice.vendor_name}' not found in the database.")
        else:
            is_vendor_registered = True
            matched_id, matched_name, matched_bank, matched_account = best_match
            
            # If vendor is registered, validate bank account
            if invoice.bank_account:
                # Remove spaces and dashes
                inv_acc_clean = invoice.bank_account.replace(" ", "").replace("-", "")
                db_acc_clean = matched_account.replace(" ", "").replace("-", "")
                
                if inv_acc_clean != db_acc_clean:
                    errors.append(f"BANK_ACCOUNT_MISMATCH: Account '{invoice.bank_account}' does not match DB record '{matched_account}' for vendor '{matched_name}'")

        # ----------------------------------------------------
        # 4. DUPLICATE (Historical Duplication Validation)
        # ----------------------------------------------------
        # If registered, check if previously billed with same amount and near identical date (within 2 days)
        if is_vendor_registered:
            cursor.execute('''
                SELECT InvoiceDate, GrandTotal FROM Invoices 
                WHERE VendorName = ? AND GrandTotal = ?
            ''', (matched_name, invoice.grand_total))
            history = cursor.fetchall()
            
            for h_date_str, h_total in history:
                try:
                    h_date = datetime.datetime.strptime(h_date_str, "%Y-%m-%d")
                    # If date difference is <= 2 days, flag as duplicate
                    if abs((inv_date - h_date).days) <= 2:
                        errors.append(f"DUPLICATE: Possible duplicate of invoice dated {h_date_str} for amount {h_total}")
                        break
                except ValueError:
                    continue

        conn.close()

        # ----------------------------------------------------
        # 5. FINAL BUSINESS DECISION
        # ----------------------------------------------------
        # Rule 1: Critical Error -> DENY
        if len(errors) > 0:
            decision = "DENY"
        # Rule 2: No Errors, but New Vendor (Warning) -> HUMAN_APPROVAL
        elif len(warnings) > 0:
            decision = "HUMAN_APPROVAL"
        # Rule 3: All checks passed -> AUTO_POST
        else:
            decision = "AUTO_POST"

        return {
            "decision": decision,
            "errors": errors,
            "warnings": warnings,
            "vendor_match": best_match[1] if best_match and highest_score >= 80 else None,
            "vendor_match_score": highest_score
        }

if __name__ == "__main__":
    import os
    
    db_path = os.path.join("Data", "master_invoices_database.db")
    validator = InvoiceValidator(db_path)
    
    print("\n[TEST CASE 1: Clean Invoice]")
    clean_invoice = InvoiceData(
        invoice_number="INV-001",
        vendor_name="Демо Компани-1",
        invoice_date="2026-05-01",
        due_date="2026-05-15",
        bank_name="Демо Банк 1",
        bank_account="5001122334",
        category="Түрээсийн зардал",
        grand_total=100000.0,
        line_items=[
            LineItem(item_name="Service", qty=1.0, unit_price=100000.0, total=100000.0)
        ]
    )
    res1 = validator.validate(clean_invoice)
    print(json.dumps(res1, indent=2))
