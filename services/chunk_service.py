import os
from fastapi import HTTPException
import aiohttp
from pydantic import BaseModel, ValidationError
import json

class ChunkInsight(BaseModel):
    chunk_id: str
    text: str
    insight_id: str
    summary: str
    overview: str

class TextInput(BaseModel):
    text: str

async def get_chunks_and_insights(input_data: TextInput, overview: str) -> list[ChunkInsight]:
    user_input = input_data.text

    # Get the LLM API endpoint from environment variables
    llm_api_endpoint = os.getenv('LLM_API_ENDPOINT', 'http://localhost:8500')
    model_endpoint = "groq"
    full_endpoint = f"{llm_api_endpoint}/{model_endpoint}"

    # System prompt for chunking
    chunking_prompt = """You are an expert text analyzer. Given a long piece of text, your task is to:
    1. Identify distinct topics or sections based on content and context.
    2. Split the text into meaningful chunks (each approximately 300-400 words, but prioritize topic coherence over strict word count).
    3. Return a list of chunks as separate strings.
    Format your response as a JSON array of strings, e.g., ["chunk1 text", "chunk2 text", ...]."""

    # Prepare payload for chunking
    chunking_payload = {
        "system_prompt": chunking_prompt,
        "user_prompt": user_input
    }

    # Step 1: Get chunks from LLM
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(full_endpoint, json=chunking_payload) as response:
                if response.status != 200:
                    raise HTTPException(status_code=500, detail=f"LLM API error during chunking: {response.status}")
                response_data = await response.json()  # Expecting a JSON object
                
                # Log or print the raw response for debugging
                print("LLM API Response for chunking:", response_data)

                # Extract and parse the response to get the actual list of chunks
                try:
                    chunks = json.loads(response_data['response'])  # Assuming 'response' contains the string of JSON array
                except (KeyError, json.JSONDecodeError):
                    raise HTTPException(status_code=500, detail="LLM did not return a valid list of chunks")
                
                if not isinstance(chunks, list):
                    raise HTTPException(status_code=500, detail="LLM did not return a valid list of chunks")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to chunk text: {str(e)}")

    # System prompt for summaries
    summary_prompt = """You are an expert summarizer. Given a chunk of text, provide a concise one-line summary capturing its main idea.
    Return your response as a JSON string with a single field "summary", e.g., {"summary": "This text discusses the evolution of AI technology."}"""

    # Step 2: Get insights for each chunk
    chunk_insights = []
    
    async with aiohttp.ClientSession() as session:
        for idx, chunk in enumerate(chunks, 1):
            summary_payload = {
                "system_prompt": summary_prompt,
                "user_prompt": chunk
            }
            
            try:
                async with session.post(full_endpoint, json=summary_payload) as response:
                    if response.status != 200:
                        raise HTTPException(status_code=500, detail=f"LLM API error during summary: {response.status}")
                    insight_response = await response.json()  # Now expecting JSON response
                    
                    # Extract summary from the JSON response
                    if isinstance(insight_response, dict) and "summary" in insight_response:
                        insight = insight_response["summary"]
                    else:
                        # Handle unexpected response format
                        insight = str(insight_response)
                    
                    # Ensure we're passing the correct data for Pydantic validation
                    try:
                        chunk_insights.append(
                            ChunkInsight(
                                chunk_id=f"c{idx}",
                                text=chunk,
                                insight_id=f"i{idx}",
                                summary=insight,
                                overview=overview
                            )
                        )
                    except ValidationError as e:
                        raise HTTPException(status_code=500, detail=f"Error validating chunk insight: {str(e)}")
            
            except Exception as e:
                chunk_insights.append(
                    ChunkInsight(
                        chunk_id=f"c{idx}",
                        text=chunk,
                        insight_id=f"i{idx}",
                        summary=f"Error generating summary: {str(e)}",
                        overview=overview
                    )
                )
    
    return chunk_insights