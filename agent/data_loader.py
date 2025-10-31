"""Data loader for transaction CSV files"""
import csv
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path


def load_transactions(csv_path: str) -> List[Dict[str, Any]]:
    """Load transactions from CSV file"""
    transactions = []
    csv_file = Path(csv_path)
    
    if not csv_file.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Skip empty rows
            if not row.get('transaction_id') or not row.get('transaction_id').strip():
                continue
            
            # Convert amount to float
            try:
                row['amount'] = float(row['amount'])
            except (ValueError, KeyError):
                continue
            
            transactions.append(row)
    
    return transactions


def get_recurring_subscriptions(transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter and group recurring subscriptions"""
    subscriptions = [t for t in transactions if t.get('expense_type') == 'subscriptions']
    return subscriptions


def get_vendor_spending(transactions: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group transactions by vendor"""
    vendor_dict = {}
    for transaction in transactions:
        vendor = transaction.get('vendor_name', 'Unknown')
        if vendor not in vendor_dict:
            vendor_dict[vendor] = []
        vendor_dict[vendor].append(transaction)
    return vendor_dict


def calculate_monthly_average(transactions: List[Dict[str, Any]]) -> float:
    """Calculate average monthly spending from a list of transactions"""
    if not transactions:
        return 0.0
    
    # Filter monthly transactions
    monthly_transactions = [t for t in transactions if t.get('recurrency', '').lower() == 'monthly']
    if not monthly_transactions:
        return 0.0
    
    total = sum(t['amount'] for t in monthly_transactions)
    count = len(monthly_transactions)
    
    return total / count if count > 0 else 0.0


def get_category_vendors(transactions: List[Dict[str, Any]], category: str) -> List[str]:
    """Get unique vendors for a specific expense category"""
    category_transactions = [t for t in transactions if t.get('expense_type') == category]
    vendors = set(t.get('vendor_name', 'Unknown') for t in category_transactions)
    return list(vendors)

