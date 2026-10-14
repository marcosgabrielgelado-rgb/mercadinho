from __future__ import annotations

import hmac
import os
import secrets
import sqlite3
import uuid
from datetime import datetime
from functools import wraps
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv
from flask import (
    Flask, abort, flash, g, redirect, render_template, request,
    session, url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")
INSTANCE_DIR = Path(os.getenv("DATA_DIR", str(BASE_DIR / "instance"))).resolve()
UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", str(BASE_DIR / "static" / "uploads"))).resolve()
INSTANCE_DIR.mkdir(parents=True, exist_ok=True)
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

app = Flask(__name__, instance_path=str(INSTANCE_DIR))
app.config.update(
    SECRET_KEY=os.getenv("SECRET_KEY", "development-only-change-this-secret-key"),
    MAX_CONTENT_LENGTH=5 * 1024 * 1024,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.getenv("COOKIE_SECURE", "0") == "1",
)
DATABASE = Path(os.getenv("DATABASE_PATH", str(INSTANCE_DIR / "mercado.db"))).resolve()
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = generate_password_hash(os.getenv("ADMIN_PASSWORD", "TroqueEstaSenha123!"))
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}

SAMPLE_PRODUCTS = [
    {
        "name": "Banana-prata", "brand": "Hortifruti", "category": "Hortifruti",
        "description": "Banana fresca, ideal para o café da manhã.", "price": 5.99,
        "old_price": 7.49, "unit": "kg", "image_url": "https://images.unsplash.com/photo-1571771894821-ce9b6c11b08e?auto=format&fit=crop&w=900&q=85",
        "featured": 1, "active": 1,
    },
    {
        "name": "Leite integral", "brand": "Fazenda", "category": "Laticínios",
        "description": "Leite integral UHT, embalagem de 1 litro.", "price": 4.79,
        "old_price": None, "unit": "unidade", "image_url": "https://images.unsplash.com/photo-1563636619-e9143da7973b?auto=format&fit=crop&w=900&q=85",
        "featured": 1, "active": 1,
    },
    {
        "name": "Tomate italiano", "brand": "Hortifruti", "category": "Hortifruti",
        "description": "Tomates selecionados para saladas e molhos.", "price": 6.49,
        "old_price": 8.99, "unit": "kg", "image_url": "https://images.unsplash.com/photo-1546094096-0df4bcaaa337?auto=format&fit=crop&w=900&q=85",
        "featured": 1, "active": 1,
    },
    {
        "name": "Pão de forma", "brand": "Pão da Casa", "category": "Padaria",
        "description": "Pão macio para sanduíches e torradas.", "price": 7.99,
        "old_price": None, "unit": "pacote", "image_url": "https://images.unsplash.com/photo-1509440159596-0249088772ff?auto=format&fit=crop&w=900&q=85",
        "featured": 0, "active": 1,
    },
    {
        "name": "Café tradicional", "brand": "Bom Aroma", "category": "Mercearia",
        "description": "Café torrado e moído, pacote de 500 g.", "price": 18.90,
        "old_price": 22.90, "unit": "pacote", "image_url": "https://images.unsplash.com/photo-1559056199-641a0ac8b55e?auto=format&fit=crop&w=900&q=85",
        "featured": 1, "active": 1,
    },
    {
        "name": "Arroz tipo 1", "brand": "Grão Bom", "category": "Mercearia",
        "description": "Arroz tipo 1, pacote de 5 kg.", "price": 27.90,
        "old_price": None, "unit": "pacote", "image_url": "https://images.unsplash.com/photo-1586201375761-83865001e31c?auto=format&fit=crop&w=900&q=85",
        "featured": 0, "active": 1,
    },
    {
        "name": "Suco de laranja", "brand": "Pomare", "category": "Bebidas",
        "description": "Suco de laranja refrescante, garrafa de 1 litro.", "price": 8.49,
        "old_price": 9.99, "unit": "garrafa", "image_url": "https://images.unsplash.com/photo-1600271886742-f049cd451bba?auto=format&fit=crop&w=900&q=85",
        "featured": 0, "active": 1,
    },
    {
        "name": "Ovos brancos", "brand": "Sítio Feliz", "category": "Laticínios",
        "description": "Bandeja com 12 ovos selecionados.", "price": 10.90,
        "old_price": None, "unit": "bandeja", "image_url": "https://images.unsplash.com/photo-1506976785307-8732e854ad03?auto=format&fit=crop&w=900&q=85",
        "featured": 0, "active": 1,
    },
]


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    db.executescript(
        """
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            brand TEXT NOT NULL DEFAULT '',
            category TEXT NOT NULL DEFAULT 'Mercearia',
            description TEXT NOT NULL DEFAULT '',
            price REAL NOT NULL CHECK(price >= 0),
            old_price REAL NULL CHECK(old_price IS NULL OR old_price >= 0),
            unit TEXT NOT NULL DEFAULT 'unidade',
            image_url TEXT NOT NULL DEFAULT '',
            image_filename TEXT NOT NULL DEFAULT '',
            featured INTEGER NOT NULL DEFAULT 0,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        """
    )
    count = db.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    if count == 0:
        db.executemany(
            """INSERT INTO products
            (name, brand, category, description, price, old_price, unit, image_url, featured, active)
            VALUES (:name, :brand, :category, :description, :price, :old_price, :unit, :image_url, :featured, :active)""",
            SAMPLE_PRODUCTS,
        )
    for key, value in {
        "store_name": os.getenv("STORE_NAME", "Mercado do Bairro"),
        "store_tagline": os.getenv("STORE_TAGLINE", "Preço bom é aqui. Todo dia."),
        "store_notice": "Ofertas válidas enquanto durarem os estoques.",
    }.items():
        db.execute("INSERT OR IGNORE INTO settings(key, value) VALUES (?, ?)", (key, value))
    db.commit()
    db.close()


