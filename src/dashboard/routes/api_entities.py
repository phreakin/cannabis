"""
REST API for manually-managed entity tables:
  Cannabis Companies, Doctors, Brands, and Products.

Endpoints (all prefixed with /api/entities):
  GET    /<type>           list (supports ?search=, ?state=, ?format=csv)
  POST   /<type>           create
  GET    /<type>/<id>      retrieve single record
  PUT    /<type>/<id>      full update
  DELETE /<type>/<id>      delete
"""
import csv
import io
import logging
from datetime import date

from flask import Blueprint, jsonify, request, make_response

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

logger = logging.getLogger(__name__)
api_entities_bp = Blueprint("api_entities", __name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _csv_response(items, filename: str):
    """Turn a list of model instances into a CSV download response."""
    if not items:
        resp = make_response("id\n")
        resp.headers["Content-Type"] = "text/csv"
        resp.headers["Content-Disposition"] = f"attachment; filename={filename}.csv"
        return resp

    data = [item.to_dict() for item in items]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=data[0].keys(), extrasaction="ignore")
    writer.writeheader()
    writer.writerows(data)

    resp = make_response(output.getvalue())
    resp.headers["Content-Type"] = "text/csv"
    resp.headers["Content-Disposition"] = f"attachment; filename={filename}.csv"
    return resp


def _parse_bool(val) -> bool:
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.lower() in ("true", "1", "yes", "on")
    return bool(val)


def _safe_float(val):
    try:
        return float(val) if val not in (None, "", "null") else None
    except (TypeError, ValueError):
        return None


def _safe_int(val):
    try:
        return int(val) if val not in (None, "", "null") else None
    except (TypeError, ValueError):
        return None


def _safe_date(val):
    if not val or val in ("", "null"):
        return None
    if isinstance(val, date):
        return val
    try:
        from datetime import datetime as dt
        return dt.strptime(val, "%Y-%m-%d").date()
    except ValueError:
        return None


# ---------------------------------------------------------------------------
#  COMPANIES
# ---------------------------------------------------------------------------

COMPANY_FIELDS = [
    "name", "logo_url", "website", "description",
    "street", "city", "state", "country", "zipcode",
    "telephone", "email", "instagram", "twitter", "facebook", "notes",
]


def _apply_company(obj: CannabisCompany, data: dict):
    for f in COMPANY_FIELDS:
        if f in data:
            setattr(obj, f, data[f] or None)


@api_entities_bp.route("/companies", methods=["GET"])
def list_companies():
    session = get_session()
    try:
        q = session.query(CannabisCompany)
        if request.args.get("search"):
            term = f"%{request.args['search']}%"
            q = q.filter(CannabisCompany.name.ilike(term))
        if request.args.get("state"):
            q = q.filter(CannabisCompany.state == request.args["state"])
        q = q.order_by(CannabisCompany.name)

        if request.args.get("format") == "csv":
            return _csv_response(q.all(), "cannabis_companies")

        total = q.count()
        page = max(1, _safe_int(request.args.get("page")) or 1)
        per_page = min(_safe_int(request.args.get("per_page")) or 500, 1000)
        items = q.offset((page - 1) * per_page).limit(per_page).all()
        return jsonify({"success": True, "data": [i.to_dict() for i in items], "total": total})
    except Exception as exc:
        logger.exception("list_companies failed")
        return jsonify({"success": False, "error": str(exc)}), 500
    finally:
        session.close()


@api_entities_bp.route("/companies", methods=["POST"])
def create_company():
    data = request.get_json(force=True) or {}
    if not data.get("name"):
        return jsonify({"success": False, "error": "name is required"}), 400
    session = get_session()
    try:
        obj = CannabisCompany()
        _apply_company(obj, data)
        session.add(obj)
        session.commit()
        return jsonify({"success": True, "data": obj.to_dict()}), 201
    except Exception as exc:
        session.rollback()
        logger.exception("create_company failed")
        return jsonify({"success": False, "error": str(exc)}), 500
    finally:
        session.close()


@api_entities_bp.route("/companies/<int:company_id>", methods=["GET"])
def get_company(company_id):
    session = get_session()
    try:
        obj = session.query(CannabisCompany).get(company_id)
        if not obj:
            return jsonify({"success": False, "error": "Not found"}), 404
        return jsonify({"success": True, "data": obj.to_dict()})
    finally:
        session.close()


@api_entities_bp.route("/companies/<int:company_id>", methods=["PUT"])
def update_company(company_id):
    data = request.get_json(force=True) or {}
    session = get_session()
    try:
        obj = session.query(CannabisCompany).get(company_id)
        if not obj:
            return jsonify({"success": False, "error": "Not found"}), 404
        _apply_company(obj, data)
        session.commit()
        return jsonify({"success": True, "data": obj.to_dict()})
    except Exception as exc:
        session.rollback()
        logger.exception("update_company failed")
        return jsonify({"success": False, "error": str(exc)}), 500
    finally:
        session.close()


@api_entities_bp.route("/companies/<int:company_id>", methods=["DELETE"])
def delete_company(company_id):
    session = get_session()
    try:
        obj = session.query(CannabisCompany).get(company_id)
        if not obj:
            return jsonify({"success": False, "error": "Not found"}), 404
        session.delete(obj)
        session.commit()
        return jsonify({"success": True})
    except Exception as exc:
        session.rollback()
        logger.exception("delete_company failed")
        return jsonify({"success": False, "error": str(exc)}), 500
    finally:
        session.close()


# ---------------------------------------------------------------------------
#  DOCTORS
# ---------------------------------------------------------------------------

