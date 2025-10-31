"""Base agent class with LangChain and OpenRouter integration"""
from typing import Any, Dict, List, Optional
try:
    from langchain_openai import ChatOpenAI
    from langchain.schema import HumanMessage, SystemMessage
    from langchain_community.tools import DuckDuckGoSearchRun
except ImportError:
    # Fallback for older langchain versions
    try:
        from langchain.chat_models import ChatOpenAI
        from langchain.schema import HumanMessage, SystemMessage
        from langchain.tools import DuckDuckGoSearchRun
    except ImportError:
        raise ImportError(
            "Please install langchain and related packages: "
            "pip install -r requirements.txt"
        )

from .config import Config


class BaseAgent:
    """Base class for all spend management agents"""
    
    def __init__(self, model_name: Optional[str] = None):
        """Initialize base agent with LangChain and OpenRouter"""
        Config.validate()
        
        model = model_name or Config.DEFAULT_MODEL
        
        # Configure OpenRouter endpoint with Descartes model and Groq provider
        # Using the exact format from the user's example
        self.llm = ChatOpenAI(
            model=model,
            api_key=Config.OPENROUTER_API_KEY,
            base_url=Config.OPENROUTER_BASE_URL,
            temperature=Config.TEMPERATURE,
            model_kwargs={
                "parallel_tool_calls": False,
                "extra_body": {
                    "provider": {
                        "order": Config.get_provider_order(),  # ["groq"] by default
                        "allow_fallbacks": Config.ALLOW_FALLBACKS  # False by default
                    }
                }
            }
        )
        
        # Web search tool for cost comparisons
        self.search_tool = DuckDuckGoSearchRun()
    
    async def _invoke_llm(self, messages: List) -> str:
        """Invoke the language model asynchronously"""
        # Note: LangChain's ChatOpenAI doesn't have native async for OpenRouter
        # We'll use sync but wrap in executor for true async
        import asyncio
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(None, lambda: self.llm(messages))
        return response.content
    
    async def search_web(self, query: str) -> str:
        """Search the web for information - OPTIONAL, non-blocking, disabled by default"""
        from .config import Config
        
        # Web search is disabled by default to avoid rate limiting
        if not Config.USE_WEB_SEARCH:
            return "Web search disabled. Analysis based on transaction data and general market knowledge."
        
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, lambda: self.search_tool.run(query))
            await asyncio.sleep(1)  # Brief delay to avoid rate limits
            return result
        except Exception as e:
            # Don't retry - just skip and continue without web search
            return "Web search unavailable. Analysis will use transaction data and general market knowledge."
    
    def format_transactions_for_analysis(self, transactions: List[Dict[str, Any]]) -> str:
        """Format transaction data for LLM analysis"""
        formatted = []
        for t in transactions:
            formatted.append(
                f"ID: {t.get('transaction_id')}, "
                f"Vendor: {t.get('vendor_name')}, "
                f"Amount: ${t.get('amount'):.2f} {t.get('currency')}, "
                f"Date: {t.get('datetime')}, "
                f"Recurrency: {t.get('recurrency')}, "
                f"Department: {t.get('department')}, "
                f"Type: {t.get('expense_type')}, "
                f"Name: {t.get('expense_name')}"
            )
        return "\n".join(formatted)

