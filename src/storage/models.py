"""
SQLAlchemy ORM models for the Cannabis Data Aggregator.
"""
import hashlib
import json
from datetime import datetime, date
from typing import Optional, Dict, Any

from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date,
    Float, Text, JSON, ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class DataSource(Base):
    """
    Defines a single data source (API endpoint, CSV download, etc.).
    Loaded from config/sources.yaml and editable via the dashboard.
    """
    __tablename__ = "data_sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    state = Column(String(20), nullable=False, index=True)
    agency = Column(String(255), nullable=True)
    category = Column(String(50), nullable=False, index=True)
    subcategory = Column(String(50), nullable=True)
    format = Column(String(20), nullable=False)      # soda, json, csv, geojson, xml
    url = Column(String(2048), nullable=True)
    discovery_url = Column(String(2048), nullable=True)
    website = Column(String(2048), nullable=True)
    enabled = Column(Boolean, default=True, nullable=False, index=True)
    api_key_required = Column(Boolean, default=False)
    api_key_env = Column(String(100), nullable=True)
    params = Column(JSON, nullable=True)             # Default query params
    headers = Column(JSON, nullable=True)            # Custom headers
    pagination = Column(JSON, nullable=True)         # Pagination config
    field_mapping = Column(JSON, nullable=True)      # Field name mapping
    tags = Column(JSON, nullable=True)               # List of tags
    notes = Column(Text, nullable=True)
    rate_limit_rpm = Column(Integer, default=60)     # Requests per minute
    timeout = Column(Integer, default=60)            # Request timeout seconds
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    schedules = relationship("CollectionSchedule", back_populates="source", cascade="all, delete-orphan")
    runs = relationship("CollectionRun", back_populates="source", cascade="all, delete-orphan")
    records = relationship("RawRecord", back_populates="source", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source_id": self.source_id,
            "name": self.name,
            "description": self.description,
            "state": self.state,
            "agency": self.agency,
            "category": self.category,
            "subcategory": self.subcategory,
            "format": self.format,
            "url": self.url,
            "discovery_url": self.discovery_url,
            "website": self.website,
            "enabled": self.enabled,
            "api_key_required": self.api_key_required,
            "api_key_env": self.api_key_env,
            "params": self.params,
            "headers": self.headers,
            "pagination": self.pagination,
            "field_mapping": self.field_mapping,
            "tags": self.tags,
            "notes": self.notes,
            "rate_limit_rpm": self.rate_limit_rpm,
            "timeout": self.timeout,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<DataSource {self.source_id} ({self.state}/{self.category})>"


class CollectionSchedule(Base):
    """
    Defines when a data source should be collected.
    Loaded from config/schedules.yaml and editable via the dashboard.
    """
    __tablename__ = "collection_schedules"

    id = Column(Integer, primary_key=True, autoincrement=True)
    schedule_id = Column(String(100), unique=True, nullable=False, index=True)
    source_id = Column(Integer, ForeignKey("data_sources.id"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    schedule_type = Column(String(20), nullable=False)  # interval, cron
    enabled = Column(Boolean, default=True, nullable=False, index=True)
    priority = Column(Integer, default=2)  # 1=high, 2=normal, 3=low

    # Cron fields
    cron_minute = Column(String(20), default="0")
    cron_hour = Column(String(20), default="0")
    cron_day_of_month = Column(String(20), default="*")
    cron_month = Column(String(20), default="*")
    cron_day_of_week = Column(String(20), default="*")

    # Interval fields
    interval_value = Column(Integer, nullable=True)
    interval_unit = Column(String(20), nullable=True)   # minutes, hours, days, weeks

    notes = Column(Text, nullable=True)
    next_run = Column(DateTime, nullable=True)
    last_run = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    source = relationship("DataSource", back_populates="schedules")
    runs = relationship("CollectionRun", back_populates="schedule")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "schedule_id": self.schedule_id,
            "source_id": self.source_id,
            "name": self.name,
            "schedule_type": self.schedule_type,
            "enabled": self.enabled,
            "priority": self.priority,
            "cron_minute": self.cron_minute,
            "cron_hour": self.cron_hour,
            "cron_day_of_month": self.cron_day_of_month,
            "cron_month": self.cron_month,
            "cron_day_of_week": self.cron_day_of_week,
            "interval_value": self.interval_value,
            "interval_unit": self.interval_unit,
            "notes": self.notes,
            "next_run": self.next_run.isoformat() if self.next_run else None,
            "last_run": self.last_run.isoformat() if self.last_run else None,
        }

    def __repr__(self):
        return f"<CollectionSchedule {self.schedule_id}>"


class CollectionRun(Base):
    """
    Records each execution of a collection job.
    """
    __tablename__ = "collection_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(Integer, ForeignKey("data_sources.id"), nullable=False, index=True)
    schedule_id = Column(Integer, ForeignKey("collection_schedules.id"), nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False, index=True)  # running, success, failed, partial
    records_fetched = Column(Integer, default=0)
    records_stored = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    records_skipped = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    raw_file_path = Column(String(512), nullable=True)
    duration_seconds = Column(Float, nullable=True)
    triggered_by = Column(String(50), default="scheduler")  # scheduler, manual, api

    # Relationships
    source = relationship("DataSource", back_populates="runs")
    schedule = relationship("CollectionSchedule", back_populates="runs")
    logs = relationship("CollectionLog", back_populates="run", cascade="all, delete-orphan")

    @property
    def duration(self) -> Optional[float]:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "source_id": self.source_id,
            "schedule_id": self.schedule_id,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "status": self.status,
            "records_fetched": self.records_fetched,
            "records_stored": self.records_stored,
            "records_updated": self.records_updated,
            "records_skipped": self.records_skipped,
            "error_message": self.error_message,
            "duration_seconds": self.duration,
            "triggered_by": self.triggered_by,
        }

    def __repr__(self):
        return f"<CollectionRun {self.id} source={self.source_id} status={self.status}>"


class RawRecord(Base):
    """
    Flexible storage for any collected data record.
    Uses a hybrid approach: standard indexed fields + full JSON blob.
    """
    __tablename__ = "raw_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    source_id = Column(Integer, ForeignKey("data_sources.id"), nullable=False, index=True)
    run_id = Column(Integer, ForeignKey("collection_runs.id"), nullable=True, index=True)

    # Indexed standard fields for fast querying
    state = Column(String(5), nullable=True, index=True)
    category = Column(String(50), nullable=True, index=True)
    subcategory = Column(String(50), nullable=True)

    # Entity identification
    name = Column(String(255), nullable=True, index=True)
    license_number = Column(String(100), nullable=True, index=True)
    license_type = Column(String(100), nullable=True, index=True)
    license_status = Column(String(50), nullable=True, index=True)

    # Location data
    address = Column(String(500), nullable=True)
    city = Column(String(100), nullable=True, index=True)
    zip_code = Column(String(20), nullable=True, index=True)
    county = Column(String(100), nullable=True, index=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)

    # Contact
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    website = Column(String(2048), nullable=True)

    # Dates
    record_date = Column(Date, nullable=True, index=True)   # Data reporting period date
    license_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True)

    # Full record data (JSON blob for all fields)
    record_data = Column(JSON, nullable=False)

    # Deduplication
    record_hash = Column(String(64), nullable=True, index=True)
    source_record_id = Column(String(255), nullable=True)   # ID from source system

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    source = relationship("DataSource", back_populates="records")

    # Indexes for common queries
    __table_args__ = (
        Index("ix_raw_records_state_category", "state", "category"),
        Index("ix_raw_records_city_state", "city", "state"),
        Index("ix_raw_records_hash", "record_hash"),
    )

    @staticmethod
    def compute_hash(record_data: dict) -> str:
        """Compute a hash for deduplication."""
        serialized = json.dumps(record_data, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()

    def to_dict(self, include_raw: bool = True) -> Dict[str, Any]:
        result = {
            "id": self.id,
            "source_id": self.source_id,
            "state": self.state,
            "category": self.category,
            "name": self.name,
            "license_number": self.license_number,
            "license_type": self.license_type,
            "license_status": self.license_status,
            "address": self.address,
            "city": self.city,
            "zip_code": self.zip_code,
            "county": self.county,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "phone": self.phone,
            "email": self.email,
            "website": self.website,
            "record_date": self.record_date.isoformat() if self.record_date else None,
            "license_date": self.license_date.isoformat() if self.license_date else None,
            "expiry_date": self.expiry_date.isoformat() if self.expiry_date else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
        if include_raw:
            result["record_data"] = self.record_data
        return result

    def to_geojson_feature(self) -> Optional[Dict]:
        """Convert to a GeoJSON feature if coordinates are available."""
        if self.latitude is None or self.longitude is None:
            return None
        props = self.to_dict(include_raw=False)
        props.pop("latitude", None)
        props.pop("longitude", None)
        return {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [self.longitude, self.latitude]
            },
            "properties": props
        }

    def __repr__(self):
        return f"<RawRecord {self.id} {self.state}/{self.category} '{self.name}'>"


class CollectionLog(Base):
    """
    Detailed log entries for collection runs.
    """
    __tablename__ = "collection_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    run_id = Column(Integer, ForeignKey("collection_runs.id"), nullable=True, index=True)
    source_id = Column(Integer, ForeignKey("data_sources.id"), nullable=True, index=True)
    level = Column(String(10), nullable=False, index=True)   # DEBUG, INFO, WARNING, ERROR
    message = Column(Text, nullable=False)
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    run = relationship("CollectionRun", back_populates="logs")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "run_id": self.run_id,
            "source_id": self.source_id,
            "level": self.level,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }

    def __repr__(self):
        return f"<CollectionLog {self.level}: {self.message[:50]}>"