DOCTOR_FIELDS = [
    "first_name", "last_name", "photo_url", "website", "practice_name",
    "street", "city", "state", "country", "zipcode",
    "telephone", "email", "specialization",
    "license_number", "license_state",
    "accepts_new_patients", "telehealth_available", "notes",
]
DOCTOR_FLOAT_FIELDS = ["latitude", "longitude"]
DOCTOR_DATE_FIELDS = ["license_expiry"]


def _apply_doctor(obj: CannabisDoctor, data: dict):
    for f in DOCTOR_FIELDS:
        if f in data:
            setattr(obj, f, data[f] or None)
    for f in DOCTOR_FLOAT_FIELDS:
        if f in data:
            setattr(obj, f, _safe_float(data[f]))
    for f in DOCTOR_DATE_FIELDS:
        if f in data:
            setattr(obj, f, _safe_date(data[f]))


@api_entities_bp.route("/doctors", methods=["GET"])
def list_doctors():
    session = get_session()
    try:
        q = session.query(CannabisDoctor)
        if request.args.get("search"):
            term = f"%{request.args['search']}%"
            q = q.filter(
                CannabisDoctor.last_name.ilike(term) |
                CannabisDoctor.first_name.ilike(term) |
                CannabisDoctor.practice_name.ilike(term)
            )
        if request.args.get("state"):
            q = q.filter(CannabisDoctor.state == request.args["state"])
        q = q.order_by(CannabisDoctor.last_name, CannabisDoctor.first_name)

        if request.args.get("format") == "csv":
            return _csv_response(q.all(), "cannabis_doctors")

        total = q.count()
        page = max(1, _safe_int(request.args.get("page")) or 1)
        per_page = min(_safe_int(request.args.get("per_page")) or 500, 1000)
        items = q.offset((page - 1) * per_page).limit(per_page).all()
        return jsonify({"success": True, "data": [i.to_dict() for i in items], "total": total})
    except Exception as exc:
        logger.exception("list_doctors failed")
        return jsonify({"success": False, "error": str(exc)}), 500
    finally:
        session.close()


@api_entities_bp.route("/doctors", methods=["POST"])
def create_doctor():
    data = request.get_json(force=True) or {}
    if not data.get("first_name") or not data.get("last_name"):
        return jsonify({"success": False, "error": "first_name and last_name are required"}), 400
    session = get_session()
    try:
        obj = CannabisDoctor()
        _apply_doctor(obj, data)
        session.add(obj)
        session.commit()
        return jsonify({"success": True, "data": obj.to_dict()}), 201
    except Exception as exc:
        session.rollback()
        logger.exception("create_doctor failed")
        return jsonify({"success": False, "error": str(exc)}), 500
    finally:
        session.close()


@api_entities_bp.route("/doctors/<int:doctor_id>", methods=["GET"])
def get_doctor(doctor_id):
    session = get_session()
    try:
        obj = session.query(CannabisDoctor).get(doctor_id)
        if not obj:
            return jsonify({"success": False, "error": "Not found"}), 404
        return jsonify({"success": True, "data": obj.to_dict()})
    finally:
        session.close()


@api_entities_bp.route("/doctors/<int:doctor_id>", methods=["PUT"])
def update_doctor(doctor_id):
    data = request.get_json(force=True) or {}
    session = get_session()
    try:
        obj = session.query(CannabisDoctor).get(doctor_id)
        if not obj:
            return jsonify({"success": False, "error": "Not found"}), 404
        _apply_doctor(obj, data)
        session.commit()
        return jsonify({"success": True, "data": obj.to_dict()})
    except Exception as exc:
        session.rollback()
        logger.exception("update_doctor failed")
        return jsonify({"success": False, "error": str(exc)}), 500
    finally:
        session.close()


@api_entities_bp.route("/doctors/<int:doctor_id>", methods=["DELETE"])
def delete_doctor(doctor_id):
    session = get_session()
    try:
        obj = session.query(CannabisDoctor).get(doctor_id)
        if not obj:
            return jsonify({"success": False, "error": "Not found"}), 404
        session.delete(obj)
        session.commit()
        return jsonify({"success": True})
    except Exception as exc:
        session.rollback()
        logger.exception("delete_doctor failed")
        return jsonify({"success": False, "error": str(exc)}), 500
    finally:
        session.close()


# ---------------------------------------------------------------------------
#  BRANDS
# ---------------------------------------------------------------------------

BRAND_FIELDS = [
    "name", "slug", "logo_url", "website", "description",
    "street", "city", "state", "country", "zipcode",
    "telephone", "email", "instagram", "twitter", "facebook",
    "category", "license_number", "license_state", "notes",
]
BRAND_INT_FIELDS = ["company_id", "founded_year"]


def _apply_brand(obj: CannabisBrand, data: dict):
    for f in BRAND_FIELDS:
        if f in data:
            setattr(obj, f, data[f] or None)
    for f in BRAND_INT_FIELDS:
        if f in data:
            setattr(obj, f, _safe_int(data[f]))


