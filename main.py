import os
from typing import Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import db, create_document, get_documents
from schemas import SCHEMA_MODELS, Proposal, ProposalItem

app = FastAPI(title="Kenya AI-CRM Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Kenya AI-CRM Backend running"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set",
        "database_name": "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set",
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:20]
                response["database"] = "✅ Connected & Working"
                response["connection_status"] = "Connected"
            except Exception as e:
                response["database"] = f"⚠️ Connected but error: {str(e)[:80]}"
        else:
            response["database"] = "❌ Not Initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:120]}"
    return response

# Generic schema discovery for the UI/database viewer
@app.get("/schema")
def get_schema():
    out: Dict[str, Any] = {}
    for name, model in SCHEMA_MODELS.items():
        example = {}
        try:
            example = model.model_json_schema()
        except Exception:
            example = {"error": "schema generation failed"}
        out[name] = example
    return out

# Minimal endpoints to support proposal drafting and lead intake
class LeadIn(BaseModel):
    tenant_id: str
    source: str
    name: str | None = None
    phone: str | None = None
    email: str | None = None
    company: str | None = None

@app.post("/leads")
def create_lead(payload: LeadIn):
    lead_dict = payload.model_dump()
    lead_dict.update({"status": "new", "meta": {"ingest": "api"}})
    try:
        inserted_id = create_document("lead", lead_dict)
        return {"id": inserted_id, "status": "created"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ProposalDraftIn(BaseModel):
    tenant_id: str
    lead_id: str
    items: list[ProposalItem]

@app.post("/proposals/draft")
def create_proposal_draft(payload: ProposalDraftIn):
    # Compute totals server-side to avoid trusting client
    subtotal = sum((it.quantity or 1) * (it.unit_price_kes or 0) for it in payload.items)
    tax = round(subtotal * 0.16, 2)  # VAT 16% (can be adjusted per tenant later)
    total = round(subtotal + tax, 2)
    proposal = Proposal(
        tenant_id=payload.tenant_id,
        lead_id=payload.lead_id,
        items=payload.items,
        subtotal_kes=subtotal,
        tax_kes=tax,
        total_kes=total,
        status="draft",
        ai_status="pending",
        delivery_channels=["pdf"],
    )
    try:
        inserted_id = create_document("proposal", proposal)
        return {"id": inserted_id, "status": "draft_created", "totals": {"subtotal": subtotal, "tax": tax, "total": total}}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Simple listing endpoints for quick UI testing
@app.get("/leads")
def list_leads(tenant_id: str):
    try:
        docs = get_documents("lead", {"tenant_id": tenant_id}, limit=50)
        return docs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/proposals")
def list_proposals(tenant_id: str):
    try:
        docs = get_documents("proposal", {"tenant_id": tenant_id}, limit=50)
        return docs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