def get_setting(key: str, default: str = "") -> str:
    row = get_db().execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default


def csrf_token() -> str:
    if "csrf_token" not in session:
        session["csrf_token"] = secrets.token_urlsafe(32)
    return session["csrf_token"]


@app.before_request
def protect_posts():
    if request.method == "POST":
        expected = session.get("csrf_token", "")
        provided = request.form.get("csrf_token", "")
        if not expected or not hmac.compare_digest(expected, provided):
            abort(400, description="Token de segurança inválido. Atualize a página e tente novamente.")


@app.context_processor
def inject_template_helpers():
    return {
        "csrf_token": csrf_token,
        "store_name": get_setting("store_name", "Mercado do Bairro"),
        "store_tagline": get_setting("store_tagline", "Preço bom é aqui. Todo dia."),
        "store_notice": get_setting("store_notice", "Ofertas válidas enquanto durarem os estoques."),
        "admin_logged_in": bool(session.get("admin_logged_in")),
    }


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login", next=request.path))
        return view(*args, **kwargs)
    return wrapped


def valid_image_url(value: str) -> bool:
    if not value:
        return True
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def save_uploaded_image(file_storage) -> str:
    if not file_storage or not file_storage.filename:
        return ""
    safe_name = secure_filename(file_storage.filename)
    if "." not in safe_name:
        raise ValueError("Escolha uma imagem PNG, JPG, JPEG, WEBP ou GIF.")
    extension = safe_name.rsplit(".", 1)[1].lower()
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        raise ValueError("Formato não permitido. Use PNG, JPG, JPEG, WEBP ou GIF.")
    filename = f"{uuid.uuid4().hex}.{extension}"
    destination = UPLOAD_DIR / filename
    file_storage.save(destination)
    return filename


def remove_uploaded_image(filename: str) -> None:
    if not filename:
        return
    try:
        path = (UPLOAD_DIR / filename).resolve()
        if path.parent == UPLOAD_DIR.resolve() and path.exists():
            path.unlink()
    except OSError:
        pass