@api_entities_bp.route("/brands", methods=["GET"])
def list_brands():
    session = get_session()
    try:
        q = session.query(CannabisBrand)
        if request.args.get("search"):
            term = f"%{request.args['search']}%"
            q = q.filter(CannabisBrand.name.ilike(term))
        if request.args.get("state"):
            q = q.filter(CannabisBrand.state == request.args["state"])
        if request.args.get("category"):
            q = q.filter(CannabisBrand.category == request.args["category"])
        q = q.order_by(CannabisBrand.name)

        if request.args.get("format") == "csv":
            return _csv_response(q.all(), "cannabis_brands")

        total = q.count()
        page = max(1, _safe_int(request.args.get("page")) or 1)
        per_page = min(_safe_int(request.args.get("per_page")) or 500, 1000)
        items = q.offset((page - 1) * per_page).limit(per_page).all()
        return jsonify({"success": True, "data": [i.to_dict() for i in items], "total": total})
    except Exception as exc:
        logger.exception("list_brands failed")
        return jsonify({"success": False, "error": str(exc)}), 500
    finally:
        session.close()


@api_entities_bp.route("/brands", methods=["POST"])
def create_brand():
    data = request.get_json(force=True) or {}
    if not data.get("name"):
        return jsonify({"success": False, "error": "name is required"}), 400
    session = get_session()
    try:
        obj = CannabisBrand()
        _apply_brand(obj, data)
        session.add(obj)
        session.commit()
        return jsonify({"success": True, "data": obj.to_dict()}), 201
    except Exception as exc:
        session.rollback()
        logger.exception("create_brand failed")
        return jsonify({"success": False, "error": str(exc)}), 500
    finally:
        session.close()


@api_entities_bp.route("/brands/<int:brand_id>", methods=["GET"])
def get_brand(brand_id):
    session = get_session()
    try:
        obj = session.query(CannabisBrand).get(brand_id)
        if not obj:
            return jsonify({"success": False, "error": "Not found"}), 404
        return jsonify({"success": True, "data": obj.to_dict()})
    finally:
        session.close()


@api_entities_bp.route("/brands/<int:brand_id>", methods=["PUT"])
def update_brand(brand_id):
    data = request.get_json(force=True) or {}
    session = get_session()
    try:
        obj = session.query(CannabisBrand).get(brand_id)
        if not obj:
            return jsonify({"success": False, "error": "Not found"}), 404
        _apply_brand(obj, data)
        session.commit()
        return jsonify({"success": True, "data": obj.to_dict()})
    except Exception as exc:
        session.rollback()
        logger.exception("update_brand failed")
        return jsonify({"success": False, "error": str(exc)}), 500
    finally:
        session.close()


@api_entities_bp.route("/brands/<int:brand_id>", methods=["DELETE"])
def delete_brand(brand_id):
    session = get_session()
    try:
        obj = session.query(CannabisBrand).get(brand_id)
        if not obj:
            return jsonify({"success": False, "error": "Not found"}), 404
        session.delete(obj)
        session.commit()
        return jsonify({"success": True})
    except Exception as exc:
        session.rollback()
        logger.exception("delete_brand failed")
        return jsonify({"success": False, "error": str(exc)}), 500
    finally:
        session.close()


# ---------------------------------------------------------------------------
#  PRODUCTS
# ---------------------------------------------------------------------------

PRODUCT_FIELDS = [
    "name", "sku", "image_url", "website", "description",
    "category", "subcategory", "strain_name", "strain_type",
    "price_unit", "state", "notes",
]
PRODUCT_FLOAT_FIELDS = ["thc_percentage", "cbd_percentage", "price", "weight_grams"]
PRODUCT_INT_FIELDS = ["brand_id"]
PRODUCT_BOOL_FIELDS = ["is_active"]


def _apply_product(obj: CannabisProduct, data: dict):
    for f in PRODUCT_FIELDS:
        if f in data:
            setattr(obj, f, data[f] or None)
    for f in PRODUCT_FLOAT_FIELDS:
        if f in data:
            setattr(obj, f, _safe_float(data[f]))
    for f in PRODUCT_INT_FIELDS:
        if f in data:
            setattr(obj, f, _safe_int(data[f]))
    for f in PRODUCT_BOOL_FIELDS:
        if f in data:
            setattr(obj, f, _parse_bool(data[f]))


@api_entities_bp.route("/products", methods=["GET"])
def list_products():
    session = get_session()
    try:
        q = session.query(CannabisProduct)
        if request.args.get("search"):
            term = f"%{request.args['search']}%"
            q = q.filter(CannabisProduct.name.ilike(term))
        if request.args.get("state"):
            q = q.filter(CannabisProduct.state == request.args["state"])
        if request.args.get("category"):
            q = q.filter(CannabisProduct.category == request.args["category"])
        if request.args.get("brand_id"):
            q = q.filter(CannabisProduct.brand_id == _safe_int(request.args["brand_id"]))
        if request.args.get("active") is not None:
            q = q.filter(CannabisProduct.is_active == _parse_bool(request.args["active"]))
        q = q.order_by(CannabisProduct.name)

        if request.args.get("format") == "csv":
            return _csv_response(q.all(), "cannabis_products")

        total = q.count()
        page = max(1, _safe_int(request.args.get("page")) or 1)
        per_page = min(_safe_int(request.args.get("per_page")) or 500, 1000)
        items = q.offset((page - 1) * per_page).limit(per_page).all()
        return jsonify({"success": True, "data": [i.to_dict() for i in items], "total": total})
    except Exception as exc:
        logger.exception("list_products failed")
        return jsonify({"success": False, "error": str(exc)}), 500
    finally:
        session.close()


@api_entities_bp.route("/products", methods=["POST"])
def create_product():
    data = request.get_json(force=True) or {}
    if not data.get("name"):
        return jsonify({"success": False, "error": "name is required"}), 400
    session = get_session()
    try:
        obj = CannabisProduct()
        _apply_product(obj, data)
        session.add(obj)
        session.commit()
        return jsonify({"success": True, "data": obj.to_dict()}), 201
    except Exception as exc:
        session.rollback()
        logger.exception("create_product failed")
        return jsonify({"success": False, "error": str(exc)}), 500
    finally:
        session.close()


