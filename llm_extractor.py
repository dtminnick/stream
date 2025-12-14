
"""
LLM-based Process Flow Extractor
================================

This module provides the `ProcessFlowExtractor` class, which uses Large Language Models (LLMs)
to analyze Standard Operating Procedure (SOP) documents and extract structured process flow information.

Supported Providers:
--------------------
- OpenAI (default)
- Anthropic
- Custom HTTP API (OpenAI-compatible format)

Features:
---------
- Configurable prompt templates (default, custom, or file-based)
- Provider-agnostic API calls (OpenAI, Anthropic, or custom REST API)
- Extraction of structured JSON process flows:
  - Process name and description
  - Sequential steps with inputs, outputs, roles, decision points
  - Tools, systems, compliance requirements
- Batch extraction from multiple documents
- Logging of successes, warnings, and errors

Example:
--------
    >>> extractor = ProcessFlowExtractor(api_key="sk-...", provider="openai")
    >>> flow = extractor.extract_process_flow(document_content="SOP text...", document_name="SOP1")
    >>> print(flow["steps"][0]["step_name"])
"""

import json
import logging
from typing import Dict, List, Optional, Any
import os
from pathlib import Path
import re

try:
    import openai
    openai_available = True
except ImportError:
    openai_available = False

try:
    import requests
    requests_available = True
except ImportError:
    requests_available = False

logger = logging.getLogger(__name__)

def safe_json_loads(response_text: str):
    import re, json
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if not match:
            raise ValueError("No JSON object found in response")

        cleaned = match.group(0)
        cleaned = re.sub(r"//.*", "", cleaned)
        cleaned = re.sub(r",(\s*[\]}])", r"\1", cleaned)

        # Try parsing again
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError:
            # If still invalid, try to auto‑close arrays/objects
            if not cleaned.strip().endswith("}"):
                cleaned += "}"  # add closing brace
            if cleaned.count("[") > cleaned.count("]"):
                cleaned += "]"  # add closing bracket
            return json.loads(cleaned)

