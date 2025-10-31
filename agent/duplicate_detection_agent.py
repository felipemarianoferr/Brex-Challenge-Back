"""Intelligent Duplicate Spend Detection Agent"""
import json
from typing import List, Dict, Any
from .base_agent import BaseAgent
from langchain.schema import HumanMessage, SystemMessage


class DuplicateDetectionAgent(BaseAgent):
    """Identifies vendors providing services with the same function"""
    
    SYSTEM_PROMPT = """You are an expert financial analyst specializing in identifying duplicate spend patterns. 
Your role is to analyze transaction data and identify different vendors that provide services with the same function.

Your analysis should:
1. Identify category overlap (e.g., multiple AI inference services, cloud providers)
2. Detect spending recurrence patterns
3. Analyze department usage patterns
4. Calculate spending correlation across vendors
5. Estimate potential savings if one supplier is consolidated

For each duplicate spend detection, provide:
- The vendors involved
- The category/function they serve
- Current combined spending
- Estimated savings if consolidated
- Reasoning for consolidation recommendation

Be thorough and data-driven in your analysis."""

    async def analyze(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze transactions for duplicate spend patterns"""
        
        # Group by expense type and vendor
        formatted_data = self.format_transactions_for_analysis(transactions)
        
        # Create analysis prompt
        prompt = f"""Analyze the following transaction data for duplicate spend patterns:

{formatted_data}

Identify:
1. Vendors providing similar services (e.g., OpenAI GPT-5 and other AI inference services)
2. Overlapping subscriptions or infrastructure services
3. Potential consolidation opportunities
4. Estimated savings from consolidating vendors

For each duplicate spend opportunity found, provide:
- Vendor names involved
- Service category/function
- Current monthly/yearly spending for each vendor
- Estimated savings percentage and amount if consolidated
- Recommendation reasoning

Format your response as JSON with the following structure:
{{
    "duplicate_detections": [
        {{
            "vendors": ["Vendor A", "Vendor B"],
            "category": "Service Category",
            "current_spending": {{
                "vendor_a_monthly": 0.0,
                "vendor_b_monthly": 0.0,
                "total_monthly": 0.0,
                "total_yearly": 0.0
            }},
            "savings_estimate": {{
                "percentage": 0.0,
                "monthly_amount": 0.0,
                "yearly_amount": 0.0
            }},
            "reasoning": "Explanation of why these are duplicates and should be consolidated",
            "recommendation": "Which vendor to keep and why"
        }}
    ],
    "summary": "Overall summary of duplicate spend findings"
}}
"""
        
        messages = [
            SystemMessage(content=self.SYSTEM_PROMPT),
            HumanMessage(content=prompt)
        ]
        
        response = await self._invoke_llm(messages)
        
        # Try to parse JSON from response
        try:
            # Extract JSON from response if wrapped in markdown code blocks
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
            # If JSON parsing fails, return the raw response
            return {
                "raw_response": response,
                "error": "Failed to parse JSON response"
            }