def parse_product_form(existing=None) -> dict:
    form = request.form
    name = form.get("name", "").strip()
    category = form.get("category", "Mercearia").strip() or "Mercearia"
    unit = form.get("unit", "unidade").strip() or "unidade"
    if not name:
        raise ValueError("Informe o nome do produto.")
    try:
        price = float(form.get("price", "").replace(",", "."))
        old_price_raw = form.get("old_price", "").strip().replace(",", ".")
        old_price = float(old_price_raw) if old_price_raw else None
    except ValueError:
        raise ValueError("Confira os preços informados.")
    if price < 0 or (old_price is not None and old_price < 0):
        raise ValueError("Os preços não podem ser negativos.")
    image_url = form.get("image_url", "").strip()
    if not valid_image_url(image_url):
        raise ValueError("O link da imagem precisa começar com http:// ou https://.")

    old_filename = existing["image_filename"] if existing else ""
    uploaded = request.files.get("image_file")
    new_filename = save_uploaded_image(uploaded) if uploaded and uploaded.filename else ""
    image_filename = old_filename
    if new_filename:
        image_filename = new_filename
        image_url = ""
        if old_filename:
            remove_uploaded_image(old_filename)
    elif image_url:
        image_filename = ""
        if old_filename:
            remove_uploaded_image(old_filename)
    elif not existing:
        image_filename = ""

    return {
        "name": name,
        "brand": form.get("brand", "").strip(),
        "category": category,
        "description": form.get("description", "").strip(),
        "price": price,
        "old_price": old_price,
        "unit": unit,
        "image_url": image_url,
        "image_filename": image_filename,
        "featured": 1 if form.get("featured") else 0,
        "active": 1 if form.get("active") else 0,
    }


def image_for(product) -> str:
    if product["image_url"]:
        return product["image_url"]
    if product["image_filename"]:
        return url_for("static", filename=f"uploads/{product['image_filename']}")
    return ""


@app.template_filter("brl")
def brl(value):
    try:
        formatted = f"{float(value):,.2f}"
        return "R$ " + formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    except (TypeError, ValueError):
        return "R$ 0,00"


@app.template_filter("discount")
def discount(old_price, price):
    try:
        if old_price and float(old_price) > float(price) > 0:
            return round((float(old_price) - float(price)) / float(old_price) * 100)
    except (TypeError, ValueError):
        pass
    return 0


app.jinja_env.globals["image_for"] = image_for


