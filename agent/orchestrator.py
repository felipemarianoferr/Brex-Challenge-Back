"""Main orchestrator to run all agents in parallel"""
import asyncio
import json
from typing import Dict, Any, List
from pathlib import Path
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.data_loader import load_transactions
from agent.duplicate_detection_agent import DuplicateDetectionAgent
from agent.yearly_switch_agent import YearlySwitchAgent
from agent.substitution_agent import SubstitutionAgent
from agent.config import Config


class SpendManagementOrchestrator:
    """Orchestrates all spend management agents"""
    
    def __init__(self, csv_path: str = None):
        """Initialize orchestrator with data path"""
        self.csv_path = csv_path or Config.DEFAULT_CSV_PATH
        self.transactions = None
    
    def load_data(self):
        """Load transaction data"""
        self.transactions = load_transactions(self.csv_path)
        return self.transactions
    
    async def run_all_agents(self) -> Dict[str, Any]:
        """Run all agents in parallel"""
        if not self.transactions:
            self.load_data()
        
        # Initialize agents
        duplicate_agent = DuplicateDetectionAgent()
        yearly_switch_agent = YearlySwitchAgent()
        substitution_agent = SubstitutionAgent()
        
        # Run all agents in parallel
        
        results = await asyncio.gather(
            duplicate_agent.analyze(self.transactions),
            yearly_switch_agent.analyze(self.transactions),
            substitution_agent.analyze(self.transactions),
            return_exceptions=True
        )
        
        duplicate_results, yearly_results, substitution_results = results
        
        # Handle exceptions silently - errors will show in summary
        if isinstance(duplicate_results, Exception):
            duplicate_results = {"error": str(duplicate_results)}
        
        if isinstance(yearly_results, Exception):
            yearly_results = {"error": str(yearly_results)}
        
        if isinstance(substitution_results, Exception):
            substitution_results = {"error": str(substitution_results)}
        
        # Compile final results
        final_results = {
            "duplicate_spend_detection": duplicate_results,
            "yearly_switch_advisor": yearly_results,
            "smart_substitution_advisor": substitution_results,
            "metadata": {
                "total_transactions": len(self.transactions),
                "analysis_date": datetime.now().isoformat()
            }
        }
        
        return final_results
    
    def print_summary(self, results: Dict[str, Any]):
        """Print a human-readable summary of results"""
        print("\n" + "="*80)
        print("SPEND MANAGEMENT ANALYSIS SUMMARY")
        print("="*80 + "\n")
        
        # Duplicate Spend Detection
        print("1. INTELLIGENT DUPLICATE SPEND DETECTION")
        print("-" * 80)
        dup_results = results.get("duplicate_spend_detection", {})
        if "duplicate_detections" in dup_results:
            detections = dup_results["duplicate_detections"]
            print(f"   Found {len(detections)} duplicate spend opportunities\n")
            for i, detection in enumerate(detections, 1):
                print(f"   {i}. {', '.join(detection.get('vendors', []))}")
                print(f"      Category: {detection.get('category', 'N/A')}")
                print(f"      Current Monthly: ${detection.get('current_spending', {}).get('total_monthly', 0):.2f}")
                print(f"      Potential Savings: ${detection.get('savings_estimate', {}).get('monthly_amount', 0):.2f}/month")
                print(f"      Recommendation: {detection.get('recommendation', 'N/A')}")
                print()
        else:
            print("   No duplicate spend patterns detected\n")
        
        # Yearly Switch Advisor
        print("2. YEARLY SWITCH ADVISOR")
        print("-" * 80)
        yearly_results = results.get("yearly_switch_advisor", {})
        if "recommendations" in yearly_results:
            recs = yearly_results["recommendations"]
            print(f"   Found {len(recs)} yearly switch opportunities\n")
            for i, rec in enumerate(recs, 1):
                vendor = rec.get('vendor', 'N/A')
                print(f"   {i}. {vendor}")
                
                if 'error' in rec:
                    print(f"      Error: {rec.get('error', 'Unknown error')}")
                    if 'raw_response' in rec:
                        print(f"      Response preview: {rec.get('raw_response', '')[:100]}...")
                else:
                    print(f"      Current Monthly: ${rec.get('current_monthly_cost', 0):.2f}")
                    print(f"      Current Yearly (monthly × 12): ${rec.get('current_yearly_cost', 0):.2f}")
                    print(f"      Projected Yearly (20% discount): ${rec.get('projected_yearly_cost', 0):.2f}")
                    print(f"      Yearly Savings: ${rec.get('yearly_savings', 0):.2f}")
                    print(f"      Payback Period: {rec.get('payback_period_months', 0):.1f} months")
                    print(f"      Recommendation: {rec.get('recommendation', 'N/A')}")
                print()
        else:
            print("   No yearly switch opportunities found\n")
        
        # Show total savings if available
        if "total_potential_savings" in yearly_results:
            totals = yearly_results["total_potential_savings"]
            if totals.get('yearly', 0) > 0 or totals.get('monthly', 0) > 0:
                print(f"   Total Potential Savings:")
                print(f"      Monthly: ${totals.get('monthly', 0):.2f}")
                print(f"      Yearly: ${totals.get('yearly', 0):.2f}\n")
        
        # Smart Substitution Advisor
        print("3. AI SMART SUBSTITUTION ADVISOR")
        print("-" * 80)
        sub_results = results.get("smart_substitution_advisor", {})
        if "recommendations" in sub_results:
            recs = sub_results["recommendations"]
            print(f"   Analyzed {len(recs)} substitution opportunities\n")
            for i, rec in enumerate(recs, 1):
                current_vendor = rec.get('current_vendor', 'N/A')
                print(f"   {i}. {current_vendor}")
                print(f"      Recommended Action: {rec.get('recommended_action', 'N/A')}")
                savings = rec.get('potential_savings', 0)
                if savings > 0:
                    print(f"      Potential Savings: ${savings:.2f}/month")
                print(f"      Reasoning: {rec.get('reasoning', 'N/A')[:150]}...")
                print()
        else:
            print("   No substitution opportunities identified\n")
        
        print("="*80)
    
    def save_results(self, results: Dict[str, Any], output_path: str = "analysis_results.json"):
        """Save results to JSON file"""
        output_file = Path(__file__).parent.parent / output_path
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Spend Management AI Agents")
    parser.add_argument(
        "--csv",
        type=str,
        default=None,
        help="Path to CSV file (default: data/mock.csv)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="analysis_results.json",
        help="Output JSON file path"
    )
    
    args = parser.parse_args()
    
    # Initialize orchestrator
    orchestrator = SpendManagementOrchestrator(csv_path=args.csv)
    
    # Run analysis
    results = await orchestrator.run_all_agents()
    
    # Print summary
    orchestrator.print_summary(results)
    
    # Save results
    orchestrator.save_results(results, args.output)
    
    # Show file location
    output_file = Path(__file__).parent.parent / args.output
    print(f"\nResults saved to: {output_file}")
    
    return results


if __name__ == "__main__":
    asyncio.run(main())