@api_entities_bp.route("/products/<int:product_id>", methods=["GET"])
def get_product(product_id):
    session = get_session()
    try:
        obj = session.query(CannabisProduct).get(product_id)
        if not obj:
            return jsonify({"success": False, "error": "Not found"}), 404
        return jsonify({"success": True, "data": obj.to_dict()})
    finally:
        session.close()


@api_entities_bp.route("/products/<int:product_id>", methods=["PUT"])
def update_product(product_id):
    data = request.get_json(force=True) or {}
    session = get_session()
    try:
        obj = session.query(CannabisProduct).get(product_id)
        if not obj:
            return jsonify({"success": False, "error": "Not found"}), 404
        _apply_product(obj, data)
        session.commit()
        return jsonify({"success": True, "data": obj.to_dict()})
    except Exception as exc:
        session.rollback()
        logger.exception("update_product failed")
        return jsonify({"success": False, "error": str(exc)}), 500
    finally:
        session.close()


@api_entities_bp.route("/products/<int:product_id>", methods=["DELETE"])
def delete_product(product_id):
    session = get_session()
    try:
        obj = session.query(CannabisProduct).get(product_id)
        if not obj:
            return jsonify({"success": False, "error": "Not found"}), 404
        session.delete(obj)
        session.commit()
        return jsonify({"success": True})
    except Exception as exc:
        session.rollback()
        logger.exception("delete_product failed")
        return jsonify({"success": False, "error": str(exc)}), 500
    finally:
        session.close()


# =============================================================================
#  IMPORT SUPPORT  –  preview + bulk-import for all entity types
# =============================================================================
import json as _json
import re as _re

# ---------------------------------------------------------------------------
# Entity config registry
# ---------------------------------------------------------------------------
_ENTITY_ALL_FIELDS = {
    'companies': COMPANY_FIELDS,
    'doctors':   DOCTOR_FIELDS + list(DOCTOR_FLOAT_FIELDS) + list(DOCTOR_DATE_FIELDS),
    'brands':    BRAND_FIELDS + list(BRAND_INT_FIELDS),
    'products':  PRODUCT_FIELDS + list(PRODUCT_FLOAT_FIELDS)
                 + list(PRODUCT_INT_FIELDS) + list(PRODUCT_BOOL_FIELDS),
}

_ENTITY_REQUIRED = {
    'companies': ['name'],
    'doctors':   ['first_name', 'last_name'],
    'brands':    ['name'],
    'products':  ['name'],
}

_ENTITY_MODELS_MAP = {
    'companies': (CannabisCompany, _apply_company),
    'doctors':   (CannabisDoctor,  _apply_doctor),
    'brands':    (CannabisBrand,   _apply_brand),
    'products':  (CannabisProduct, _apply_product),
}

_ENTITY_DUPE_KEYS = {
    'companies': ['name'],
    'doctors':   [],
    'brands':    ['name'],
    'products':  ['sku', 'name'],
}

_FIELD_LABELS = {
    'name': 'Name', 'first_name': 'First Name', 'last_name': 'Last Name',
    'photo_url': 'Photo URL', 'logo_url': 'Logo URL', 'image_url': 'Image URL',
    'website': 'Website', 'description': 'Description', 'street': 'Street',
    'city': 'City', 'state': 'State', 'country': 'Country', 'zipcode': 'ZIP Code',
    'telephone': 'Telephone', 'email': 'Email', 'instagram': 'Instagram',
    'twitter': 'Twitter / X', 'facebook': 'Facebook', 'notes': 'Notes',
    'slug': 'Slug', 'company_id': 'Company ID', 'brand_id': 'Brand ID',
    'founded_year': 'Founded Year', 'category': 'Category', 'subcategory': 'Subcategory',
    'license_number': 'License Number', 'license_state': 'License State',
    'license_expiry': 'License Expiry', 'accepts_new_patients': 'Accepts New Patients',
    'telehealth_available': 'Telehealth Available', 'specialization': 'Specialization',
    'latitude': 'Latitude', 'longitude': 'Longitude', 'practice_name': 'Practice Name',
    'sku': 'SKU', 'strain_name': 'Strain Name', 'strain_type': 'Strain Type',
    'thc_percentage': 'THC %', 'cbd_percentage': 'CBD %', 'price': 'Price',
    'price_unit': 'Price Unit', 'weight_grams': 'Weight (g)', 'is_active': 'Is Active',
    # Strain cannabinoids + characteristics
    'thc': 'THC %', 'thca': 'THCA %', 'thcv': 'THCV %',
    'cbd': 'CBD %', 'cbda': 'CBDA %', 'cbdv': 'CBDV %',
    'cbn': 'CBN %', 'cbg': 'CBG %', 'cbc': 'CBC %',
    'crosses': 'Crosses', 'breeder': 'Breeder',
    'effects': 'Effects', 'ailments': 'Ailments',
    'flavors': 'Flavors', 'terpenes': 'Terpenes',
    'source_id': 'Source ID', 'status': 'Status',
}

# ---------------------------------------------------------------------------
# Auto-mapping helpers
# ---------------------------------------------------------------------------

