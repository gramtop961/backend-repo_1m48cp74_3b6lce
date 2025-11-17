"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
Each Pydantic model represents a collection in your database.
Class name lowercased is the collection name (e.g., Tenant -> "tenant").

These schemas model a Kenya-focused AI-CRM with multi-tenant isolation,
AI human-in-loop, payments and messaging integrations.
"""
from __future__ import annotations
from typing import Optional, List, Literal, Dict, Any
from pydantic import BaseModel, Field, EmailStr

# Core, tenancy, billing
class Tenant(BaseModel):
    name: str = Field(..., description="Tenant/Company name")
    domain: Optional[str] = Field(None, description="Preferred custom domain")
    plan: Literal["free", "business", "enterprise"] = Field("free", description="Pricing tier")
    country: str = Field("KE", description="ISO country code")
    settings: Dict[str, Any] = Field(default_factory=dict, description="Tenant-level settings and flags")

class BillingRecord(BaseModel):
    tenant_id: str = Field(..., description="Tenant ObjectId as string")
    plan: Literal["free", "business", "enterprise"]
    monthly_fee_kes: int = Field(..., ge=0)
    setup_fee_kes: int = Field(0, ge=0)
    usage: Dict[str, Any] = Field(default_factory=dict, description="Aggregated usage metrics for billing")
    status: Literal["trial", "active", "past_due", "canceled"] = "active"

class ModuleSubscription(BaseModel):
    tenant_id: str
    module_key: Literal[
        "sender_id_sms",
        "shortcodes",
        "ussd",
        "sms_surveys",
        "rewards_airtime",
        "mpesa_integration",
        "bulk_emails",
        "notifications",
        "loyalty_points",
    ]
    status: Literal["active", "inactive", "pending"] = "active"
    config: Dict[str, Any] = Field(default_factory=dict)

# Users and access
class UserAccount(BaseModel):
    tenant_id: str
    name: str
    email: EmailStr
    role: Literal["owner", "admin", "sales", "viewer"] = "owner"
    seats: Optional[int] = None
    is_active: bool = True

# Leads, messages, catalog
class Lead(BaseModel):
    tenant_id: str
    source: Literal["whatsapp", "gmail", "web", "social", "manual"]
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    company: Optional[str] = None
    score: Optional[float] = Field(None, ge=0, le=100)
    status: Literal["new", "qualified", "proposal", "won", "lost"] = "new"
    meta: Dict[str, Any] = Field(default_factory=dict)

class Message(BaseModel):
    tenant_id: str
    lead_id: str
    channel: Literal["whatsapp", "gmail", "sms", "email"]
    direction: Literal["inbound", "outbound"]
    content: str
    meta: Dict[str, Any] = Field(default_factory=dict)

class CatalogItem(BaseModel):
    tenant_id: str
    sku: Optional[str] = None
    title: str
    description: Optional[str] = None
    unit_price_kes: float = Field(..., ge=0)
    currency: Literal["KES", "USD"] = "KES"
    tags: List[str] = Field(default_factory=list)

# Proposals
class ProposalItem(BaseModel):
    catalog_item_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    quantity: float = 1
    unit_price_kes: float = 0

class Proposal(BaseModel):
    tenant_id: str
    lead_id: str
    items: List[ProposalItem]
    subtotal_kes: float = 0
    tax_kes: float = 0
    total_kes: float = 0
    status: Literal["draft", "approved", "sent", "accepted", "rejected"] = "draft"
    ai_status: Literal["none", "pending", "completed", "failed"] = "pending"
    delivery_channels: List[Literal["whatsapp", "gmail", "pdf"]] = Field(default_factory=list)

# Payments
class Payment(BaseModel):
    tenant_id: str
    provider: Literal["mpesa", "paystack"]
    amount_kes: float = Field(..., ge=0)
    currency: Literal["KES", "USD"] = "KES"
    status: Literal["initiated", "succeeded", "failed"] = "initiated"
    reference: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)

# AI & events
class AIJob(BaseModel):
    tenant_id: str
    job_type: Literal["lead_analysis", "catalog_generation", "proposal_generation", "embedding"]
    status: Literal["queued", "running", "completed", "failed"] = "queued"
    input: Dict[str, Any] = Field(default_factory=dict)
    output: Dict[str, Any] = Field(default_factory=dict)

class EventLog(BaseModel):
    tenant_id: str
    type: str
    actor: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    audit: Dict[str, Any] = Field(default_factory=dict)

# Export list used by /schema endpoint
SCHEMA_MODELS = {
    "tenant": Tenant,
    "billingrecord": BillingRecord,
    "modulesubscription": ModuleSubscription,
    "useraccount": UserAccount,
    "lead": Lead,
    "message": Message,
    "catalogitem": CatalogItem,
    "proposal": Proposal,
    "payment": Payment,
    "aijob": AIJob,
    "eventlog": EventLog,
}
