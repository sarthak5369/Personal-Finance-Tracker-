import os
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from flask import Flask, flash, jsonify, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import func
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, current_user, login_user, logout_user, login_required

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-only-change-this-secret")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL",
    "mysql+pymysql://root:Sarthak_30@localhost/penny_pilot"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message_category = "info"


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    transactions = db.relationship("Transaction", backref="owner", lazy=True,
                                   cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    amount = db.Column(db.Numeric(12, 2), nullable=False)
    kind = db.Column(db.String(10), nullable=False)  # income or expense
    category = db.Column(db.String(60), nullable=False)
    transaction_date = db.Column(db.Date, nullable=False, default=date.today)
    note = db.Column(db.String(500), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def as_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "amount": float(self.amount),
            "type": self.kind,
            "category": self.category,
            "date": self.transaction_date.isoformat(),
            "note": self.note or "",
        }


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


def parse_transaction_form(form):
    title = form.get("title", "").strip()
    kind = form.get("kind", "").strip().lower()
    category = form.get("category", "").strip()
    raw_amount = form.get("amount", "").strip()
    raw_date = form.get("transaction_date", "").strip()
    note = form.get("note", "").strip()

    if not title or len(title) > 120:
        raise ValueError("Enter a title (up to 120 characters).")
    if kind not in {"income", "expense"}:
        raise ValueError("Choose income or expense.")
    if not category or len(category) > 60:
        raise ValueError("Enter a category (up to 60 characters).")
    try:
        amount = Decimal(raw_amount)
    except (InvalidOperation, TypeError):
        raise ValueError("Enter a valid amount.")
    if not amount.is_finite() or amount <= 0 or amount > Decimal("9999999999.99"):
        raise ValueError("Amount must be greater than zero and within the supported limit.")
    try:
        transaction_date = date.fromisoformat(raw_date) if raw_date else date.today()
    except ValueError:
        raise ValueError("Enter a valid date.")
    if len(note) > 500:
        raise ValueError("Notes must be 500 characters or fewer.")

    return {
        "title": title,
        "amount": amount,
        "kind": kind,
        "category": category,
        "transaction_date": transaction_date,
        "note": note or None,
    }


@app.route("/")
def index():
    if not current_user.is_authenticated:
        return render_template("landing.html")
    transactions = (Transaction.query.filter_by(user_id=current_user.id)
                    .order_by(Transaction.transaction_date.desc(), Transaction.id.desc())
                    .limit(8).all())
    income = db.session.query(func.coalesce(func.sum(Transaction.amount), 0)).filter_by(
        user_id=current_user.id, kind="income").scalar()
    expenses = db.session.query(func.coalesce(func.sum(Transaction.amount), 0)).filter_by(
        user_id=current_user.id, kind="expense").scalar()
    return render_template("dashboard.html", transactions=transactions,
                           income=income, expenses=expenses, balance=income - expenses)


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        if not name or len(name) > 100:
            flash("Enter your name (up to 100 characters).", "error")
        elif "@" not in email or len(email) > 150:
            flash("Enter a valid email address.", "error")
        elif len(password) < 8:
            flash("Password must contain at least 8 characters.", "error")
        elif User.query.filter_by(email=email).first():
            flash("An account with this email already exists.", "error")
        else:
            user = User(name=name, email=email)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Account created successfully.", "success")
            return redirect(url_for("index"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
            flash("Welcome back!", "success")
            return redirect(url_for("index"))
        flash("Invalid email or password.", "error")
    return render_template("login.html")


@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))


@app.route("/transactions")
@login_required
def transactions_page():
    kind = request.args.get("type", "").lower()
    query = Transaction.query.filter_by(user_id=current_user.id)
    if kind in {"income", "expense"}:
        query = query.filter_by(kind=kind)
    transactions = query.order_by(Transaction.transaction_date.desc(), Transaction.id.desc()).all()
    return render_template("transactions.html", transactions=transactions, selected_type=kind)


@app.route("/transactions/new", methods=["GET", "POST"])
@login_required
def new_transaction():
    if request.method == "POST":
        try:
            values = parse_transaction_form(request.form)
            transaction = Transaction(user_id=current_user.id, **values)
            db.session.add(transaction)
            db.session.commit()
            flash("Transaction added.", "success")
            return redirect(url_for("transactions_page"))
        except ValueError as exc:
            flash(str(exc), "error")
    return render_template("transaction_form.html", transaction=None, today=date.today().isoformat())


@app.route("/transactions/<int:transaction_id>/edit", methods=["GET", "POST"])
@login_required
def edit_transaction(transaction_id):
    transaction = Transaction.query.filter_by(id=transaction_id, user_id=current_user.id).first_or_404()
    if request.method == "POST":
        try:
            values = parse_transaction_form(request.form)
            for key, value in values.items():
                setattr(transaction, key, value)
            db.session.commit()
            flash("Transaction updated.", "success")
            return redirect(url_for("transactions_page"))
        except ValueError as exc:
            flash(str(exc), "error")
    return render_template("transaction_form.html", transaction=transaction,
                           today=date.today().isoformat())


@app.route("/transactions/<int:transaction_id>/delete", methods=["POST"])
@login_required
def delete_transaction(transaction_id):
    transaction = Transaction.query.filter_by(id=transaction_id, user_id=current_user.id).first_or_404()
    db.session.delete(transaction)
    db.session.commit()
    flash("Transaction deleted.", "success")
    return redirect(request.referrer or url_for("transactions_page"))


# JSON REST API: all transaction endpoints require a logged-in browser session.
@app.route("/api/transactions", methods=["GET", "POST"])
@login_required
def api_transactions():
    if request.method == "GET":
        query = Transaction.query.filter_by(user_id=current_user.id)
        kind = request.args.get("type", "").lower()
        if kind in {"income", "expense"}:
            query = query.filter_by(kind=kind)
        return jsonify([item.as_dict() for item in query.order_by(
            Transaction.transaction_date.desc(), Transaction.id.desc()).all()])

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Send a JSON object."}), 400
    try:
        values = parse_transaction_form(data)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    transaction = Transaction(user_id=current_user.id, **values)
    db.session.add(transaction)
    db.session.commit()
    return jsonify(transaction.as_dict()), 201


@app.route("/api/transactions/<int:transaction_id>", methods=["GET", "PUT", "DELETE"])
@login_required
def api_transaction_detail(transaction_id):
    transaction = Transaction.query.filter_by(
        id=transaction_id, user_id=current_user.id).first()
    if transaction is None:
        return jsonify({"error": "Transaction not found."}), 404
    if request.method == "GET":
        return jsonify(transaction.as_dict())
    if request.method == "DELETE":
        db.session.delete(transaction)
        db.session.commit()
        return jsonify({"message": "Transaction deleted."})
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"error": "Send a JSON object."}), 400
    try:
        values = parse_transaction_form(data)
    except ValueError as exc:
        return jsonify({"error": str(exc)}), 400
    for key, value in values.items():
        setattr(transaction, key, value)
    db.session.commit()
    return jsonify(transaction.as_dict())


@app.route("/api/summary")
@login_required
def api_summary():
    income = db.session.query(func.coalesce(func.sum(Transaction.amount), 0)).filter_by(
        user_id=current_user.id, kind="income").scalar()
    expenses = db.session.query(func.coalesce(func.sum(Transaction.amount), 0)).filter_by(
        user_id=current_user.id, kind="expense").scalar()
    return jsonify({"income": float(income), "expenses": float(expenses),
                    "balance": float(income - expenses)})


@app.route("/health")
def health():
    return jsonify({"status": "ok", "app": "Personal Finance Tracker"})


with app.app_context():
    db.create_all()


if __name__ == "__main__":
    app.run(debug=True)