@app.route("/")
def index():
    db = get_db()
    search = request.args.get("q", "").strip()
    category = request.args.get("categoria", "").strip()
    only_offers = request.args.get("ofertas", "") == "1"
    clauses = ["active = 1"]
    params: list[object] = []
    if search:
        clauses.append("(name LIKE ? OR brand LIKE ? OR category LIKE ? OR description LIKE ?)")
        like = f"%{search}%"
        params.extend([like, like, like, like])
    if category:
        clauses.append("category = ?")
        params.append(category)
    if only_offers:
        clauses.append("old_price IS NOT NULL AND old_price > price")
    where = " AND ".join(clauses)
    products = db.execute(f"SELECT * FROM products WHERE {where} ORDER BY featured DESC, name COLLATE NOCASE", params).fetchall()
    categories = db.execute("SELECT DISTINCT category FROM products WHERE active = 1 ORDER BY category COLLATE NOCASE").fetchall()
    offers_count = db.execute("SELECT COUNT(*) FROM products WHERE active = 1 AND old_price IS NOT NULL AND old_price > price").fetchone()[0]
    featured = db.execute("SELECT * FROM products WHERE active = 1 AND featured = 1 ORDER BY name COLLATE NOCASE LIMIT 4").fetchall()
    return render_template(
        "index.html", products=products, categories=categories, featured=featured,
        search=search, selected_category=category, only_offers=only_offers,
        offers_count=offers_count,
    )


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if session.get("admin_logged_in"):
        return redirect(url_for("admin_dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if hmac.compare_digest(username, ADMIN_USERNAME) and check_password_hash(ADMIN_PASSWORD_HASH, password):
            session.clear()
            session["admin_logged_in"] = True
            session["admin_username"] = username
            csrf_token()
            flash("Login realizado. Agora você manda nos preços, como deve ser.", "success")
            return redirect(url_for("admin_dashboard"))
        flash("Usuário ou senha incorretos.", "error")
    return render_template("login.html")


@app.post("/admin/logout")
@admin_required
def admin_logout():
    session.clear()
    flash("Você saiu da área administrativa.", "success")
    return redirect(url_for("index"))


@app.route("/admin")
@admin_required
def admin_dashboard():
    db = get_db()
    products = db.execute("SELECT * FROM products ORDER BY created_at DESC, name COLLATE NOCASE").fetchall()
    stats = {
        "total": db.execute("SELECT COUNT(*) FROM products").fetchone()[0],
        "active": db.execute("SELECT COUNT(*) FROM products WHERE active = 1").fetchone()[0],
        "offers": db.execute("SELECT COUNT(*) FROM products WHERE active = 1 AND old_price IS NOT NULL AND old_price > price").fetchone()[0],
    }
    return render_template("admin.html", products=products, stats=stats)


@app.route("/admin/produto/novo", methods=["GET", "POST"])
@admin_required
def product_new():
    if request.method == "POST":
        try:
            product = parse_product_form()
            db = get_db()
            db.execute(
                """INSERT INTO products (name, brand, category, description, price, old_price, unit,
                image_url, image_filename, featured, active)
                VALUES (:name, :brand, :category, :description, :price, :old_price, :unit,
                :image_url, :image_filename, :featured, :active)""", product,
            )
            db.commit()
            flash("Produto cadastrado com sucesso.", "success")
            return redirect(url_for("admin_dashboard"))
        except ValueError as exc:
            flash(str(exc), "error")
        except sqlite3.Error:
            flash("Não foi possível salvar o produto. Confira os dados e tente novamente.", "error")
    return render_template("product_form.html", product=None, page_title="Novo produto")


@app.route("/admin/produto/<int:product_id>/editar", methods=["GET", "POST"])
@admin_required
def product_edit(product_id: int):
    db = get_db()
    product = db.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    if product is None:
        abort(404)
    if request.method == "POST":
        try:
            values = parse_product_form(product)
            values["id"] = product_id
            db.execute(
                """UPDATE products SET name=:name, brand=:brand, category=:category, description=:description,
                price=:price, old_price=:old_price, unit=:unit, image_url=:image_url,
                image_filename=:image_filename, featured=:featured, active=:active WHERE id=:id""", values,
            )
            db.commit()
            flash("Produto atualizado.", "success")
            return redirect(url_for("admin_dashboard"))
        except ValueError as exc:
            flash(str(exc), "error")
        except sqlite3.Error:
            flash("Não foi possível atualizar o produto. Confira os dados e tente novamente.", "error")
    return render_template("product_form.html", product=product, page_title="Editar produto")


@app.post("/admin/produto/<int:product_id>/excluir")
@admin_required
def product_delete(product_id: int):
    db = get_db()
    product = db.execute("SELECT image_filename FROM products WHERE id = ?", (product_id,)).fetchone()
    if product:
        db.execute("DELETE FROM products WHERE id = ?", (product_id,))
        db.commit()
        remove_uploaded_image(product["image_filename"])
        flash("Produto removido do catálogo.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/configuracoes", methods=["GET", "POST"])
@admin_required
def admin_settings():
    db = get_db()
    if request.method == "POST":
        values = {
            "store_name": request.form.get("store_name", "").strip()[:70],
            "store_tagline": request.form.get("store_tagline", "").strip()[:120],
            "store_notice": request.form.get("store_notice", "").strip()[:180],
        }
        if not values["store_name"]:
            flash("O nome do supermercado não pode ficar vazio.", "error")
        else:
            db.executemany(
                "INSERT INTO settings(key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                values.items(),
            )
            db.commit()
            flash("Identidade da loja atualizada.", "success")
            return redirect(url_for("admin_settings"))
    settings = {key: get_setting(key) for key in ("store_name", "store_tagline", "store_notice")}
    return render_template("settings.html", settings=settings)


@app.errorhandler(413)
def file_too_large(_error):
    flash("A imagem é muito grande. O limite é 5 MB.", "error")
    return redirect(request.referrer or url_for("admin_dashboard"))


@app.errorhandler(400)
def bad_request(error):
    return render_template("error.html", code=400, message=getattr(error, "description", "Solicitação inválida.")), 400


@app.errorhandler(404)
def not_found(_error):
    return render_template("error.html", code=404, message="Esta página não foi encontrada."), 404


init_db()

if __name__ == "__main__":
    # Local-only by default. Set HOST=0.0.0.0 only when intentionally exposing it.
    app.run(host=os.getenv("HOST", "127.0.0.1"), port=int(os.getenv("PORT", "5000")), debug=False)
