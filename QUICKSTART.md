# Quick Start Guide

## 1. Setup Environment

### Windows
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Linux/Mac
```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## 2. Configure API Key

Create a `.env` file in the `Brex-Challenge-Back` directory:

**Windows (PowerShell):**
```powershell
echo "OPENROUTER_API_KEY=your_api_key_here" > .env
```

**Linux/Mac:**
```bash
echo "OPENROUTER_API_KEY=your_api_key_here" > .env
```

Or manually create `.env` with:
```
OPENROUTER_API_KEY=your_openrouter_api_key_here
```

Get your API key from: https://openrouter.ai/keys

## 3. Run Analysis

```bash
# Simple way - uses default CSV (data/mock.csv)
python run_analysis.py

# With custom CSV file
python run_analysis.py path/to/your/data.csv
```

## Output

The analysis will:
- Generate `analysis_results.json` with detailed results
- Print a human-readable summary to the console
- Show recommendations from all three agents

## Three AI Agents

1. **Intelligent Duplicate Spend Detection** - Identifies overlapping vendors
2. **Yearly Switch Advisor** - Recommends switching to yearly billing
3. **AI Smart Substitution Advisor** - Suggests vendor substitutions with web search

All agents run in parallel for faster execution!

