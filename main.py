import os
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from services.chunk_service import get_chunks_and_insights
from services.overview_service import get_overview

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
    chunks: list[ChunkInsight]

# API endpoint to process text, get overview, then chunks and insights
@app.post("/data-processing", response_model=LLMResponse)
async def process_text(input_data: TextInput):
    # Step 1: Get the overview
    overview = await get_overview(input_data)
    
    # Step 2: Get chunks and insights, passing the overview
    chunks = await get_chunks_and_insights(input_data, overview)
    
    # Return the combined response
    return LLMResponse(chunks=chunks)

if __name__ == "__main__":
    port = int(os.getenv('PORT', 8600))
    uvicorn.run(app, host="0.0.0.0", port=port)