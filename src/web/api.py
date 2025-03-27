from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl
from typing import List, Optional
import logging

from ..crawlers.sheikhbot import SheikhBot
from ..utils.logger import setup_logger

app = FastAPI(title="SheikhBot API")
logger = setup_logger("sheikhbot_api")

class AnalysisRequest(BaseModel):
    url: HttpUrl
    depth: Optional[int] = 3
    crawler_types: Optional[List[str]] = ["desktop", "mobile"]
    generate_sitemap: Optional[bool] = True
    submit_to_indexnow: Optional[bool] = False

@app.post("/analyze")
async def analyze_url(request: AnalysisRequest):
    try:
        bot = SheikhBot()
        results = bot.crawl(str(request.url))
        return {
            "status": "success",
            "results": results,
            "url": request.url,
        }
    except Exception as e:
        logger.error(f"Analysis error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))