"""AI Smart Substitution Advisor Agent with Web Search"""
import json
import asyncio
from typing import List, Dict, Any
from .base_agent import BaseAgent
from langchain.schema import HumanMessage, SystemMessage


class SubstitutionAgent(BaseAgent):
    """Identifies similar tools/services and recommends substitutions based on cost and efficiency"""
    
    SYSTEM_PROMPT = """You are an expert technology and financial advisor specializing in tool stack optimization. 
Your role is to identify tools and services that fulfill similar roles (e.g., Canva vs Figma, Slack vs Teams, 
AWS vs GCP) and recommend which one to keep based on:
- Cost effectiveness (using actual transaction data)
- Actual spending comparison from CSV records
- Feature overlap and efficiency (using general knowledge)
- Market position and vendor reliability

IMPORTANT: Use ACTUAL transaction amounts from the company's CSV to compare vendor costs. 
The transaction data shows real spending, which is the most reliable source for cost comparison."""

    async def analyze(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze transactions and recommend substitutions"""
        self.transactions = transactions
        
        # Group vendors by expense category to find similar tools
        category_vendors = {}
        for transaction in transactions:
            category = transaction.get('expense_type', 'other')
            vendor = transaction.get('vendor_name', 'Unknown')
            
            if category not in category_vendors:
                category_vendors[category] = {}
            
            if vendor not in category_vendors[category]:
                category_vendors[category][vendor] = []
            
            category_vendors[category][vendor].append(transaction)
        
        # Identify categories with multiple vendors (potential substitution opportunities)
        substitution_opportunities = []
        
        for category, vendors in category_vendors.items():
            if len(vendors) > 1 and category in ['subscriptions', 'infrastructure', 'software']:
                for vendor, vendor_transactions in vendors.items():
                    avg_monthly = sum(t['amount'] for t in vendor_transactions) / len(vendor_transactions)
                    substitution_opportunities.append({
                        'category': category,
                        'vendor': vendor,
                        'transactions': vendor_transactions,
                        'avg_monthly_cost': avg_monthly,
                        'alternative_vendors': [v for v in vendors.keys() if v != vendor]
                    })
        
        if not substitution_opportunities:
            return {
                "recommendations": [],
                "summary": "No substitution opportunities identified"
            }
        
        # Filter to only compare similar tools (infrastructure vs infrastructure, AI vs AI, design vs design)
        meaningful_opportunities = []
        for opp in substitution_opportunities:
            vendor = opp['vendor'].lower()
            alts = [a.lower() for a in opp['alternative_vendors']]
            
            # Infrastructure: AWS vs GCP
            if opp['category'] == 'infrastructure':
                meaningful_opportunities.append(opp)
            # AI services: OpenAI vs Anthropic
            elif any(v in vendor for v in ['openai', 'anthropic']) and any(any(v in a for v in ['openai', 'anthropic']) for a in alts):
                meaningful_opportunities.append(opp)
            # Design tools: Figma vs Canva
            elif any(v in vendor for v in ['figma', 'canva']) and any(any(v in a for v in ['figma', 'canva']) for a in alts):
                meaningful_opportunities.append(opp)
        
        if not meaningful_opportunities:
            return {
                "recommendations": [],
                "summary": "No meaningful substitution opportunities found"
            }
        
            # Get all vendor costs for comparison
        all_opps_data = []
        for opp in meaningful_opportunities:
            vendor = opp['vendor']
            current_cost = opp['avg_monthly_cost']
            
            alt_costs = {}
            for alt_vendor in opp['alternative_vendors']:
                alt_tx = [t for t in self.transactions 
                         if t.get('vendor_name') == alt_vendor 
                         and t.get('expense_type') == opp['category']]
                if alt_tx:
                    alt_avg = sum(float(t.get('amount', 0)) for t in alt_tx) / len(alt_tx)
                    alt_costs[alt_vendor] = alt_avg
            
            all_opps_data.append({
                'current_vendor': vendor,
                'category': opp['category'],
                'current_cost': current_cost,
                'alternatives': alt_costs
            })
        
        formatted_opps = "\n".join([
            f"- {d['current_vendor']} ({d['category']}): ${d['current_cost']:.2f}/month vs {', '.join([f'{v} ${c:.2f}/month' for v, c in d['alternatives'].items()])}"
            for d in all_opps_data
        ])
        
        prompt = f"""Analyze vendor substitution opportunities based on ACTUAL transaction data:

{formatted_opps}

For each pair, determine:
1. Should company keep current vendor or switch to alternative?
2. Potential monthly savings from switching
3. Reasoning based on cost comparison and feature overlap

Format as JSON:
{{
    "recommendations": [
        {{
            "current_vendor": "Vendor Name",
            "category": "Category",
            "recommended_action": "Keep Current / Switch to [Alternative]",
            "potential_savings": 0.0,
            "reasoning": "Brief explanation"
        }}
    ],
    "summary": "Summary of substitution recommendations"
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

