"""Yearly Switch Advisor Agent with Web Search"""
import json
import re
import asyncio
from typing import List, Dict, Any
from .base_agent import BaseAgent
from langchain.schema import HumanMessage, SystemMessage


class YearlySwitchAgent(BaseAgent):
    """Reviews recurring subscriptions and recommends yearly billing switches using real vendor pricing"""
    
    SYSTEM_PROMPT = """You are an expert financial advisor specializing in subscription optimization. 
Your role is to analyze recurring monthly subscriptions (SaaS platforms, cloud services) and determine 
which contracts would be financially advantageous if switched to yearly billing cycles.

Your analysis should:
1. Detect subscriptions with stable monthly spending (consistent amounts over time)
2. Use ACTUAL transaction data from the company's CSV records
3. Calculate potential savings based on typical yearly billing discounts (15-25%, standard is 20%)
4. Calculate payback period accurately
5. Assess impact on cash runway
6. Consider commitment levels and vendor stability

IMPORTANT: The CSV transaction amounts are REAL spending by the company. Use these actual amounts 
to calculate savings when switching to yearly billing with typical SaaS discounts."""

    async def analyze(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze transactions for yearly billing switch opportunities with web search"""
        
        # Filter for monthly recurring subscriptions
        monthly_subscriptions = [
            t for t in transactions 
            if t.get('recurrency', '').lower() == 'monthly' 
            and t.get('expense_type') in ['subscriptions', 'infrastructure']
        ]
        
        if not monthly_subscriptions:
            return {
                "recommendations": [],
                "summary": "No monthly subscriptions found for analysis"
            }
        
        # Group by vendor only (ignore service name variations to properly group)
        vendor_data = {}
        for transaction in monthly_subscriptions:
            vendor = transaction.get('vendor_name', 'Unknown')
            # Group by vendor only - simpler and more reliable
            key = vendor
            
            if key not in vendor_data:
                vendor_data[key] = {
                    'vendor': vendor,
                    'transactions': [],
                    'amounts': []
                }
            
            vendor_data[key]['transactions'].append(transaction)
            vendor_data[key]['amounts'].append(float(transaction.get('amount', 0)))
        
        # Calculate averages for each vendor
        vendor_summaries = []
        for key, data in vendor_data.items():
            amounts = data['amounts']
            if not amounts:
                continue
                
            avg_monthly = sum(amounts) / len(amounts)
            total_yearly = sum(amounts)
            
            # Check for stability - all amounts should be the same (or very close)
            if len(amounts) > 1:
                unique_amounts = set(amounts)
                # Stable if all amounts are within 1% of each other
                if len(unique_amounts) == 1:
                    stability = "stable"
                else:
                    min_amount = min(amounts)
                    max_amount = max(amounts)
                    variance_pct = ((max_amount - min_amount) / avg_monthly) * 100
                    stability = "stable" if variance_pct < 1.0 else "variable"
            else:
                stability = "unknown"
            
            vendor_summaries.append({
                'vendor': data['vendor'],
                'transactions': data['transactions'],
                'avg_monthly_cost': avg_monthly,
                'total_yearly_cost': total_yearly,
                'transaction_count': len(amounts),
                'stability': stability,
                'all_amounts': amounts
            })
        
        # Filter to only stable subscriptions (exclude infrastructure like AWS, GCP, variable spending)
        stable_subscriptions = [
            v for v in vendor_summaries 
            if v['stability'] == 'stable' 
            and v['transaction_count'] >= 3
            and v.get('expense_type', 'subscriptions') != 'infrastructure'  # Exclude infrastructure
        ]
        
        # Also check expense_type from transactions
        final_stable = []
        for v in stable_subscriptions:
            first_tx = v['transactions'][0]
            expense_type = first_tx.get('expense_type', '')
            # Only subscriptions, not infrastructure or variable usage-based
            if expense_type == 'subscriptions':
                final_stable.append(v)
        
        if not final_stable:
            return {
                "recommendations": [],
                "summary": "No stable monthly subscriptions found for yearly switch analysis"
            }
        
        # Format all stable subscriptions for single LLM call (faster!)
        stable_data = []
        for v in final_stable:
            stable_data.append({
                'vendor': v['vendor'],
                'avg_monthly': v['avg_monthly_cost'],
                'yearly_cost': v['total_yearly_cost'],
                'count': v['transaction_count'],
                'amounts': v['all_amounts']
            })
        
        formatted_data = "\n".join([
            f"- {d['vendor']}: ${d['avg_monthly']:.2f}/month (consistent across {d['count']} transactions: {d['amounts']})"
            for d in stable_data
        ])
        
        prompt = f"""Analyze the following stable monthly subscriptions for yearly billing switch opportunities:

STABLE SUBSCRIPTIONS (same amount every month):
{formatted_data}

For each subscription:
1. Current monthly cost (shown above)
2. Current yearly cost if paying monthly (monthly × 12)
3. Estimated yearly cost with 20% discount (standard SaaS annual discount)
4. Potential yearly savings
5. Payback period in months
6. Recommendation: Switch or Don't Switch (only recommend if savings > $100/year and spending is truly stable)

Format as JSON:
{{
    "recommendations": [
        {{
            "vendor": "Vendor Name",
            "current_monthly_cost": 0.0,
            "current_yearly_cost": 0.0,
            "projected_yearly_cost": 0.0,
            "yearly_savings": 0.0,
            "payback_period_months": 0.0,
            "recommendation": "Switch to yearly / Don't switch",
            "reasoning": "Brief explanation"
        }}
    ],
    "summary": "Summary of recommendations"
}}
"""
        
        messages = [
            SystemMessage(content=self.SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ]
        
        response = await self._invoke_llm(messages)
        
        try:
            if "```json" in response:
                json_start = response.find("```json") + 7
                json_end = response.find("```", json_start)
                response = response[json_start:json_end].strip()
            elif "```" in response:
                json_start = response.find("```") + 3
                json_end = response.find("```", json_start)
                response = response[json_start:json_end].strip()
            
            result = json.loads(response)
            return result
        except json.JSONDecodeError:
            return {
                "recommendations": [],
                "summary": "Failed to parse response",
                "raw_response": response[:500]
            }

