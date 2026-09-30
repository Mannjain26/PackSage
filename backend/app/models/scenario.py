from datetime import datetime
import uuid
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

def make_uuid():
    return str(uuid.uuid4())

class Scenario(Base):
    __tablename__ = "scenarios"

    id = Column(String, primary_key=True, default=make_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    # Commodity
    commodity_name = Column(String, nullable=False)
    commodity_category = Column(String, nullable=False)  # fresh_produce | dry | oily | dairy | processed
    moisture_pct = Column(Float, nullable=True)
    fat_pct = Column(Float, nullable=True)
    ph = Column(Float, nullable=True)
    respiration_rate = Column(Float, nullable=True)  # mg CO2/kg/hr — fresh produce only

    # Storage
    storage_type = Column(String, nullable=False)   # ambient | chilled | frozen
    target_rh = Column(Float, nullable=True)         # %
    temp_min = Column(Float, nullable=True)          # °C
    temp_max = Column(Float, nullable=True)          # °C

    # Transport
    transport_mode = Column(String, nullable=True)  # road | rail | cold_chain
    transport_days = Column(Float, nullable=True)

    # Target & Priority
    target_shelf_life_days = Column(Integer, nullable=False)
    cost_priority = Column(String, default="balanced")  # performance_first | balanced | cost_first | sustainability_first

    # Packaging Commercial & Cost Parameters
    package_format = Column(String, default="pouch")    # pouch | bag | sachet | tray_lidding | bottle | jar | box | bulk | custom
    product_weight_g = Column(Float, default=100.0)     # grams per package
    package_quantity = Column(Integer, default=5000)    # batch quantity
    currency = Column(String, default="INR")            # INR | USD | EUR
    target_cost_per_package = Column(Float, nullable=True) # budget cap per pack
    target_total_budget = Column(Float, nullable=True)     # total project budget

    # Dimensions & Physical Specs
    package_length_cm = Column(Float, nullable=True)
    package_width_cm = Column(Float, nullable=True)
    package_height_cm = Column(Float, nullable=True)   # or gusset
    film_area_cm2 = Column(Float, nullable=True)       # explicit or calculated
    custom_thickness_um = Column(Float, nullable=True) # optional override
    layer_count = Column(Integer, default=1)

    # Optional Additional Cost Components (per package in specified currency)
    closure_cost_per_pkg = Column(Float, nullable=True)     # cap, zipper, valve
    label_cost_per_pkg = Column(Float, nullable=True)       # sticker / pressure-sensitive label
    printing_cost_per_pkg = Column(Float, nullable=True)    # flexo/rotogravure printing
    secondary_pack_cost_per_pkg = Column(Float, nullable=True) # outer carton / corrugated box share
    labor_packing_cost_per_pkg = Column(Float, nullable=True)  # filling / labor cost
    transport_cost_per_pkg = Column(Float, nullable=True)      # shipping / freight share
    wastage_pct_override = Column(Float, nullable=True)        # user-specified scrap %

    status = Column(String, default="draft")  # draft | in_progress | completed
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    owner = relationship("User", back_populates="scenarios")
    recommendations = relationship("Recommendation", back_populates="scenario", cascade="all, delete-orphan")



class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(String, primary_key=True, default=make_uuid)
    scenario_id = Column(String, ForeignKey("scenarios.id"), nullable=False)
    generated_at = Column(DateTime, default=datetime.utcnow)

    shelf_life_est_min = Column(Integer, nullable=True)
    shelf_life_est_max = Column(Integer, nullable=True)
    dominant_failure_mode = Column(String, nullable=True)

    # UUID used in QR code for traceability
    report_uuid = Column(String, default=make_uuid, unique=True)

    scenario = relationship("Scenario", back_populates="recommendations")
    items = relationship("RecommendationItem", back_populates="recommendation", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="recommendation", cascade="all, delete-orphan")


class RecommendationItem(Base):
    __tablename__ = "recommendation_items"

    id = Column(String, primary_key=True, default=make_uuid)
    recommendation_id = Column(String, ForeignKey("recommendations.id"), nullable=False)
    material_id = Column(String, ForeignKey("materials.id"), nullable=False)
    fit_score = Column(Float, nullable=False)
    rank = Column(Integer, nullable=False)
    explanation_text = Column(Text, nullable=True)

    recommendation = relationship("Recommendation", back_populates="items")
    material = relationship("Material")


class Report(Base):
    __tablename__ = "reports"

    id = Column(String, primary_key=True, default=make_uuid)
    recommendation_id = Column(String, ForeignKey("recommendations.id"), nullable=False)
    report_type = Column(String, default="recommendation")  # recommendation | test_plan
    file_path = Column(String, nullable=True)
    qr_code_value = Column(String, nullable=True)
    generated_by = Column(String, ForeignKey("users.id"), nullable=True)
    generated_at = Column(DateTime, default=datetime.utcnow)
    sign_off_status = Column(String, default="pending")  # pending | approved

    recommendation = relationship("Recommendation", back_populates="reports")


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(String, primary_key=True, default=make_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=False)
    entity_type = Column(String, nullable=True)
    entity_id = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="audit_logs")