_ALIASES = {
    'phone': 'telephone', 'tel': 'telephone', 'phone_number': 'telephone',
    'mobile': 'telephone', 'url': 'website', 'site': 'website', 'web': 'website',
    'logo': 'logo_url', 'image': 'image_url', 'photo': 'photo_url',
    'img': 'image_url', 'img_url': 'image_url', 'picture': 'photo_url',
    'zip': 'zipcode', 'postal_code': 'zipcode', 'postal': 'zipcode', 'postcode': 'zipcode',
    'active': 'is_active', 'enabled': 'is_active',
    'thc': 'thc_percentage', 'cbd': 'cbd_percentage',
    'price_per': 'price_unit', 'unit_price': 'price', 'cost': 'price',
    'brand': 'brand_id', 'company': 'company_id',
    'founded': 'founded_year', 'year_founded': 'founded_year', 'est': 'founded_year',
    'first': 'first_name', 'last': 'last_name', 'fname': 'first_name',
    'lname': 'last_name', 'firstname': 'first_name', 'lastname': 'last_name',
    'surname': 'last_name', 'street_address': 'street', 'address': 'street',
    'addr': 'street', 'st': 'state', 'province': 'state',
    'ig': 'instagram', 'insta': 'instagram', 'fb': 'facebook',
    'twitter_handle': 'twitter', 'x_handle': 'twitter',
    'wt': 'weight_grams', 'weight': 'weight_grams', 'grams': 'weight_grams',
    'strain': 'strain_name', 'practice': 'practice_name', 'clinic': 'practice_name',
    'specialty': 'specialization', 'speciality': 'specialization',
    'license': 'license_number', 'lic_num': 'license_number',
    'lat': 'latitude', 'lng': 'longitude', 'lon': 'longitude', 'long': 'longitude',
}

_DOCTOR_FULL_NAME_SLUGS = {
    'full_name', 'name', 'doctor_name', 'physician_name',
    'doctor', 'physician', 'provider_name', 'provider',
}


def _slugify(h):
    h = h.strip().lower()
    h = _re.sub(r'[^a-z0-9]+', '_', h)
    return h.strip('_')


def _auto_map(headers, entity_type):
    fields = set(_ENTITY_ALL_FIELDS.get(entity_type, []))
    mapping = {}
    for h in headers:
        slug = _slugify(h)
        if slug in fields:
            mapping[h] = slug
        elif entity_type == 'doctors' and slug in _DOCTOR_FULL_NAME_SLUGS:
            mapping[h] = '__full_name__'
        elif slug in _ALIASES and _ALIASES[slug] in fields:
            mapping[h] = _ALIASES[slug]
        else:
            mapping[h] = None
    return mapping


def _parse_upload(fileobj, filename):
    raw = fileobj.read()
    fname = (filename or '').lower()

    if fname.endswith('.json') or fname.endswith('.jsonl'):
        text = raw.decode('utf-8-sig', errors='replace')
        try:
            parsed = _json.loads(text)
            if isinstance(parsed, list):
                return parsed
            if isinstance(parsed, dict):
                for key in ('data', 'records', 'items', 'results'):
                    if isinstance(parsed.get(key), list):
                        return parsed[key]
            return [parsed] if isinstance(parsed, dict) else []
        except _json.JSONDecodeError:
            pass
        rows = []
        for line in text.splitlines():
            line = line.strip()
            if line:
                rows.append(_json.loads(line))
        return rows

    text = raw.decode('utf-8-sig', errors='replace')
    sample = text[:4096]
    try:
        dialect = csv.Sniffer().sniff(sample, delimiters=',\t|;')
    except csv.Error:
        dialect = csv.excel
    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    return [dict(row) for row in reader if any(str(v).strip() for v in row.values() if v is not None)]


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@api_entities_bp.route("/<entity_type>/preview", methods=["POST"])
def preview_import(entity_type):
    if entity_type not in _ENTITY_MODELS_MAP:
        return jsonify({"success": False, "error": f"Unknown entity type: {entity_type}"}), 400
    f = request.files.get('file')
    if not f or not f.filename:
        return jsonify({"success": False, "error": "No file uploaded"}), 400
    try:
        rows = _parse_upload(f, f.filename)
    except Exception as exc:
        logger.exception("preview_import parse error")
        return jsonify({"success": False, "error": f"Could not parse file: {exc}"}), 400
    if not rows:
        return jsonify({"success": False, "error": "File is empty or has no data rows"}), 400

    headers = list(rows[0].keys())
    mapping = _auto_map(headers, entity_type)
    all_fields = list(_ENTITY_ALL_FIELDS.get(entity_type, []))
    field_options = (['__full_name__'] + all_fields) if entity_type == 'doctors' else all_fields

    return jsonify({
        "success": True,
        "total_rows": len(rows),
        "headers": headers,
        "rows": rows[:10],          # preview rows (JS expects "rows")
        "auto_mapping": mapping,
        "field_options": field_options,
        "field_labels": _FIELD_LABELS,
        "required_fields": _ENTITY_REQUIRED.get(entity_type, []),
    })


