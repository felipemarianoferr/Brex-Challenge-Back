# CSV Generation Prompt - With Pattern Detection Requirements

I need you to generate a CSV file with transaction data that uses REAL, ACTUAL pricing from vendor websites. Please follow these instructions carefully:

**CSV FORMAT:**
The CSV must have exactly these columns (in this order):
transaction_id,amount,currency,datetime,payment_method,src_account,dst_account,vendor_name,start_date,end_date,recurrency,department,expense_type,expense_name

**EXAMPLE ROW:**
T0001,1200.00,USD,2025-01-02 09:00:00,TED,Main Checking,OpenAI,OpenAI Enterprise,2025-01-01,2025-01-31,Monthly,Engineering,subscriptions,Enterprise GPT-5 Plan

**REQUIREMENTS:**

1. **RESEARCH REAL PRICING FIRST:**
   Before generating any transaction row, you MUST research and verify the actual current pricing from the vendor's official website. For example:
   - If generating "Enterprise GPT-5 Plan" from OpenAI, check OpenAI's actual pricing page
   - If generating AWS cloud services, check AWS actual pricing calculator or pricing page
   - If generating Google Ads spending, use realistic Google Ads cost ranges
   - For office rent, use realistic commercial rent rates
   - For salaries, use realistic market rates

2. **PRICING ACCURACY:**
   - The `amount` field MUST match the ACTUAL pricing found on vendor websites
   - Do NOT make up prices or use outdated information
   - If you cannot find exact pricing, use the most current publicly available pricing from 2024-2025
   - For services like AWS, use realistic usage-based costs
   - For subscriptions, use the actual monthly/yearly prices listed

3. **CRITICAL: GENERATE PATTERNS FOR AGENT TESTING**

   The data must include specific patterns that allow spend management agents to detect:

   **A. DUPLICATE SPEND DETECTION PATTERNS:**
   - Include MULTIPLE vendors providing the SAME TYPE of service (to test duplicate detection):
     * Example: Both OpenAI and Anthropic (Claude) for AI inference
     * Example: Both AWS and Google Cloud Platform for cloud infrastructure
     * Example: Both Slack and Microsoft Teams for collaboration
     * Example: Both Canva and Figma for design tools
   - These should be ACTIVE at the SAME TIME (overlapping periods)
   - Use REAL pricing from each vendor's website
   - Make sure the amounts are realistic for duplicate spend opportunities

   **B. YEARLY SWITCH ADVISOR PATTERNS:**
   - Include STABLE monthly subscriptions (consistent amounts across months) that would benefit from yearly billing:
     * Same vendor, same service, same amount every month
     * Examples: GitHub Pro, Notion, Linear, other SaaS tools with yearly discounts
   - Include VARIABLE monthly subscriptions (amounts change) that should NOT switch to yearly:
     * Usage-based services like AWS (amounts vary by month)
     * Ad spend that fluctuates seasonally
   - Research actual yearly pricing from vendor websites (usually 15-25% discount)
   - Make sure stable subscriptions have the same amount every month

   **C. SMART SUBSTITUTION ADVISOR PATTERNS:**
   - Include multiple vendors in the SAME category but with DIFFERENT pricing:
     * Example: AWS ($3000/month) vs Google Cloud ($2800/month) - both cloud infrastructure
     * Example: Slack ($600/month) vs Microsoft Teams ($500/month) - both collaboration
     * Example: Canva ($200/month) vs Figma ($400/month) - both design tools
   - These should have overlapping usage periods
   - Use REAL pricing comparisons from vendor websites
   - Include cases where one vendor is clearly more expensive

4. **TRANSACTION STRUCTURE:**
   Generate 12 months of data (January 2025 through December 2025) with:
   - Multiple recurring subscriptions (SaaS tools, cloud services)
   - Office rent (consistent monthly)
   - Infrastructure costs (AWS, GCP, Azure - with realistic variation)
   - Marketing/advertising spend (Google Ads, Facebook Ads - with seasonal variation)
   - Salaries (consistent monthly)
   - Equipment purchases (quarterly)
   - One-time expenses (onboarding, equipment)