class AppSetting(Base):
    """
    Key-value store for application settings editable via the dashboard.
    Overrides values in settings.yaml at runtime.
    """
    __tablename__ = "app_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)
    value_type = Column(String(20), default="string")  # string, int, float, bool, json
    description = Column(String(500), nullable=True)
    category = Column(String(50), default="general")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def get_typed_value(self):
        """Return value coerced to the correct Python type."""
        if self.value is None:
            return None
        if self.value_type == "int":
            return int(self.value)
        if self.value_type == "float":
            return float(self.value)
        if self.value_type == "bool":
            return self.value.lower() in ("true", "1", "yes")
        if self.value_type == "json":
            return json.loads(self.value)
        return self.value

    def __repr__(self):
        return f"<AppSetting {self.key}={self.value}>"


# =============================================================================
#  MANUALLY-MANAGED ENTITY TABLES
#  Cannabis Companies, Doctors, Brands, and Products
# =============================================================================

class CannabisCompany(Base):
    """
    A cannabis company / parent organization.
    Other entities (brands, facilities) may reference this table.
    """
    __tablename__ = "cannabis_companies"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False, index=True)
    logo_url = Column(String(500), nullable=True)
    website = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    street = Column(String(255), nullable=True)
    city = Column(String(255), nullable=True, index=True)
    state = Column(String(2), nullable=True, index=True)
    country = Column(String(2), nullable=True, default="US")
    zipcode = Column(String(20), nullable=True)
    telephone = Column(String(25), nullable=True)
    email = Column(String(255), nullable=True)
    instagram = Column(String(255), nullable=True)
    twitter = Column(String(255), nullable=True)
    facebook = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    brands = relationship("CannabisBrand", back_populates="company", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "logo_url": self.logo_url,
            "website": self.website,
            "description": self.description,
            "street": self.street,
            "city": self.city,
            "state": self.state,
            "country": self.country,
            "zipcode": self.zipcode,
            "telephone": self.telephone,
            "email": self.email,
            "instagram": self.instagram,
            "twitter": self.twitter,
            "facebook": self.facebook,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<CannabisCompany {self.name}>"


class CannabisDoctor(Base):
    """
    A medical cannabis doctor / recommending physician.
    """
    __tablename__ = "cannabis_doctors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False, index=True)
    photo_url = Column(String(500), nullable=True)
    website = Column(String(255), nullable=True)
    practice_name = Column(String(255), nullable=True, index=True)
    street = Column(String(255), nullable=True)
    city = Column(String(255), nullable=True, index=True)
    state = Column(String(2), nullable=True, index=True)
    country = Column(String(2), nullable=True, default="US")
    zipcode = Column(String(20), nullable=True)
    telephone = Column(String(25), nullable=True)
    email = Column(String(255), nullable=True)
    specialization = Column(String(255), nullable=True)
    license_number = Column(String(100), nullable=True)
    license_state = Column(String(2), nullable=True)
    license_expiry = Column(Date, nullable=True)
    accepts_new_patients = Column(String(10), nullable=True)   # Yes | No | Unknown
    telehealth_available = Column(String(10), nullable=True)   # Yes | No | Unknown
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "full_name": self.full_name,
            "photo_url": self.photo_url,
            "website": self.website,
            "practice_name": self.practice_name,
            "street": self.street,
            "city": self.city,
            "state": self.state,
            "country": self.country,
            "zipcode": self.zipcode,
            "telephone": self.telephone,
            "email": self.email,
            "specialization": self.specialization,
            "license_number": self.license_number,
            "license_state": self.license_state,
            "license_expiry": self.license_expiry.isoformat() if self.license_expiry else None,
            "accepts_new_patients": self.accepts_new_patients,
            "telehealth_available": self.telehealth_available,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<CannabisDoctor {self.full_name}>"


class CannabisBrand(Base):
    """
    A cannabis product brand. May belong to a CannabisCompany.
    """
    __tablename__ = "cannabis_brands"

    id = Column(Integer, primary_key=True, autoincrement=True)
    company_id = Column(Integer, ForeignKey("cannabis_companies.id"), nullable=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    slug = Column(String(255), nullable=True, index=True)
    logo_url = Column(String(500), nullable=True)
    website = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    street = Column(String(255), nullable=True)
    city = Column(String(255), nullable=True, index=True)
    state = Column(String(2), nullable=True, index=True)
    country = Column(String(2), nullable=True, default="US")
    zipcode = Column(String(20), nullable=True)
    telephone = Column(String(25), nullable=True)
    email = Column(String(255), nullable=True)
    instagram = Column(String(255), nullable=True)
    twitter = Column(String(255), nullable=True)
    facebook = Column(String(255), nullable=True)
    founded_year = Column(Integer, nullable=True)
    category = Column(String(100), nullable=True, index=True)  # flower, edibles, concentrates…
    license_number = Column(String(100), nullable=True)
    license_state = Column(String(2), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    company = relationship("CannabisCompany", back_populates="brands")
    products = relationship("CannabisProduct", back_populates="brand", cascade="all, delete-orphan")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "company_id": self.company_id,
            "company_name": self.company.name if self.company else None,
            "name": self.name,
            "slug": self.slug,
            "logo_url": self.logo_url,
            "website": self.website,
            "description": self.description,
            "street": self.street,
            "city": self.city,
            "state": self.state,
            "country": self.country,
            "zipcode": self.zipcode,
            "telephone": self.telephone,
            "email": self.email,
            "instagram": self.instagram,
            "twitter": self.twitter,
            "facebook": self.facebook,
            "founded_year": self.founded_year,
            "category": self.category,
            "license_number": self.license_number,
            "license_state": self.license_state,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<CannabisBrand {self.name}>"


class CannabisProduct(Base):
    """
    A cannabis product. May belong to a CannabisBrand.
    """
    __tablename__ = "cannabis_products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    brand_id = Column(Integer, ForeignKey("cannabis_brands.id"), nullable=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    sku = Column(String(100), nullable=True, index=True)
    image_url = Column(String(500), nullable=True)
    website = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    category = Column(String(100), nullable=True, index=True)   # flower, edibles, concentrates…
    subcategory = Column(String(100), nullable=True)
    strain_name = Column(String(255), nullable=True, index=True)
    strain_type = Column(String(20), nullable=True)             # Indica | Sativa | Hybrid | CBD | Unknown
    thc_percentage = Column(Float, nullable=True)
    cbd_percentage = Column(Float, nullable=True)
    price = Column(Float, nullable=True)
    price_unit = Column(String(50), nullable=True)              # per gram, per oz, each…
    weight_grams = Column(Float, nullable=True)
    state = Column(String(2), nullable=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    brand = relationship("CannabisBrand", back_populates="products")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "brand_id": self.brand_id,
            "brand_name": self.brand.name if self.brand else None,
            "name": self.name,
            "sku": self.sku,
            "image_url": self.image_url,
            "website": self.website,
            "description": self.description,
            "category": self.category,
            "subcategory": self.subcategory,
            "strain_name": self.strain_name,
            "strain_type": self.strain_type,
            "thc_percentage": self.thc_percentage,
            "cbd_percentage": self.cbd_percentage,
            "price": self.price,
            "price_unit": self.price_unit,
            "weight_grams": self.weight_grams,
            "state": self.state,
            "is_active": self.is_active,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<CannabisProduct {self.name}>"


# ---------------------------------------------------------------------------
# Cannabis License  (state licensing data — Alaska, etc.)
# ---------------------------------------------------------------------------

class CannabisLicense(Base):
    """
    Marijuana business license record from a state licensing authority.
    Stores data from Alaska AMCO and similar scraped / downloaded sources.
    """
    __tablename__ = "cannabis_licenses"

    id                      = Column(Integer, primary_key=True)

    # License identifiers
    license_number          = Column(String(50),  nullable=True)   # MJ license # (e.g. "10004")
    license_url             = Column(String(500), nullable=True)   # Link to MJ licence detail page
    business_license_number = Column(String(50),  nullable=True)   # State biz license #
    business_license_url    = Column(String(500), nullable=True)   # Link to biz licence detail page

    # Classification
    license_type            = Column(String(100), nullable=True)   # Retail, Cultivation, Testing …
    license_status          = Column(String(100), nullable=True)   # Active-Operating, Expired, Revoked …

    # Business
    business_name           = Column(String(255), nullable=False)
    dba_name                = Column(String(255), nullable=True)

    # Location
    street                  = Column(String(255), nullable=True)
    city                    = Column(String(100), nullable=True)
    state                   = Column(String(10),  nullable=True)   # 2-letter state code
    zipcode                 = Column(String(20),  nullable=True)
    country                 = Column(String(10),  nullable=True, default="US")

    # Source metadata
    source_state            = Column(String(10),  nullable=True)   # Which state this came from
    source_file             = Column(String(255), nullable=True)   # Origin filename

    created_at  = Column(DateTime, default=datetime.utcnow)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "license_number": self.license_number,
            "license_url": self.license_url,
            "business_license_number": self.business_license_number,
            "business_license_url": self.business_license_url,
            "license_type": self.license_type,
            "license_status": self.license_status,
            "business_name": self.business_name,
            "dba_name": self.dba_name,
            "street": self.street,
            "city": self.city,
            "state": self.state,
            "zipcode": self.zipcode,
            "country": self.country,
            "source_state": self.source_state,
            "source_file": self.source_file,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<CannabisLicense {self.license_number} – {self.business_name}>"


# ---------------------------------------------------------------------------
# Cannabis Strain
# ---------------------------------------------------------------------------

class CannabisStrain(Base):
    """Cannabis strain with cannabinoid profiles and metadata."""
    __tablename__ = "cannabis_strains"

    id          = Column(Integer, primary_key=True)
    source_id   = Column(Integer, nullable=True)   # ID in origin dataset
    status      = Column(Integer, nullable=True)   # 1 = published

    name        = Column(String(255), nullable=False)
    slug        = Column(String(255), nullable=True)
    image_url   = Column(String(500), nullable=True)
    description = Column(Text,        nullable=True)

    # Classification
    strain_type = Column(String(50),  nullable=True)   # Indica, Sativa, Hybrid
    crosses     = Column(String(500), nullable=True)   # Parent strains (free text)
    breeder     = Column(String(255), nullable=True)

    # Effects / flavour
    effects     = Column(String(500), nullable=True)
    ailments    = Column(String(500), nullable=True)
    flavors     = Column(String(500), nullable=True)
    terpenes    = Column(String(500), nullable=True)

    # Cannabinoid percentages (raw values from source)
    thc     = Column(Float, nullable=True)
    thca    = Column(Float, nullable=True)
    thcv    = Column(Float, nullable=True)
    cbd     = Column(Float, nullable=True)
    cbda    = Column(Float, nullable=True)
    cbdv    = Column(Float, nullable=True)
    cbn     = Column(Float, nullable=True)
    cbg     = Column(Float, nullable=True)
    cbgm    = Column(Float, nullable=True)
    cbgv    = Column(Float, nullable=True)
    cbc     = Column(Float, nullable=True)
    cbcv    = Column(Float, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "source_id": self.source_id,
            "name": self.name,
            "slug": self.slug,
            "image_url": self.image_url,
            "description": self.description,
            "strain_type": self.strain_type,
            "crosses": self.crosses,
            "breeder": self.breeder,
            "effects": self.effects,
            "ailments": self.ailments,
            "flavors": self.flavors,
            "terpenes": self.terpenes,
            "thc": self.thc,
            "thca": self.thca,
            "thcv": self.thcv,
            "cbd": self.cbd,
            "cbda": self.cbda,
            "cbdv": self.cbdv,
            "cbn": self.cbn,
            "cbg": self.cbg,
            "cbc": self.cbc,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<CannabisStrain {self.name}>"


# ---------------------------------------------------------------------------
# Cannabis Shop  (dispensaries, delivery services, etc.)
# ---------------------------------------------------------------------------

class CannabisShop(Base):
    """
    Cannabis retail shop / dispensary.
    Schema derived from the Kushy dataset shops table.
    """
    __tablename__ = "cannabis_shops"

    id          = Column(Integer, primary_key=True)
    source_id   = Column(Integer, nullable=True)   # ID in origin dataset
    status      = Column(Integer, nullable=True)   # 1 = published / active

    name        = Column(String(255), nullable=False)
    slug        = Column(String(255), nullable=True)
    shop_type   = Column(String(100), nullable=True)   # Dispensary, Delivery, etc.
    description = Column(Text,        nullable=True)

    # Media
    featured_image = Column(String(500), nullable=True)
    avatar_url     = Column(String(500), nullable=True)

    # Location
    street      = Column(String(255), nullable=True)
    city        = Column(String(100), nullable=True)
    state       = Column(String(10),  nullable=True)
    zipcode     = Column(String(20),  nullable=True)
    country     = Column(String(10),  nullable=True, default="US")
    latitude    = Column(Float,       nullable=True)
    longitude   = Column(Float,       nullable=True)

    # Contact / social
    telephone   = Column(String(50),  nullable=True)
    website     = Column(String(500), nullable=True)
    email       = Column(String(255), nullable=True)
    instagram   = Column(String(100), nullable=True)
    twitter     = Column(String(100), nullable=True)
    facebook    = Column(String(255), nullable=True)

    # Metadata
    rating      = Column(Float,       nullable=True)
    hours       = Column(Text,        nullable=True)
    tags        = Column(String(500), nullable=True)

    created_at  = Column(DateTime, default=datetime.utcnow)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "source_id": self.source_id,
            "status": self.status,
            "name": self.name,
            "slug": self.slug,
            "shop_type": self.shop_type,
            "description": self.description,
            "featured_image": self.featured_image,
            "avatar_url": self.avatar_url,
            "street": self.street,
            "city": self.city,
            "state": self.state,
            "zipcode": self.zipcode,
            "country": self.country,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "telephone": self.telephone,
            "website": self.website,
            "email": self.email,
            "instagram": self.instagram,
            "twitter": self.twitter,
            "facebook": self.facebook,
            "rating": self.rating,
            "tags": self.tags,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def __repr__(self):
        return f"<CannabisShop {self.name}>"