@api_entities_bp.route("/<entity_type>/import", methods=["POST"])
def import_entities(entity_type):
    if entity_type not in _ENTITY_MODELS_MAP:
        return jsonify({"success": False, "error": f"Unknown entity type: {entity_type}"}), 400
    f = request.files.get('file')
    if not f or not f.filename:
        return jsonify({"success": False, "error": "No file uploaded"}), 400

    mode        = request.form.get('mode', 'insert')
    skip_errors = request.form.get('skip_errors', 'true').lower() in ('true', '1', 'yes')
    mapping_raw = request.form.get('mapping', '{}')
    try:
        col_map = _json.loads(mapping_raw)
    except Exception:
        col_map = {}

    try:
        rows = _parse_upload(f, f.filename)
    except Exception as exc:
        return jsonify({"success": False, "error": f"Could not parse file: {exc}"}), 400
    if not rows:
        return jsonify({"success": False, "error": "File is empty"}), 400

    if not col_map:
        col_map = _auto_map(list(rows[0].keys()), entity_type)

    model_cls, apply_fn = _ENTITY_MODELS_MAP[entity_type]
    required            = _ENTITY_REQUIRED[entity_type]
    dupe_keys           = _ENTITY_DUPE_KEYS[entity_type]
    stats = {"imported": 0, "skipped": 0, "errors": []}
    session = get_session()

    try:
        for row_num, raw_row in enumerate(rows, start=2):
            data = {}
            for col, field in col_map.items():
                if not field or col not in raw_row:
                    continue
                val = raw_row[col]
                if isinstance(val, str):
                    val = val.strip() or None
                data[field] = val

            if '__full_name__' in data:
                full = (data.pop('__full_name__') or '').strip()
                parts = full.split(' ', 1)
                data.setdefault('first_name', parts[0] if parts else '')
                data.setdefault('last_name', parts[1] if len(parts) > 1 else '')

            missing = [fld for fld in required if not data.get(fld)]
            if missing:
                stats['skipped'] += 1
                if len(stats['errors']) < 200:
                    stats['errors'].append({"row": row_num, "error": f"Missing required: {', '.join(missing)}"})
                continue

            if mode == 'skip_dupes' and dupe_keys:
                existing = None
                for key in dupe_keys:
                    val = data.get(key)
                    if val:
                        existing = session.query(model_cls).filter(getattr(model_cls, key) == val).first()
                        if existing:
                            break
                if existing:
                    stats['skipped'] += 1
                    continue

            try:
                obj = model_cls()
                apply_fn(obj, data)
                session.add(obj)
                session.flush()
                stats['imported'] += 1
            except Exception as row_err:
                session.rollback()
                stats['skipped'] += 1
                if len(stats['errors']) < 200:
                    stats['errors'].append({"row": row_num, "error": str(row_err)})
                if not skip_errors:
                    return jsonify({"success": False, "error": str(row_err), **stats}), 500

        session.commit()
        return jsonify({"success": True, **stats})
    except Exception as exc:
        session.rollback()
        logger.exception("import_entities failed")
        return jsonify({"success": False, "error": str(exc)}), 500
    finally:
        session.close()


@api_entities_bp.route("/<entity_type>/sample", methods=["GET"])
def download_sample(entity_type):
    if entity_type not in _ENTITY_ALL_FIELDS:
        return jsonify({"success": False, "error": "Unknown entity type"}), 400
    fmt    = request.args.get('format', 'csv')
    fields = _ENTITY_ALL_FIELDS[entity_type]
    if fmt == 'json':
        sample = [{f: '' for f in fields}]
        resp = make_response(_json.dumps(sample, indent=2))
        resp.headers['Content-Type'] = 'application/json'
        resp.headers['Content-Disposition'] = f'attachment; filename=sample_{entity_type}.json'
        return resp
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fields)
    writer.writeheader()
    writer.writerow({f: '' for f in fields})
    resp = make_response(buf.getvalue())
    resp.headers['Content-Type'] = 'text/csv'
    resp.headers['Content-Disposition'] = f'attachment; filename=sample_{entity_type}.csv'
    return resp


# ---------------------------------------------------------------------------
#  LICENSES
# ---------------------------------------------------------------------------

LICENSE_FIELDS = [
    'license_number', 'license_url', 'business_license_number', 'business_license_url',
    'license_type', 'license_status', 'business_name', 'dba_name',
    'street', 'city', 'state', 'zipcode', 'country',
    'source_state', 'source_file',
]


def _apply_license(obj: CannabisLicense, data: dict):
    for f in LICENSE_FIELDS:
        if f in data:
            setattr(obj, f, data[f] or None)


@api_entities_bp.route("/licenses", methods=["GET"])
def list_licenses():
    session = get_session()
    try:
        q = session.query(CannabisLicense)
        if request.args.get("search"):
            term = f"%{request.args['search']}%"
            q = q.filter(
                CannabisLicense.business_name.ilike(term) |
                CannabisLicense.license_number.ilike(term)
            )
        if request.args.get("state"):
            q = q.filter(CannabisLicense.state == request.args["state"])
        if request.args.get("license_type"):
            q = q.filter(CannabisLicense.license_type == request.args["license_type"])
        q = q.order_by(CannabisLicense.business_name)

        if request.args.get("format") == "csv":
            return _csv_response(q.all(), "cannabis_licenses")

        total = q.count()
        page = max(1, _safe_int(request.args.get("page")) or 1)
        per_page = min(_safe_int(request.args.get("per_page")) or 500, 1000)
        items = q.offset((page - 1) * per_page).limit(per_page).all()
        return jsonify({"success": True, "data": [i.to_dict() for i in items], "total": total})
    except Exception as exc:
        logger.exception("list_licenses failed")
        return jsonify({"success": False, "error": str(exc)}), 500
    finally:
        session.close()


@api_entities_bp.route("/licenses", methods=["POST"])
def create_license():
    data = request.get_json(force=True) or {}
    if not data.get("business_name"):
        return jsonify({"success": False, "error": "business_name is required"}), 400
    session = get_session()
    try:
        obj = CannabisLicense()
        _apply_license(obj, data)
        session.add(obj)
        session.commit()
        return jsonify({"success": True, "data": obj.to_dict()}), 201
    except Exception as exc:
        session.rollback()
        logger.exception("create_license failed")
        return jsonify({"success": False, "error": str(exc)}), 400
    finally:
        session.close()