class FlowExtractor:
    """
    ProcessFlowExtractor
    --------------------

    A utility class for extracting structured process flow information from SOP documents using LLMs.

    Attributes:
    -----------
    model : str
        Model name to use (default: "gpt-4o-mini").
    temperature : float
        Sampling temperature (lower = more deterministic).
    max_tokens : int
        Maximum tokens in the response.
    provider : str
        LLM provider ("openai", "anthropic", or "custom").
    api_base_url : Optional[str]
        Base URL for custom API provider.
    prompt_template : str
        Prompt template used for extraction.
    api_key : Optional[str]
        API key for the chosen provider.
    """

    default_prompt = """You are an expert at analyzing Standard Operating Procedures (SOPs) and extracting structured process flow information.

    [Prompt truncated for brevity in docstring; see class definition for full template]
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        temperature: float = 0.1,
        max_tokens: int = 2000,
        custom_prompt: Optional[str] = None,
        prompt_file: Optional[str] = None,
        provider: str = "openai",
        api_base_url: Optional[str] = None
    ):
        """
        Initialize the ProcessFlowExtractor.

        Parameters:
        -----------
        api_key : Optional[str]
            API key for the LLM provider (or set via environment variable).
        model : str, default="gpt-4o-mini"
            Model to use for extraction.
        temperature : float, default=0.1
            Sampling temperature (lower = more deterministic).
        max_tokens : int, default=2000
            Maximum tokens in the response.
        custom_prompt : Optional[str]
            Custom prompt template (overridden by prompt_file if provided).
        prompt_file : Optional[str]
            Path to text file containing the prompt template.
        provider : str, default="openai"
            LLM provider ("openai", "anthropic", or "custom").
        api_base_url : Optional[str]
            Base URL for custom API provider (required if provider="custom").

        Raises:
        -------
        ImportError
            If required libraries for the chosen provider are not installed.
        ValueError
            If required API keys or parameters are missing.
        """
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.provider = provider.lower()
        self.api_base_url = api_base_url
        
        # Load prompt from file if provided, otherwise use custom_prompt or default
        if prompt_file:
            self.prompt_template = self._load_prompt_from_file(prompt_file)
        else:
            self.prompt_template = custom_prompt or self.default_prompt
        
        # Initialize provider-specific clients
        if self.provider == "openai":
            if not openai_available:
                raise ImportError(
                    "OpenAI library is required. Install with: pip install openai"
                )
            
            self.api_key = api_key or os.getenv("OPENAI_API_KEY")
            if not self.api_key:
                raise ValueError(
                    "OpenAI API key is required. Provide via api_key parameter or "
                    "set OPENAI_API_KEY environment variable."
                )
            
            self.client = openai.OpenAI(api_key=self.api_key)
            
        elif self.provider == "anthropic":
            try:
                import anthropic
                self.anthropic_client = anthropic.Anthropic(api_key=api_key or os.getenv("ANTHROPIC_API_KEY"))
                self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
                if not self.api_key:
                    raise ValueError(
                        "Anthropic API key is required. Provide via api_key parameter or "
                        "set ANTHROPIC_API_KEY environment variable."
                    )
            except ImportError:
                raise ImportError(
                    "Anthropic library is required. Install with: pip install anthropic"
                )

        elif self.provider == "ollama":
            # Ollama runs locally, no API key required
            self.api_key = api_key or "none"
            self.api_base_url = api_base_url or "http://localhost:11434/v1/chat/completions"
            if not requests_available:
                raise ImportError(
                "Requests library is required for Ollama. Install with: pip install requests"
            )

        elif self.provider == "custom":
            if not requests_available:
                raise ImportError(
                    "Requests library is required for custom API. Install with: pip install requests"
                )
            if not api_base_url:
                raise ValueError(
                    "api_base_url is required when provider='custom'"
                )
            self.api_key = api_key
            if not self.api_key:
                raise ValueError(
                    "API key is required for custom provider. Provide via api_key parameter."
                )
        else:
            raise ValueError(
                f"Unsupported provider: {provider}. Supported providers: 'openai', 'anthropic', 'custom'"
            )
    
    def _load_prompt_from_file(self, prompt_file: str) -> str:
        """
        Load prompt template from a text file.

        Parameters:
        -----------
        prompt_file : str
            Path to the prompt text file.

        Returns:
        --------
        str
            Prompt template as string.

        Raises:
        -------
        FileNotFoundError
            If the prompt file does not exist.
        Exception
            If the file cannot be read.
        """
        prompt_path = Path(prompt_file)

        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
        
        try:
            with open(prompt_path, 'r', encoding='utf-8') as f:
                prompt = f.read()
            logger.info(f"Loaded prompt from file: {prompt_file}")
            return prompt
        except Exception as e:
            logger.error(f"Error reading prompt file {prompt_file}: {e}")
            raise

    def _call_ollama_api(self, prompt: str) -> str:
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens
            }
        }

        response = requests.post("http://localhost:11434/api/generate",
                                headers=headers, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()
        return data.get("response", "")

    def extract_process_flow(self, document_content: str, document_name: str = "") -> Dict[str, Any]:
        """
        Extract process flow structure from SOP document content.

        Parameters:
        -----------
        document_content : str
            Text content of the SOP document.
        document_name : str, optional
            Name of the document (for metadata).

        Returns:
        --------
        Dict[str, Any]
            Extracted process flow structure with metadata:
            - process_name
            - process_description
            - steps (list of structured step dictionaries)
            - roles, tools_systems, compliance_requirements
            - source_document, extraction_model

        Raises:
        -------
        ValueError
            If the response is not valid JSON.
        Exception
            For API or extraction errors.
        """
        # Truncate content if too long (most models have token limits)

        max_content_length = 20000  # Approximate character limit

        if len(document_content) > max_content_length:
            logger.warning(
                f"Document content too long ({len(document_content)} chars), "
                f"truncating to {max_content_length} chars"
            )
            document_content = document_content[:max_content_length]
        
        # Construct the prompt

        prompt = f"{self.prompt_template}\n\n--- Document: {document_name} ---\n\n{document_content}"
        
        try:
            # Call appropriate API based on provider
            if self.provider == "openai":
                response_text = self._call_openai_api(prompt)
            elif self.provider == "anthropic":
                response_text = self._call_anthropic_api(prompt)
            elif self.provider == "ollama":
                response_text = self._call_ollama_api(prompt)
            elif self.provider == "custom":
                response_text = self._call_custom_api(prompt)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
            
            # Extract JSON from response

            process_flow = safe_json_loads(response_text)
            
            # Add metadata

            process_flow['source_document'] = document_name
            process_flow['extraction_model'] = self.model
            
            logger.info(f"Successfully extracted process flow from {document_name}")

            return process_flow
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            logger.error(f"Response was: {response_text[:500]}")
            raise ValueError(f"Invalid JSON response from LLM: {e}")
        except Exception as e:
            logger.error(f"Error extracting process flow: {e}")
            raise
    
    def _call_openai_api(self, prompt: str) -> str:
        """
        Call OpenAI API and return response text.

        Parameters:
        -----------
        prompt : str
            Prompt to send to the API.

        Returns:
        --------
        str
            Response text (JSON string).
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an expert at extracting structured process flows from SOP documents."},
                {"role": "user", "content": prompt}
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            response_format={"type": "json_object"}
        )

        return response.choices[0].message.content
    
    def _call_anthropic_api(self, prompt: str) -> str:
        """
        Call Anthropic API and return response text.

        Parameters:
        -----------
        prompt : str
            Prompt to send to the API.

        Returns:
        --------
        str
            Response text (JSON string).
        """
        system_message = "You are an expert at extracting structured process flows from SOP documents."
        
        response = self.anthropic_client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            temperature=self.temperature,
            system=system_message,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Anthropic returns content as a list of text blocks

        response_text = ""

        for block in response.content:
            if hasattr(block, 'text'):
                response_text += block.text
            elif isinstance(block, str):
                response_text += block
        
        return response_text
    
    def _call_custom_api(self, prompt: str) -> str:
        """
        Call a custom LLM API via HTTP request.

        Parameters:
        -----------
        prompt : str
            Prompt to send to the API.

        Returns:
        --------
        str
            Response text (JSON string).

        Notes:
        ------
        - Expects OpenAI-compatible payload format.
        - Handles multiple common response formats.
        """
        headers = {
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "You are an expert at extracting structured process flows from SOP documents."},
                {"role": "user", "content": prompt}
            ],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens
        }
        
        # Add JSON mode if supported (OpenAI-compatible format)

        payload["response_format"] = {"type": "json_object"}
        
        try:
            response = requests.post(
                self.api_base_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            response_data = response.json()
            
            # Try to extract response text from common response formats

            if "choices" in response_data and len(response_data["choices"]) > 0:
                # OpenAI-compatible format
                return response_data["choices"][0]["message"]["content"]
            elif "content" in response_data:
                # Direct content field
                if isinstance(response_data["content"], list):
                    return "".join([item.get("text", "") for item in response_data["content"]])
                return response_data["content"]
            elif "text" in response_data:
                # Simple text field
                return response_data["text"]
            elif "message" in response_data:
                # Message field
                if isinstance(response_data["message"], dict) and "content" in response_data["message"]:
                    return response_data["message"]["content"]
                return str(response_data["message"])
            else:
                # Fallback: return the whole response as string
                logger.warning(f"Unexpected API response format: {list(response_data.keys())}")
                return json.dumps(response_data)
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling custom API: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response status: {e.response.status_code}")
                logger.error(f"Response body: {e.response.text[:500]}")
            raise
    
    def extract_from_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Extract process flows from multiple documents.

        Parameters:
        -----------
        documents : List[Dict[str, Any]]
            List of document dictionaries (from DocumentReader).

        Returns:
        --------
        List[Dict[str, Any]]
            List of extracted process flow dictionaries with metadata.

        Notes:
        ------
        - Skips documents that fail extraction, logging errors.
        - Useful for batch processing of SOP repositories.
        """
        extracted_flows = []
        
        for doc in documents:
            try:
                process_flow = self.extract_process_flow(
                    doc['content'],
                    doc['name']
                )
                # Add document metadata
                process_flow['document_path'] = doc['path']
                process_flow['document_relative_path'] = doc.get('relative_path', '')
                extracted_flows.append(process_flow)
            except Exception as e:
                logger.error(f"Failed to extract process flow from {doc['name']}: {e}")
                continue
        
        return extracted_flows
