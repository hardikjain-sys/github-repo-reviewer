from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from main import reviewRepo

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ReviewRequest(BaseModel):
    url: str
    deep: bool = False


@app.post("/review")
async def review(req: ReviewRequest):
    try:
        result = await reviewRepo(req.url, req.deep)
        return result

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        print(f"Backend Crash Error: {e}")
        raise HTTPException(
            status_code=500, detail="error reviewing the repository."
        )