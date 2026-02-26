"""
Page-level routes for the manually-managed entity tables:
  Cannabis Companies, Doctors, Brands, Products, Licenses, Strains, and Shops.
"""
from flask import Blueprint, render_template, request

from src.storage.database import get_session
from src.storage.models import (
    CannabisCompany,
    CannabisDoctor,
    CannabisBrand,
    CannabisProduct,
    CannabisLicense,
    CannabisStrain,
    CannabisShop,
)

entities_bp = Blueprint("entities", __name__)


@entities_bp.route("/")
def index():
    """Entity management hub — shows counts for each entity type."""
    session = get_session()
    try:
        counts = {
            "companies": session.query(CannabisCompany).count(),
            "doctors":   session.query(CannabisDoctor).count(),
            "brands":    session.query(CannabisBrand).count(),
            "products":  session.query(CannabisProduct).count(),
            "licenses":  session.query(CannabisLicense).count(),
            "strains":   session.query(CannabisStrain).count(),
            "shops":     session.query(CannabisShop).count(),
        }
    finally:
        session.close()
    return render_template("entities/index.html", counts=counts)


@entities_bp.route("/companies")
def companies():
    return render_template("entities/companies.html")


@entities_bp.route("/doctors")
def doctors():
    return render_template("entities/doctors.html")


@entities_bp.route("/brands")
def brands():
    """Brands page — passes company list for the FK dropdown."""
    session = get_session()
    try:
        company_list = (
            session.query(CannabisCompany.id, CannabisCompany.name)
            .order_by(CannabisCompany.name)
            .all()
        )
    finally:
        session.close()
    return render_template(
        "entities/brands.html",
        company_options=[{"id": c.id, "name": c.name} for c in company_list],
    )


@entities_bp.route("/products")
def products():
    """Products page — passes brand list for the FK dropdown."""
    session = get_session()
    try:
        brand_list = (
            session.query(CannabisBrand.id, CannabisBrand.name)
            .order_by(CannabisBrand.name)
            .all()
        )
    finally:
        session.close()
    return render_template(
        "entities/products.html",
        brand_options=[{"id": b.id, "name": b.name} for b in brand_list],
    )


@entities_bp.route("/licenses")
def licenses():
    return render_template("entities/licenses.html")


@entities_bp.route("/strains")
def strains():
    return render_template("entities/strains.html")


@entities_bp.route("/shops")
def shops():
    return render_template("entities/shops.html")


@entities_bp.route("/import")
def import_page():
    """Import wizard — accepts ?type=companies|doctors|brands|products|licenses|strains|shops."""
    entity_type = request.args.get("type", "companies")
    valid_types = ["companies", "doctors", "brands", "products", "licenses", "strains", "shops"]
    if entity_type not in valid_types:
        entity_type = "companies"
    return render_template("entities/import.html", entity_type=entity_type)
