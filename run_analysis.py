"""Simple script to run spend management analysis"""
import asyncio
import sys
from pathlib import Path

# Add agent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from agent.orchestrator import SpendManagementOrchestrator


async def main():
    """Run the analysis"""
    # Get CSV path from command line or use default
    csv_path = sys.argv[1] if len(sys.argv) > 1 else None
    
    # Initialize orchestrator
    orchestrator = SpendManagementOrchestrator(csv_path=csv_path)
    
    # Load data
    orchestrator.load_data()
    
    # Run analysis
    results = await orchestrator.run_all_agents()
    
    # Print summary
    orchestrator.print_summary(results)
    
    # Save results
    orchestrator.save_results(results)
    
    return results


if __name__ == "__main__":
    asyncio.run(main())

