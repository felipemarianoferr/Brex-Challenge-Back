#!/usr/bin/env python3
"""Script to test the API flow: create or login as user, upload or read CSV"""

import httpx
import json

# API base URL
BASE_URL = "http://localhost:8000"

def main():
    print("=" * 60)
    print("Testing API Flow: Create/Login User -> Upload/Read CSV")
    print("=" * 60)
    
    # User credentials
    user_email = "testuser@example.com"
    user_password = "0101"
    user_full_name = "Test User"
    
    try:
        with httpx.Client(timeout=10.0) as client:
            # Step 1: Try to register a new user
            print(f"\n1. Creating or logging in as user: {user_email}")
            register_data = {
                "email": user_email,
                "password": user_password,
                "full_name": user_full_name
            }
            
            register_response = client.post(
                f"{BASE_URL}/api/auth/register",
                json=register_data
            )
            
            user_created = False
            if register_response.status_code == 201:
                print("[OK] User created successfully!")
                user_data = register_response.json()
                print(f"  User ID: {user_data.get('id')}")
                print(f"  Email: {user_data.get('email')}")
                print(f"  Full Name: {user_data.get('full_name')}")
                user_created = True
            elif register_response.status_code == 400:
                print("[INFO] User already exists, will try to log in...")
                user_created = False
                # Note: If login fails, the user exists but password might be different
                # User will need to wipe database or use a different email for testing
            else:
                print(f"[ERROR] Registration failed: {register_response.status_code}")
                print(f"  Response: {register_response.text}")
                return
            
            # Step 2: Login
            print(f"\n2. Logging in as {user_email}...")
            login_data = {
                "username": user_email,
                "password": user_password
            }
            
            login_response = client.post(
                f"{BASE_URL}/api/auth/login",
                data=login_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if login_response.status_code == 200:
                token_data = login_response.json()
                access_token = token_data.get("access_token")
                print("[OK] Login successful!")
                print(f"  Token: {access_token[:30]}...")
            else:
                print(f"[ERROR] Login failed: {login_response.status_code}")
                print(f"  Response: {login_response.text}")
                if register_response.status_code == 400:
                    print(f"\n[NOTE] User '{user_email}' exists but password doesn't match '0101'")
                    print("  To use password '0101', you can either:")
                    print("    1. Wipe the database: python wipe_db.py --force")
                    print("    2. Or use a different email address for testing")
                return
            
            headers = {"Authorization": f"Bearer {access_token}"}
            
            # Step 3: Check existing expenses
            print(f"\n3. Checking existing expenses...")
            list_response = client.get(
                f"{BASE_URL}/api/expenses",
                headers=headers
            )
            
            existing_expenses = []
            if list_response.status_code == 200:
                existing_expenses = list_response.json()
                print(f"[OK] Found {len(existing_expenses)} existing expenses")
                if existing_expenses:
                    print("  Sample expenses:")
                    for i, exp in enumerate(existing_expenses[:3], 1):
                        print(f"    {i}. {exp.get('transaction_id')} - {exp.get('vendor_name')} - ${exp.get('amount')}")
            
            # Step 4: Upload CSV if user was created, or if no expenses exist
            if user_created or len(existing_expenses) == 0:
                print(f"\n4. Uploading CSV file (user created or no expenses found)...")
                
                try:
                    with open("mock.csv", "rb") as f:
                        files = {"file": ("mock.csv", f, "text/csv")}
                        
                        upload_response = client.post(
                            f"{BASE_URL}/api/expenses/upload-csv",
                            files=files,
                            headers=headers
                        )
                    
                    if upload_response.status_code == 200:
                        upload_result = upload_response.json()
                        print("[OK] CSV uploaded successfully!")
                        print(f"  Records processed: {upload_result.get('records_processed')}")
                        print(f"  Records inserted: {upload_result.get('records_inserted')}")
                        print(f"  Records updated: {upload_result.get('records_updated')}")
                        
                        # List expenses after upload
                        print(f"\n5. Reading expenses after upload...")
                        list_response = client.get(
                            f"{BASE_URL}/api/expenses",
                            headers=headers
                        )
                        
                        if list_response.status_code == 200:
                            expenses = list_response.json()
                            print(f"[OK] Total expenses: {len(expenses)}")
                            print("  Expenses summary:")
                            for i, exp in enumerate(expenses[:5], 1):
                                print(f"    {i}. ID: {exp.get('transaction_id')} | Vendor: {exp.get('vendor_name')} | Amount: ${exp.get('amount')} {exp.get('currency')} | Date: {exp.get('datetime')}")
                            if len(expenses) > 5:
                                print(f"    ... and {len(expenses) - 5} more expenses")
                    else:
                        print(f"[ERROR] CSV upload failed: {upload_response.status_code}")
                        print(f"  Response: {upload_response.text}")
                        return
                        
                except FileNotFoundError:
                    print(f"[ERROR] CSV file 'mock.csv' not found!")
                    return
            else:
                # Step 4: Read existing expenses
                print(f"\n4. Reading existing expenses (user already had data)...")
                print(f"[OK] Found {len(existing_expenses)} expenses")
                print("  Expenses summary:")
                for i, exp in enumerate(existing_expenses[:10], 1):
                    print(f"    {i}. ID: {exp.get('transaction_id')} | Vendor: {exp.get('vendor_name')} | Amount: ${exp.get('amount')} {exp.get('currency')} | Department: {exp.get('department')} | Type: {exp.get('expense_type')} | Date: {exp.get('datetime')}")
                if len(existing_expenses) > 10:
                    print(f"    ... and {len(existing_expenses) - 10} more expenses")
                
                # Show statistics
                print(f"\n5. Expense statistics:")
                total_amount = sum(float(str(exp.get('amount', 0))) for exp in existing_expenses)
                currencies = {}
                departments = {}
                for exp in existing_expenses:
                    curr = exp.get('currency', 'N/A')
                    dept = exp.get('department', 'N/A')
                    currencies[curr] = currencies.get(curr, 0) + 1
                    departments[dept] = departments.get(dept, 0) + 1
                
                print(f"  Total expenses: {len(existing_expenses)}")
                print(f"  Total amount: ${total_amount:,.2f}")
                print(f"  Currencies: {dict(currencies)}")
                print(f"  Departments: {dict(departments)}")
            
            print("\n" + "=" * 60)
            print("API flow completed successfully!")
            print("=" * 60)
            
    except httpx.ConnectError:
        print("[ERROR] Could not connect to the API server.")
        print("  Make sure the server is running on http://localhost:8000")
        print("  Start it with: uvicorn app.main:app --reload")
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