5. **SPECIFIC PATTERNS TO INCLUDE:**

   **Duplicate Spend Examples (must overlap in time):**
   - OpenAI + Anthropic (both AI inference, both active monthly)
   - AWS + Google Cloud (both cloud infrastructure, both active monthly)
   - Slack + Microsoft Teams (both collaboration tools, both active monthly)
   - Canva + Figma (both design tools, both active monthly)

   **Yearly Switch Candidates (stable monthly amounts):**
   - GitHub Pro: Same amount every month (check actual pricing)
   - Notion: Same amount every month
   - Linear: Same amount every month
   - Other SaaS with stable pricing

   **Variable Spend (should NOT switch to yearly):**
   - AWS: Vary amounts month-to-month (3200, 3500, 3800, 4000, 4500, etc.)
   - Google Ads: Seasonal variation (400, 350, 380, 420, 400, etc.)
   - Infrastructure costs: Show realistic variation

   **Substitution Candidates:**
   - Same category, different vendors, different pricing
   - Make sure pricing differences are significant enough to detect

6. **FIELD DETAILS:**
   - `transaction_id`: Sequential (T0001, T0002, etc.)
   - `amount`: REAL pricing from vendor websites (use 2 decimal places)
   - `currency`: USD
   - `datetime`: Realistic timestamps (YYYY-MM-DD HH:MM:SS format)
   - `payment_method`: TED, PIX, WIRE (vary appropriately)
   - `src_account`: Main Checking, Cloud Account, Payroll Account, Marketing Account
   - `dst_account`: Vendor name or account
   - `vendor_name`: Real vendor company names
   - `start_date`: Start of billing period (YYYY-MM-DD)
   - `end_date`: End of billing period (YYYY-MM-DD)
   - `recurrency`: Monthly, Yearly, Quarterly, Bimonthly, One-time
   - `department`: Engineering, Operations, Marketing, HR, Sales
   - `expense_type`: subscriptions, infrastructure, rent, ads, salaries, equipment, onboarding
   - `expense_name`: Specific service/product name (e.g., "Enterprise GPT-5 Plan")

7. **DATA CONSISTENCY:**
   - Recurring monthly subscriptions should have consistent amounts for yearly switch detection
   - Infrastructure costs (AWS, cloud) should vary month-to-month (shows usage-based)
   - Marketing spend should have seasonal variations
   - Salaries are always consistent
   - Duplicate vendors must have overlapping dates (same months)

8. **IMPORTANT:**
   - Research actual pricing from official vendor websites for each service
   - Do NOT use placeholder or estimated prices - use REAL current pricing
   - If a service doesn't have public pricing, use realistic market rates based on similar services
   - Ensure the CSV is valid and can be parsed by Python's csv module
   - MAKE SURE duplicate spend patterns are active at the same time
   - MAKE SURE stable subscriptions have identical amounts each month
   - MAKE SURE variable spend shows realistic variation

**OUTPUT FORMAT:**
Generate the complete CSV file with a header row and at least 60-70 transaction rows covering 12 months of data. Make sure to include the header row as the first line.

**VERIFICATION CHECKLIST:**
Before generating, verify:
- [ ] At least 3-4 duplicate spend opportunities (same category, different vendors, overlapping periods)
- [ ] At least 5-6 stable monthly subscriptions (same amount every month) for yearly switch analysis
- [ ] Variable spending patterns (AWS, ads) that should NOT switch to yearly
- [ ] Multiple vendors in same categories for substitution analysis
- [ ] All pricing is verified from vendor websites
- [ ] Data spans 12 months (Jan-Dec 2025)

Start by researching the actual pricing for:
1. OpenAI Enterprise plans
2. Anthropic (Claude) plans (for duplicate detection with OpenAI)
3. AWS EC2/Cloud services pricing (with variation)
4. Google Cloud Platform pricing (for duplicate detection with AWS)
5. Google Ads typical monthly spend (with seasonal variation)
6. Slack and Microsoft Teams pricing (for duplicate detection)
7. Canva and Figma pricing (for duplicate detection)
8. Office rent in a major city (e.g., San Francisco, New York, Austin)
9. Popular SaaS tools with stable pricing (GitHub, Notion, Linear, etc.)

Then generate the CSV with these verified, real pricing amounts and the specific patterns described above.

