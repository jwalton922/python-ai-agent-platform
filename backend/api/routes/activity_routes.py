from typing import List
from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from backend.models.activity import Activity, ActivityCreate
from backend.storage.file_storage import file_storage as storage
import json
import asyncio
from datetime import datetime

router = APIRouter()


@router.get("/", response_model=List[Activity])
async def get_activities(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0)
) -> List[Activity]:
    """Get activity feed (polling endpoint)"""
    return storage.list_activities(limit=limit, offset=offset)


@router.get("/stream")
async def stream_activities():
    """Server-Sent Events endpoint for real-time activity updates"""
    
    async def event_generator():
        last_check = datetime.utcnow()
        
        while True:
            # Get recent activities
            activities = storage.list_activities(limit=50)
            new_activities = [
                activity for activity in activities 
                if activity.created_at > last_check
            ]
            
            if new_activities:
                for activity in new_activities:
                    data = {
                        "id": activity.id,
                        "type": activity.type.value,
                        "title": activity.title,
                        "description": activity.description,
                        "created_at": activity.created_at.isoformat(),
                        "success": activity.success
                    }
                    yield f"data: {json.dumps(data)}\n\n"
                
                last_check = new_activities[0].created_at
            
            # Send heartbeat
            yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': datetime.utcnow().isoformat()})}\n\n"
            
            await asyncio.sleep(2)  # Check every 2 seconds
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control",
        }
    )


@router.post("/", response_model=Activity)
async def create_activity(activity_data: ActivityCreate) -> Activity:
    """Create a new activity (used internally by the system)"""
    return storage.create_activity(activity_data)