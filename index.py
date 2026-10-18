
import os
import math
from collections import defaultdict

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key"],
)


@app.options("/analytics")
async def analytics_options():
    return JSONResponse(
        status_code=204,
        content=None,
    )


@app.post("/analytics")
async def analytics(request: Request):
    # Use the exact assigned key stored in Vercel.
    expected_key = os.environ.get("API_KEY", "")
    supplied_key = request.headers.get("X-API-Key", "")

    # Reject missing or incorrect keys.
    if not expected_key or supplied_key != expected_key:
        return JSONResponse(
            status_code=401,
            content={"error": "Unauthorized"},
        )

    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid JSON"},
        )

    if not isinstance(body, dict) or not isinstance(
        body.get("events"), list
    ):
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid events array"},
        )

    events = body["events"]
    users = set()
    user_revenue = defaultdict(float)
    revenue = 0.0

    for event in events:
        if not isinstance(event, dict):
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid event"},
            )

        user = event.get("user")
        amount = event.get("amount")

        if (
            not isinstance(user, str)
            or isinstance(amount, bool)
            or not isinstance(amount, (int, float))
            or not math.isfinite(amount)
        ):
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid event fields"},
            )

        users.add(user)

        if amount > 0:
            revenue += amount
            user_revenue[user] += amount

    top_user = (
        max(user_revenue, key=user_revenue.get)
        if user_revenue
        else None
    )

    return {
        "email": os.environ.get("GRADER_EMAIL", ""),
        "total_events": len(events),
        "unique_users": len(users),
        "revenue": round(revenue, 10),
        "top_user": top_user,
    }
