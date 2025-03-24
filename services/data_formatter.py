# data_formatter.py
from typing import Dict, List
from typing import List
from pydantic import BaseModel
import asyncio
import json

class ChunkInsight(BaseModel):
    chunk_id: str
    text: str
    insight_id: str
    summary: str
    overview: str

async def format_chunk_data(chunks: List[ChunkInsight]) -> Dict[str, dict]:
    """
    Transforms a list of ChunkInsight objects into a dictionary
    where keys are chunk_ids and values are dictionaries containing
    chunk data.
    """
    chunk_data = {}
    for chunk in chunks:
        chunk_id = chunk.chunk_id
        chunk_data[chunk_id] = {
            "text": chunk.text,
            "insight_id": chunk.insight_id,
            "summary": chunk.summary
        }
        # Simulate an async operation (e.g., database call)
        await asyncio.sleep(0.001)  # Just for demonstration
    return chunk_data

async def extract_summaries_with_overview(overview: str, formatted_chunks: Dict[str, dict]) -> Dict[str, dict]:
    summaries = {}

    for chunk in formatted_chunks.values():
        insight_id = chunk.get("insight_id")
        raw_summary = chunk.get("summary")

        try:
            # Case 1: summary is a dict already
            if isinstance(raw_summary, dict):
                response_str = raw_summary.get("response", "")

            # Case 2: summary is a string — try parsing it
            elif isinstance(raw_summary, str):
                # Try to evaluate it as Python dict first (since it looks like that)
                try:
                    raw_summary_dict = eval(raw_summary)
                except Exception:
                    raw_summary_dict = json.loads(raw_summary.replace("'", '"'))  # fallback
                response_str = raw_summary_dict.get("response", "")

            else:
                raise ValueError("Unsupported summary format")

            # Now parse the inner summary string
            if isinstance(response_str, str):
                summary_text = json.loads(response_str)["summary"]
            else:
                summary_text = response_str.get("summary", "")

            summaries[insight_id] = summary_text

        except Exception as e:
            print(f"[Error] insight_id={insight_id} | raw={raw_summary} | err={e}")
            summaries[insight_id] = "Parsing error"

    return {
        "overview": overview,
        "summaries": summaries
    }