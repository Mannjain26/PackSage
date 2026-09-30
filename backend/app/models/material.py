from datetime import datetime
import uuid
from sqlalchemy import Column, String, Float, Boolean, DateTime, Text
from app.core.database import Base

def make_uuid():
    return str(uuid.uuid4())

class Material(Base):
    __tablename__ = "materials"

    id = Column(String, primary_key=True, default=make_uuid)
    name = Column(String, index=True, nullable=False)
    mat_type = Column(String, nullable=False)  # LDPE, HDPE, PET, BOPP, metalized, foil_laminate, biodegradable, breathable

    # Barrier properties (standardized: OTR at 23°C/0%RH, WVTR at 38°C/90%RH)
    otr = Column(Float, nullable=True)           # cc/m²/day
    wvtr = Column(Float, nullable=True)          # g/m²/day
    thickness_min = Column(Float, nullable=True) # microns
    thickness_max = Column(Float, nullable=True) # microns
    temp_min = Column(Float, default=-40.0)      # °C
    temp_max = Column(Float, default=60.0)       # °C

    # Functional properties
    sealability = Column(Boolean, default=True)
    breathable = Column(Boolean, default=False)   # micro-perforated / breathable
    gas_permeability = Column(String, nullable=True)  # High/Medium/Low

    # Compliance & sustainability
    food_contact_safe = Column(Boolean, default=False)
    recyclable = Column(Boolean, default=False)
    biodegradable = Column(Boolean, default=False)

    # Economics & Pricing
    cost_index = Column(Float, default=1.0)      # relative (1.0 = baseline LDPE)
    price_per_kg = Column(Float, nullable=True)  # currency per kg (e.g. ₹130/kg)
    price_per_sqm = Column(Float, nullable=True) # currency per m² (e.g. ₹5.50/m²)
    currency = Column(String, default="INR")     # INR, USD, EUR
    price_source = Column(String, default="Converter Index / Market Benchmark")
    price_last_updated = Column(DateTime, default=datetime.utcnow)
    price_confidence = Column(String, default="Illustrative Demo")  # High, Medium, Low, Illustrative Demo
    material_density_g_cm3 = Column(Float, default=0.92) # g/cm³ (e.g. 0.92 for LDPE, 1.38 for PET, 2.70 for Alu)
    wastage_pct_default = Column(Float, default=5.0)     # Default cutting/forming scrap %
    conversion_cost_default = Column(Float, default=0.25) # Default forming/conversion cost per package
    sealing_cost_default = Column(Float, default=0.10)   # Default sealing cost per package
    moq_kg = Column(Float, default=50.0)                 # Minimum order quantity in kg
    quantity_discount_pct = Column(Float, default=5.0)   # Discount % for large volume batches
    sustainability_score = Column(Float, default=50.0)  # 0-100

    # Metadata
    notes = Column(Text, nullable=True)
    verified = Column(Boolean, default=False)    # must be True to appear in recommendations
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

