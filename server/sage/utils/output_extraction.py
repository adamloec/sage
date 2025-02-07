import re
import json

from sage.utils.logger import Logger
LOGGER = Logger.create(__name__)

def extract_json(text: str):
    """
    Extract and parse JSON from text with improved handling of special characters.
    
    Args:
        text (str): Input text containing JSON
        
    Returns:
        Optional[Any]: Parsed JSON object or None if parsing fails
    """
    json_blocks = re.findall(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    
    if json_blocks:
        for block in reversed(json_blocks):
            cleaned_block = block.strip()
            try:
                return json.loads(cleaned_block)
            except json.JSONDecodeError as e:
                continue
    
    try:
        json_pattern = r'{[^{}]*(?:{[^{}]*}[^{}]*)*}'
        potential_jsons = re.findall(json_pattern, text, re.DOTALL)
        
        for json_str in reversed(potential_jsons):
            cleaned_json = json_str.strip()
            try:
                return json.loads(cleaned_json)
            except json.JSONDecodeError as e:
                LOGGER.debug(f"Failed to parse raw JSON: {e}")
                continue
                
        json_pattern_permissive = r'({[\s\S]*?})'
        potential_jsons = re.findall(json_pattern_permissive, text, re.DOTALL)
        
        for json_str in reversed(potential_jsons):
            cleaned_json = json_str.strip()
            if cleaned_json != json_str:
                try:
                    return json.loads(cleaned_json)
                except json.JSONDecodeError as e:
                    LOGGER.debug(f"Failed to parse permissive pattern: {e}")
                    continue
                    
    except Exception as e:
        LOGGER.error(f"Error during raw JSON extraction: {e}")
    
    return None