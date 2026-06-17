from openai import OpenAI
import time
import json
import re
from core.config import Config
from core.logger import logger

class APIClient:
    def __init__(self):
        self.api_key = Config.NVIDIA_API_KEY
        self.base_url = Config.NVIDIA_BASE_URL
        self.model_name = Config.MODEL_NAME
        
        if not self.api_key:
            logger.warning("NVIDIA_API_KEY is not set. API calls will fail.")
            
        self.client = OpenAI(
            base_url=self.base_url,
            api_key=self.api_key
        )
        
    def generate_gherkin(self, prompt: str, max_retries: int = None) -> tuple[str, float]:
        """
        Sends the prompt to the Nemotron API and returns the generated Gherkin and latency.
        Includes a retry mechanism for failed API calls.
        """
        if max_retries is None:
            max_retries = Config.MAX_RETRIES
            
        if not self.api_key:
            return "Error: NVIDIA API Key is missing. Please check your .env file.", 0.0
            
        start_time = time.time()
        
        for attempt in range(1, max_retries + 1):
            try:
                logger.info(f"Sending prompt to {self.model_name} (Attempt {attempt}/{max_retries}). Input size: {len(prompt)} chars.")
                
                # Create a deterministic completion by setting temperature to 0
                completion = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0,
                    top_p=1.0,
                    max_tokens=1024,
                    stream=False
                )
                
                latency = time.time() - start_time
                result = completion.choices[0].message.content
                if not result or not result.strip():
                    raise ValueError("Received empty or None response from LLM.")
                result = result.strip()
                
                logger.info(f"API call successful on attempt {attempt}. Latency: {latency:.2f}s")
                return result, latency
                
            except Exception as e:
                logger.warning(f"API call failed on attempt {attempt}/{max_retries}. Error: {str(e)}")
                if attempt == max_retries:
                    latency = time.time() - start_time
                    logger.error(f"All {max_retries} API attempts failed after {latency:.2f}s.")
                    return f"Error during conversion after {max_retries} attempts: {str(e)}", latency
                
                # Exponential backoff: 2s, 4s, 8s, etc.
                time.sleep(2 ** attempt)

    def validate_requirement_with_llm(self, requirement_text: str, max_retries: int = None) -> tuple[dict, str, float]:
        """
        Validates an EARS requirement using the LLM. 
        Returns a tuple of (validation_dict, raw_llm_response, latency).
        """
        if max_retries is None:
            max_retries = Config.MAX_RETRIES
            
        if not self.api_key:
            return {"is_valid": False, "issues": ["NVIDIA API Key missing."]}, "API Key Missing", 0.0
            
        prompt = (
            "Analyze the following requirement. Determine if it properly follows the EARS "
            "(Easy Approach to Requirements Syntax) format, and determine if it is practically testable.\n"
            "Return ONLY a valid JSON object with three keys:\n"
            "- 'is_ears' (boolean)\n"
            "- 'is_testable' (boolean)\n"
            "- 'issues' (list of strings explaining what is wrong or why it is not testable. Leave empty if perfect).\n\n"
            f"Requirement: \"{requirement_text}\""
        )
        
        start_time = time.time()
        for attempt in range(1, max_retries + 1):
            try:
                completion = self.client.chat.completions.create(
                    model=self.model_name,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0,
                    top_p=1.0,
                    max_tokens=1024,
                    stream=False
                )
                
                latency = time.time() - start_time
                raw_result = completion.choices[0].message.content
                if not raw_result or not raw_result.strip():
                    raise ValueError("Received empty or None response from LLM.")
                raw_result = raw_result.strip()
                
                # Attempt to extract JSON if there's markdown wrapping
                json_str = raw_result
                match = re.search(r'```json\s*(.*?)\s*```', json_str, re.DOTALL)
                if match:
                    json_str = match.group(1)
                else:
                    match = re.search(r'```\s*(.*?)\s*```', json_str, re.DOTALL)
                    if match:
                        json_str = match.group(1)
                        
                # Parse JSON
                try:
                    data = json.loads(json_str)
                    if "is_ears" not in data or "is_testable" not in data or "issues" not in data:
                        raise ValueError("JSON missing required keys.")
                        
                    is_valid = data["is_ears"] and data["is_testable"]
                    data["is_valid"] = is_valid
                    return data, raw_result, latency
                except json.JSONDecodeError:
                    raise ValueError(f"Failed to parse JSON from LLM: {raw_result}")
                    
            except Exception as e:
                logger.warning(f"Validation API call failed on attempt {attempt}/{max_retries}. Error: {str(e)}")
                if attempt == max_retries:
                    latency = time.time() - start_time
                    logger.error(f"Validation failed after {max_retries} attempts.")
                    return {"is_valid": False, "issues": [f"LLM validation failed: {str(e)}"]}, "", latency
                
                time.sleep(2 ** attempt)
        
        return {"is_valid": False, "issues": ["Unknown error"]}, "", 0.0