@api_entities_bp.route("/licenses/<int:eid>", methods=["GET"])
def get_license(eid):
    session = get_session()
    try:
        obj = session.query(CannabisLicense).get(eid)
        if not obj:
            return jsonify({"success": False, "error": "Not found"}), 404
        return jsonify({"success": True, "data": obj.to_dict()})
    finally:
        session.close()


@api_entities_bp.route("/licenses/<int:eid>", methods=["PUT"])
def update_license(eid):
    data = request.get_json(force=True) or {}
    session = get_session()
    try:
        obj = session.query(CannabisLicense).get(eid)
        if not obj:
            return jsonify({"success": False, "error": "Not found"}), 404
        _apply_license(obj, data)
        session.commit()
        return jsonify({"success": True, "data": obj.to_dict()})
    except Exception as exc:
        session.rollback()
        logger.exception("update_license failed")
        return jsonify({"success": False, "error": str(exc)}), 400
    finally:
        session.close()


@api_entities_bp.route("/licenses/<int:eid>", methods=["DELETE"])
def delete_license(eid):
    session = get_session()
    try:
        obj = session.query(CannabisLicense).get(eid)
        if not obj:
            return jsonify({"success": False, "error": "Not found"}), 404
        session.delete(obj)
        session.commit()
        return jsonify({"success": True})
    except Exception as exc:
        session.rollback()
        logger.exception("delete_license failed")
        return jsonify({"success": False, "error": str(exc)}), 400
    finally:
        session.close()


# ---------------------------------------------------------------------------
#  STRAINS
# ---------------------------------------------------------------------------

STRAIN_FIELDS = [
    'name', 'slug', 'image_url', 'description', 'strain_type',
    'crosses', 'breeder', 'effects', 'ailments', 'flavors', 'terpenes',
    'thc', 'thca', 'thcv', 'cbd', 'cbda', 'cbdv',
    'cbn', 'cbg', 'cbc', 'status', 'source_id',
]
STRAIN_FLOAT_FIELDS = ['thc', 'thca', 'thcv', 'cbd', 'cbda', 'cbdv', 'cbn', 'cbg', 'cbc']
STRAIN_INT_FIELDS = ['status', 'source_id']
STRAIN_STR_FIELDS = [f for f in STRAIN_FIELDS if f not in STRAIN_FLOAT_FIELDS and f not in STRAIN_INT_FIELDS]


def _apply_strain(obj: CannabisStrain, data: dict):
    for f in STRAIN_STR_FIELDS:
        if f in data:
            setattr(obj, f, data[f] or None)
    for f in STRAIN_FLOAT_FIELDS:
        if f in data:
            setattr(obj, f, _safe_float(data[f]))
    for f in STRAIN_INT_FIELDS:
        if f in data:
            setattr(obj, f, _safe_int(data[f]))


# Register strains in the CSV import pipeline
_ENTITY_ALL_FIELDS['strains'] = STRAIN_STR_FIELDS + list(STRAIN_FLOAT_FIELDS) + list(STRAIN_INT_FIELDS)
_ENTITY_REQUIRED['strains']   = ['name']
_ENTITY_MODELS_MAP['strains'] = (CannabisStrain, _apply_strain)
_ENTITY_DUPE_KEYS['strains']  = ['name', 'slug']


@api_entities_bp.route("/strains", methods=["GET"])
def list_strains():
    session = get_session()
    try:
        q = session.query(CannabisStrain)
        if request.args.get("search"):
            term = f"%{request.args['search']}%"
            q = q.filter(
                CannabisStrain.name.ilike(term) |
                CannabisStrain.breeder.ilike(term)
            )
        if request.args.get("strain_type"):
            q = q.filter(CannabisStrain.strain_type == request.args["strain_type"])
        q = q.order_by(CannabisStrain.name)

        if request.args.get("format") == "csv":
            return _csv_response(q.all(), "cannabis_strains")

        total = q.count()
        page = max(1, _safe_int(request.args.get("page")) or 1)
        per_page = min(_safe_int(request.args.get("per_page")) or 500, 1000)
        items = q.offset((page - 1) * per_page).limit(per_page).all()
        return jsonify({"success": True, "data": [i.to_dict() for i in items], "total": total})
    except Exception as exc:
        logger.exception("list_strains failed")
        return jsonify({"success": False, "error": str(exc)}), 500
    finally:
        session.close()


@api_entities_bp.route("/strains", methods=["POST"])
def create_strain():
    data = request.get_json(force=True) or {}
    if not data.get("name"):
        return jsonify({"success": False, "error": "name is required"}), 400
    session = get_session()
    try:
        obj = CannabisStrain()
        _apply_strain(obj, data)
        session.add(obj)
        session.commit()
        return jsonify({"success": True, "data": obj.to_dict()}), 201
    except Exception as exc:
        session.rollback()
        logger.exception("create_strain failed")
        return jsonify({"success": False, "error": str(exc)}), 400
    finally:
        session.close()


@api_entities_bp.route("/strains/<int:eid>", methods=["GET"])
def get_strain(eid):
    session = get_session()
    try:
        obj = session.query(CannabisStrain).get(eid)
        if not obj:
            return jsonify({"success": False, "error": "Not found"}), 404
        return jsonify({"success": True, "data": obj.to_dict()})
    finally:
        session.close()


