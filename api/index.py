
import os
import math
from collections import defaultdict

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Allow browser-based requests from the grader.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-API-Key"],
)


@app.post("/analytics")
async def analytics(request: Request):
    # Authenticate using the configured API key.
    expected_key = os.environ.get("API_KEY")

    if (
        not expected_key
        or request.headers.get("X-API-Key") != expected_key
    ):
        return JSONResponse(
            status_code=401,
            content={"error": "Unauthorized"},
        )

    # Parse and validate the request body.
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
            content={
                "error": "Request body must contain an events array"
            },
        )

    events = body["events"]
    users = set()
    user_revenue = defaultdict(float)
    revenue = 0.0

    # Calculate totals from the submitted batch.
    for event in events:
        if (
            not isinstance(event, dict)
            or not isinstance(event.get("user"), str)
            or isinstance(event.get("amount"), bool)
            or not isinstance(event.get("amount"), (int, float))
            or not math.isfinite(event["amount"])
        ):
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Each event must have a string user "
                             "and finite numeric amount"
                },
            )

        user = event["user"]
        amount = event["amount"]

        users.add(user)

        # Only positive amounts count toward revenue and top_user.
        if amount > 0:
            revenue += amount
            user_revenue[user] += amount

    # Find the user with the highest positive-amount total.
    top_user = None
    if user_revenue:
        top_user = max(user_revenue, key=user_revenue.get)

    return {
        "email": os.environ.get("GRADER_EMAIL", ""),
        "total_events": len(events),
        "unique_users": len(users),
        "revenue": round(revenue, 10),
        "top_user": top_user,
    }


# Vercel's Python runtime can use the ASGI app above.
