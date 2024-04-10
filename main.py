from fastapi import FastAPI
from counter import print_counters
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://counter-ai.pages.dev",
    "https://counter-ai.pages.dev"
    "http://localhost",
    "http://localhost:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class CounterData(BaseModel):
    query: str
    opinion: str

@app.post("/counter")
async def counter(counter_data: CounterData):
    
    display = 40
    response_counter = await print_counters(counter_data.query, counter_data.opinion, display=display)

    return {"query": counter_data.query, "opinion": counter_data.opinion, "response": response_counter}
