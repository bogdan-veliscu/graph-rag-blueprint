"""Async LLM client wrapper for parallel processing."""

import asyncio
import logging
from typing import Optional

import httpx

from src.graph_rag.config import config

logger = logging.getLogger(__name__)


class AsyncLLMClient:
    """Async LLM client for parallel query processing."""

    def __init__(self, max_concurrent: Optional[int] = None):
        """Initialize async LLM client.

        Args:
            max_concurrent: Maximum concurrent requests (defaults to config.max_concurrent)
        """
        self.provider = config.llm_provider
        self.temperature = config.llm_temperature
        self.max_tokens = config.llm_max_tokens
        self.max_concurrent = max_concurrent or config.max_concurrent
        self.semaphore = asyncio.Semaphore(self.max_concurrent)

    async def generate(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate text from prompt asynchronously.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt

        Returns:
            Generated text
        """
        async with self.semaphore:
            if self.provider == "ollama":
                return await self._generate_ollama(prompt, system_prompt)
            elif self.provider == "anthropic":
                return await self._generate_anthropic(prompt, system_prompt)
            else:
                raise ValueError(f"Unknown LLM provider: {self.provider}")

    async def _generate_ollama(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate using Ollama asynchronously.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt

        Returns:
            Generated text
        """
        url = f"{config.ollama_base_url}/api/generate"
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        payload = {
            "model": config.ollama_model,
            "prompt": full_prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
            },
        }

        max_retries = 3
        timeout = 300.0  # 5 minutes timeout
        
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(url, json=payload)
                    response.raise_for_status()
                    result = response.json()
                    answer = result.get("response", "")
                    if not answer:
                        logger.warning("Ollama returned empty response")
                        if attempt < max_retries - 1:
                            continue
                    return answer
            except httpx.TimeoutException as e:
                logger.warning(f"Ollama timeout (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    raise TimeoutError(f"Ollama request timed out after {max_retries} attempts")
            except httpx.ConnectError as e:
                logger.error(f"Ollama connection error: {e}")
                raise ConnectionError(f"Cannot connect to Ollama at {config.ollama_base_url}. Is Ollama running?")
            except httpx.HTTPStatusError as e:
                logger.error(f"Ollama HTTP error: {e}")
                if e.response.status_code >= 500 and attempt < max_retries - 1:
                    # Retry on server errors
                    continue
                raise
            except Exception as e:
                logger.error(f"Ollama generation error: {e}")
                if attempt < max_retries - 1:
                    continue
                raise
        
        raise RuntimeError("Failed to generate response after all retries")

    async def _generate_anthropic(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """Generate using Anthropic API asynchronously.

        Args:
            prompt: User prompt
            system_prompt: Optional system prompt

        Returns:
            Generated text
        """
        if not config.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")

        url = config.anthropic_base_url
        headers = {
            "x-api-key": config.anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

        messages = [{"role": "user", "content": prompt}]
        if system_prompt:
            system = system_prompt
        else:
            system = "You are a helpful assistant."

        payload = {
            "model": "claude-3-5-sonnet-20241022",
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "system": system,
            "messages": messages,
        }

        max_retries = 3
        timeout = 300.0  # 5 minutes timeout
        
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(url, headers=headers, json=payload)
                    response.raise_for_status()
                    result = response.json()
                    answer = result.get("content", [{}])[0].get("text", "")
                    if not answer:
                        logger.warning("Anthropic returned empty response")
                        if attempt < max_retries - 1:
                            continue
                    return answer
            except httpx.TimeoutException as e:
                logger.warning(f"Anthropic timeout (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    raise TimeoutError(f"Anthropic request timed out after {max_retries} attempts")
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 401:
                    raise ValueError("Invalid Anthropic API key")
                elif e.response.status_code == 429:
                    logger.warning(f"Rate limited (attempt {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        import asyncio
                        await asyncio.sleep(2 ** attempt)  # Exponential backoff
                        continue
                logger.error(f"Anthropic HTTP error: {e}")
                if e.response.status_code >= 500 and attempt < max_retries - 1:
                    # Retry on server errors
                    continue
                raise
            except Exception as e:
                logger.error(f"Anthropic generation error: {e}")
                if attempt < max_retries - 1:
                    continue
                raise
        
        raise RuntimeError("Failed to generate response after all retries")

