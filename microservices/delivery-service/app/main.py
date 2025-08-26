from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Delivery Service", version="1.0.0")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

@app.get("/health")
async def health(): return {"status": "healthy", "service": "Delivery Service"}

@app.get("/delivery/me")
async def get_delivery_partner(): return {"id": 1, "name": "John Doe", "status": "available"}

@app.put("/delivery/status")
async def update_status(): return {"status": "updated"}

@app.post("/delivery/location")
async def update_location(): return {"message": "Location updated"}

@app.get("/delivery/orders")
async def get_orders(): return [{"id": 1, "customer": "Jane", "address": "123 Main St"}]