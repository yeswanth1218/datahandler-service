import os
from dotenv import load_dotenv
from typing import Dict, List
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from services.chunk_service import get_chunks_and_insights
from services.overview_service import get_overview
from services.data_formatter import format_chunk_data, extract_summaries_with_overview

# Load environment variables
load_dotenv()

app = FastAPI(title="Data handler", description="An api where the incoming LLM response is segrigated and sculpted to store")

# Input model
class TextInput(BaseModel):
    text: str

# Response model for individual chunk-insight pair
class ChunkInsight(BaseModel):
    chunk_id: str
    text: str
    insight_id: str
    summary: str
    overview: str

# Response model for the entire output
class LLMResponse(BaseModel):
    overview: str
    chunks: dict 
# class LLMResponse(BaseModel):
#     chunks: list[ChunkInsight]
# class LLMResponse(BaseModel):
#     overview: str
#     chunks: Dict[str, dict]  # Changed type to Dict[str, dict]


class SummaryResponse(BaseModel):
    overview: str
    summaries: Dict[str, str]
    

# API endpoint to process text, get overview, then chunks and insights
@app.post("/data-processing", response_model=SummaryResponse)
async def process_text(input_data: TextInput):
    # Step 1: Get the overview
    overview_dict = await get_overview(input_data)
    overview = overview_dict["response"]
    print(overview)

    # Step 2: Get chunks and insights, passing the overview
    chunks = await get_chunks_and_insights(input_data, overview)

    # LLMResponse(chunks=[chunk.dict() for chunk in chunks])

    chunk_data = await format_chunk_data(chunks)

    summary_payload = await extract_summaries_with_overview(overview, chunk_data)

    return summary_payload
    
    # Return the combined response
    #return LLMResponse(overview=overview, chunks=chunk_data)
     
    #return LLMResponse(chunks=chunks)

if __name__ == "__main__":
    port = int(os.getenv('PORT', 8600))
    
    uvicorn.run(app, host="0.0.0.0", port=port)