import os
from fastapi import HTTPException
import aiohttp
from pydantic import BaseModel

class TextInput(BaseModel):
    text: str

async def get_overview(input_data: TextInput) -> str:
    user_input = input_data.text
    
    # Get the LLM API endpoint from environment variables
    llm_api_endpoint = os.getenv('LLM_API_ENDPOINT', 'http://localhost:8500')
    model_endpoint = "gemini"
    full_endpoint = f"{llm_api_endpoint}/{model_endpoint}"
    
    # System prompt for overview
    system_prompt = """you are an efficient interactive summariser assistant. Your job is to give an overview summary of a received text within 70 words, without losing the overall meaning."""
    
    # Prepare the request payload
    payload = {
        "system_prompt": system_prompt,
        "user_prompt": user_input
    }
    
    # Make the async API call
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(full_endpoint, json=payload) as response:
                if response.status != 200:
                    raise HTTPException(status_code=response.status, detail=f"LLM API error during overview: {response.status}")
                # Assuming the response is plain text; adjust if it's JSON
                overview = await response.json()
                return overview
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error in get_overview: {str(e)}")