@api_entities_bp.route("/strains/<int:eid>", methods=["PUT"])
def update_strain(eid):
    data = request.get_json(force=True) or {}
    session = get_session()
    try:
        obj = session.query(CannabisStrain).get(eid)
        if not obj:
            return jsonify({"success": False, "error": "Not found"}), 404
        _apply_strain(obj, data)
        session.commit()
        return jsonify({"success": True, "data": obj.to_dict()})
    except Exception as exc:
        session.rollback()
        logger.exception("update_strain failed")
        return jsonify({"success": False, "error": str(exc)}), 400
    finally:
        session.close()


@api_entities_bp.route("/strains/<int:eid>", methods=["DELETE"])
def delete_strain(eid):
    session = get_session()
    try:
        obj = session.query(CannabisStrain).get(eid)
        if not obj:
            return jsonify({"success": False, "error": "Not found"}), 404
        session.delete(obj)
        session.commit()
        return jsonify({"success": True})
    except Exception as exc:
        session.rollback()
        logger.exception("delete_strain failed")
        return jsonify({"success": False, "error": str(exc)}), 400
    finally:
        session.close()


# ---------------------------------------------------------------------------
#  SHOPS
# ---------------------------------------------------------------------------

SHOP_FIELDS = [
    'name', 'slug', 'shop_type', 'description', 'featured_image', 'avatar_url',
    'street', 'city', 'state', 'zipcode', 'country',
    'latitude', 'longitude',
    'telephone', 'website', 'email',
    'instagram', 'twitter', 'facebook',
    'rating', 'tags', 'hours', 'status', 'source_id',
]
SHOP_FLOAT_FIELDS = ['latitude', 'longitude', 'rating']
SHOP_INT_FIELDS = ['status', 'source_id']
SHOP_STR_FIELDS = [f for f in SHOP_FIELDS if f not in SHOP_FLOAT_FIELDS and f not in SHOP_INT_FIELDS]


def _apply_shop(obj: CannabisShop, data: dict):
    for f in SHOP_STR_FIELDS:
        if f in data:
            setattr(obj, f, data[f] or None)
    for f in SHOP_FLOAT_FIELDS:
        if f in data:
            setattr(obj, f, _safe_float(data[f]))
    for f in SHOP_INT_FIELDS:
        if f in data:
            setattr(obj, f, _safe_int(data[f]))


@api_entities_bp.route("/shops", methods=["GET"])
def list_shops():
    session = get_session()
    try:
        q = session.query(CannabisShop)
        if request.args.get("search"):
            term = f"%{request.args['search']}%"
            q = q.filter(
                CannabisShop.name.ilike(term) |
                CannabisShop.city.ilike(term)
            )
        if request.args.get("state"):
            q = q.filter(CannabisShop.state == request.args["state"])
        if request.args.get("shop_type"):
            q = q.filter(CannabisShop.shop_type == request.args["shop_type"])
        q = q.order_by(CannabisShop.name)

        if request.args.get("format") == "csv":
            return _csv_response(q.all(), "cannabis_shops")

        total = q.count()
        page = max(1, _safe_int(request.args.get("page")) or 1)
        per_page = min(_safe_int(request.args.get("per_page")) or 500, 1000)
        items = q.offset((page - 1) * per_page).limit(per_page).all()
        return jsonify({"success": True, "data": [i.to_dict() for i in items], "total": total})
    except Exception as exc:
        logger.exception("list_shops failed")
        return jsonify({"success": False, "error": str(exc)}), 500
    finally:
        session.close()


@api_entities_bp.route("/shops", methods=["POST"])
def create_shop():
    data = request.get_json(force=True) or {}
    if not data.get("name"):
        return jsonify({"success": False, "error": "name is required"}), 400
    session = get_session()
    try:
        obj = CannabisShop()
        _apply_shop(obj, data)
        session.add(obj)
        session.commit()
        return jsonify({"success": True, "data": obj.to_dict()}), 201
    except Exception as exc:
        session.rollback()
        logger.exception("create_shop failed")
        return jsonify({"success": False, "error": str(exc)}), 400
    finally:
        session.close()


@api_entities_bp.route("/shops/<int:eid>", methods=["GET"])
def get_shop(eid):
    session = get_session()
    try:
        obj = session.query(CannabisShop).get(eid)
        if not obj:
            return jsonify({"success": False, "error": "Not found"}), 404
        return jsonify({"success": True, "data": obj.to_dict()})
    finally:
        session.close()


@api_entities_bp.route("/shops/<int:eid>", methods=["PUT"])
def update_shop(eid):
    data = request.get_json(force=True) or {}
    session = get_session()
    try:
        obj = session.query(CannabisShop).get(eid)
        if not obj:
            return jsonify({"success": False, "error": "Not found"}), 404
        _apply_shop(obj, data)
        session.commit()
        return jsonify({"success": True, "data": obj.to_dict()})
    except Exception as exc:
        session.rollback()
        logger.exception("update_shop failed")
        return jsonify({"success": False, "error": str(exc)}), 400
    finally:
        session.close()


@api_entities_bp.route("/shops/<int:eid>", methods=["DELETE"])
def delete_shop(eid):
    session = get_session()
    try:
        obj = session.query(CannabisShop).get(eid)
        if not obj:
            return jsonify({"success": False, "error": "Not found"}), 404
        session.delete(obj)
        session.commit()
        return jsonify({"success": True})
    except Exception as exc:
        session.rollback()
        logger.exception("delete_shop failed")
        return jsonify({"success": False, "error": str(exc)}), 400
    finally:
        session.close()
