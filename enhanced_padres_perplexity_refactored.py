"""
Refactored Enhanced Padres Perplexity Research Module

Key improvements:
- Async/await throughout
- Connection pooling with aiohttp
- Better resource management with context managers
- Improved error handling
- Structured logging
"""

import os
import json
import logging
import asyncio
from datetime import datetime
from typing import Optional, Dict, Any
from dotenv import load_dotenv

import aiohttp
import google.generativeai as genai

# Internal imports
from run_single_padres_test import PadresTest

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv(override=True)


class SimplePadresResearch:
    """
    Async research automation with proper connection management.

    Improvements:
    - Connection pooling for HTTP requests
    - Async/await for all I/O operations
    - Proper resource cleanup
    - Better error handling
    """

    def __init__(self):
        """Initialize research automation with all required services."""
        logger.info("Initializing SimplePadresResearch with Gemini...")

        # PadresTest - set use_llm=False if we're the sole LLM interactor
        self.padres = PadresTest(use_llm=False)

        # API keys
        self.perplexity_key = os.getenv('PERPLEXITY_API_KEY')
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')

        # HTTP session (will be created lazily)
        self._session: Optional[aiohttp.ClientSession] = None
        self._session_lock = asyncio.Lock()

        # Initialize Gemini
        self._init_gemini()

        if not self.perplexity_key:
            logger.warning("PERPLEXITY_API_KEY not found. Perplexity searches will fail.")

        logger.info("SimplePadresResearch initialization complete.")

    def _init_gemini(self):
        """Initialize Gemini client."""
        if not self.gemini_api_key:
            logger.warning("GEMINI_API_KEY not found. Gemini calls will fail.")
            self.gemini_model = None
            return

        try:
            genai.configure(api_key=self.gemini_api_key)
            self.gemini_model = genai.GenerativeModel('gemini-1.5-flash-latest')
            logger.info("Gemini client configured (gemini-1.5-flash-latest)")
        except Exception as e:
            logger.error(f"Failed to configure Gemini: {e}", exc_info=True)
            self.gemini_model = None

    async def get_session(self) -> aiohttp.ClientSession:
        """
        Get or create HTTP session with connection pooling.

        This implements proper connection pooling for all HTTP requests.
        """
        if self._session is None or self._session.closed:
            async with self._session_lock:
                if self._session is None or self._session.closed:
                    # Configure connector with connection pooling
                    connector = aiohttp.TCPConnector(
                        limit=100,  # Max total connections
                        limit_per_host=30,  # Max connections per host
                        ttl_dns_cache=300,  # DNS cache TTL in seconds
                        enable_cleanup_closed=True
                    )

                    # Configure timeout
                    timeout = aiohttp.ClientTimeout(
                        total=60,  # Total timeout for request
                        connect=10,  # Connection timeout
                        sock_read=30  # Socket read timeout
                    )

                    self._session = aiohttp.ClientSession(
                        connector=connector,
                        timeout=timeout,
                        raise_for_status=True  # Automatically raise for 4xx/5xx
                    )
                    logger.info("Created new aiohttp session with connection pooling")

        return self._session

    async def cleanup(self):
        """Cleanup HTTP session and resources."""
        if self._session and not self._session.closed:
            await self._session.close()
            logger.info("HTTP session closed")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.cleanup()

    def call_llm_for_text(self, prompt_text: str) -> str:
        """
        Call Gemini to generate text.

        Note: This is still synchronous because google.generativeai
        doesn't have async support yet. If needed, we can wrap in
        asyncio.to_thread() to avoid blocking.
        """
        if not self.gemini_model:
            logger.error("Gemini model not initialized")
            return "[Error: Gemini model not available]"

        logger.info(f"Sending prompt to Gemini (length: {len(prompt_text)})")

        try:
            response = self.gemini_model.generate_content(prompt_text)

            # Extract text from response
            generated_text = ""
            if response.parts:
                generated_text = "".join(
                    part.text for part in response.parts if hasattr(part, 'text')
                )
            elif hasattr(response, 'text') and response.text:
                generated_text = response.text
            else:
                # Fallback: try to find text in candidates
                logger.warning("Unexpected Gemini response structure")
                if hasattr(response, 'candidates') and response.candidates:
                    for candidate in response.candidates:
                        if hasattr(candidate, 'content') and \
                           hasattr(candidate.content, 'parts') and \
                           candidate.content.parts:
                            for part in candidate.content.parts:
                                if hasattr(part, 'text'):
                                    generated_text += part.text
                            if generated_text:
                                break

            if not generated_text:
                logger.warning("No text found in Gemini response")
                return "[Error: No text in Gemini response]"

            logger.info(f"Received Gemini response (length: {len(generated_text)})")
            return generated_text

        except Exception as e:
            logger.error(f"Gemini API error: {e}", exc_info=True)
            return f"[Error interacting with Gemini: {e}]"

    async def call_llm_for_text_async(self, prompt_text: str) -> str:
        """
        Async wrapper for Gemini LLM call.

        Runs the synchronous Gemini call in a thread pool to avoid blocking.
        """
        return await asyncio.to_thread(self.call_llm_for_text, prompt_text)

    async def search_perplexity(self, query: str) -> str:
        """
        Async Perplexity API call with connection pooling.

        This is now properly async and uses the connection pool.
        """
        if not self.perplexity_key:
            logger.error("Perplexity API key not found")
            return "Error: Perplexity API key not found"

        logger.info(f"Querying Perplexity: {query[:100]}...")

        try:
            session = await self.get_session()

            headers = {
                "Authorization": f"Bearer {self.perplexity_key}",
                "Content-Type": "application/json"
            }

            data = {
                "model": "sonar",
                "messages": [{"role": "user", "content": query}],
                "max_tokens": 1000
            }

            async with session.post(
                "https://api.perplexity.ai/chat/completions",
                headers=headers,
                json=data
            ) as response:
                result = await response.json()
                generated_text = result['choices'][0]['message']['content']
                logger.info("Received response from Perplexity")
                return generated_text

        except aiohttp.ClientResponseError as e:
            error_msg = f"Perplexity HTTP Error: {e.status}"
            logger.error(error_msg, exc_info=True)
            return error_msg
        except asyncio.TimeoutError:
            error_msg = "Perplexity request timed out"
            logger.error(error_msg)
            return error_msg
        except Exception as e:
            error_msg = f"Perplexity API error: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg

    async def run_research_experiment(self) -> Dict[str, Any]:
        """
        Run a single research experiment: Padres -> Gemini analysis.

        Now fully async with proper error handling.
        """
        logger.info("=== Running Single Research Experiment (Padres -> Gemini) ===")

        # 1. Run Padres experiment
        logger.info("1. Running Padres experiment...")
        # Note: If PadresTest has async methods, use them here
        # For now assuming test_padres_api() is sync
        padres_result_raw = await asyncio.to_thread(self.padres.test_padres_api)

        # Extract observation
        observation_for_llm = padres_result_raw.get(
            'observation',
            "No observation provided by Padres API."
        )

        # Check for errors
        if isinstance(padres_result_raw.get('status'), dict) and \
           padres_result_raw['status'].get('api_status', '').endswith("ERROR"):
            logger.warning(f"Padres API error: {padres_result_raw['status']}")
            observation_for_llm = (
                f"Padres API Error: "
                f"{padres_result_raw['status'].get('error_message', json.dumps(padres_result_raw['status']))}"
            )
        elif not observation_for_llm and isinstance(padres_result_raw, dict):
            observation_for_llm = json.dumps(padres_result_raw)

        # 2. Analyze with Gemini
        llm_analysis_prompt = (
            f"Analyze the following spatial simulation data and provide insights.\n\n"
            f"Simulation Data:\n{observation_for_llm}"
        )
        logger.info("2. Analyzing with LLM (Gemini)...")
        llm_generated_analysis = await self.call_llm_for_text_async(llm_analysis_prompt)

        # 3. Determine success
        action_result = padres_result_raw.get('action', {})
        is_padres_success = False

        if isinstance(action_result, dict):
            if action_result.get('status') == 'SUCCESS':
                is_padres_success = True
            elif (action_result.get('done') is True and
                  isinstance(action_result.get('reward'), (int, float)) and
                  action_result.get('reward', 0) > 0):
                is_padres_success = True
            elif (isinstance(padres_result_raw.get('status'), dict) and
                  padres_result_raw['status'].get('api_status', '').endswith("ERROR")):
                is_padres_success = False

        # 4. Build result
        current_timestamp = datetime.utcnow().isoformat() + "Z"
        experiment_core_data = {
            'experiment_id': current_timestamp,
            'timestamp': current_timestamp,
            'padres_api_response': padres_result_raw,
            'padres_success': is_padres_success,
            'score': action_result.get('reward', 0) if isinstance(action_result, dict) else 0,
            'distance': action_result.get('distance', 0) if isinstance(action_result, dict) else 0,
            'task_completed': action_result.get('done', False) if isinstance(action_result, dict) else False,
            'llm_analysis': llm_generated_analysis
        }

        logger.info(
            f"Experiment processed. ID: {current_timestamp}, "
            f"Success: {is_padres_success}"
        )

        return experiment_core_data


# Example usage
async def main():
    """Example of proper usage with context manager."""
    load_dotenv()

    logger.info("Running SimplePadresResearch with connection pooling...")

    # Check required env vars
    if not os.getenv("GEMINI_API_KEY"):
        print("Error: GEMINI_API_KEY not found")
        return
    if not os.getenv("PADRES_API_URL"):
        print("Error: PADRES_API_URL not found")
        return

    # Use async context manager for proper cleanup
    async with SimplePadresResearch() as researcher:
        # Run experiment
        results = await researcher.run_research_experiment()
        logger.info("--- Experiment Complete ---")
        logger.info(json.dumps(results, indent=2))

        # Test Perplexity if key available
        if os.getenv("PERPLEXITY_API_KEY"):
            logger.info("\n--- Testing Perplexity Search ---")
            pq_result = await researcher.search_perplexity("Latest in AI for robotics")
            logger.info(f"Perplexity Result: {pq_result[:500]}...")


if __name__ == '__main__':
    asyncio.run(main())
