"""
encounter.bio — Flask app
Static-by-design report site with email-gated access for retrospective reports
and contact-form for prospective reports.
"""
import os
import csv
import json
import secrets
import smtplib
from datetime import datetime, timedelta
from email.message import EmailMessage
from pathlib import Path

from flask import (
    Flask, render_template, request, jsonify, redirect,
    url_for, abort, make_response,
)

# ────────────────────────────────────────────────────────────────────
# Config
# ────────────────────────────────────────────────────────────────────
APP_ROOT = Path(__file__).parent
DATA_DIR = APP_ROOT / "data"
LEADS_RETRO = DATA_DIR / "leads_retro.csv"
LEADS_PROSPECTIVE = DATA_DIR / "leads_prospective.csv"
REPORTS_JSON = DATA_DIR / "reports.json"

COOKIE_NAME = "encounter_member"
COOKIE_DAYS = 90

# Free email providers — block at the form level
FREE_EMAIL_DOMAINS = {
    "gmail.com", "googlemail.com", "outlook.com", "hotmail.com",
    "live.com", "msn.com", "yahoo.com", "yahoo.co.uk", "ymail.com",
    "rocketmail.com", "icloud.com", "me.com", "mac.com",
    "aol.com", "protonmail.com", "proton.me", "pm.me",
    "tutanota.com", "tuta.io", "fastmail.com", "fastmail.fm",
    "gmx.com", "gmx.net", "gmx.de", "mail.com", "zoho.com",
    "yandex.com", "yandex.ru", "qq.com", "163.com", "126.com",
    "naver.com", "daum.net", "hanmail.net",
}

# SMTP for notification emails (configure via Render env vars)
SMTP_HOST = os.environ.get("SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
SMTP_FROM = os.environ.get("SMTP_FROM", "hello@encounter.bio")
NOTIFY_TO = os.environ.get("NOTIFY_TO", "raimo@encounter.bio")

# Google Analytics 4 measurement ID (e.g. G-XXXXXXXXXX). Empty = no tracking.
GA_MEASUREMENT_ID = os.environ.get("GA_MEASUREMENT_ID", "")

app = Flask(__name__)


@app.context_processor
def inject_globals():
    """Make GA_MEASUREMENT_ID available to all templates as ga_measurement_id."""
    return {"ga_measurement_id": GA_MEASUREMENT_ID}


# ────────────────────────────────────────────────────────────────────
# Helpers
# ────────────────────────────────────────────────────────────────────
def load_reports():
    """Load report metadata from data/reports.json."""
    with open(REPORTS_JSON) as f:
        reports = json.load(f)
    # Sort newest first
    reports.sort(key=lambda r: r.get("date", ""), reverse=True)
    return reports


def get_report(slug):
    """Look up a single report by slug. Returns None if not found."""
    for r in load_reports():
        if r["slug"] == slug:
            return r
    return None


def is_free_email(email):
    """Check if email belongs to a free email provider."""
    if "@" not in email:
        return True
    domain = email.split("@", 1)[1].strip().lower()
    return domain in FREE_EMAIL_DOMAINS


def is_member(req):
    """Check if request has the member cookie set."""
    return req.cookies.get(COOKIE_NAME) == "1"


def append_csv(path, row, fieldnames):
    """Append a row to a CSV file, creating it with headers if missing."""
    path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = path.exists()
    with open(path, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)


def send_notification(subject, body):
    """Email Raimo about a new lead. Silent on failure."""
    if not SMTP_HOST or not SMTP_USER:
        # No SMTP configured — just print to logs
        print(f"[notification] {subject}\n{body}")
        return
    try:
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = SMTP_FROM
        msg["To"] = NOTIFY_TO
        msg.set_content(body)
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
            s.starttls()
            s.login(SMTP_USER, SMTP_PASS)
            s.send_message(msg)
    except Exception as e:
        print(f"[notification failed] {e}")


# ────────────────────────────────────────────────────────────────────
# Routes
# ────────────────────────────────────────────────────────────────────
@app.route("/")
def home():
    reports = load_reports()
    return render_template(
        "index.html",
        reports=reports,
        is_member=is_member(request),
    )


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact")
def contact():
    return render_template("contact.html")


@app.route("/service")
def service():
    return render_template("service.html")


@app.route("/reports/<slug>")
def report(slug):
    rep = get_report(slug)
    if rep is None:
        abort(404)
    template_name = f"reports/{slug}.html"
    unlocked = is_member(request) if rep["type"] == "retrospective" else False
    return render_template(
        template_name,
        report=rep,
        unlocked=unlocked,
        is_member=is_member(request),
    )


@app.route("/unlock-retro", methods=["POST"])
def unlock_retro():
    """Process the email-gate form on retrospective report cards."""
    email = (request.form.get("email") or "").strip().lower()
    name = (request.form.get("name") or "").strip()
    org = (request.form.get("organization") or "").strip()
    purpose = (request.form.get("purpose") or "").strip()
    slug = (request.form.get("slug") or "").strip()

    # Validation
    if not email or "@" not in email:
        return render_template(
            "form_error.html",
            error="Please enter a valid email address.",
            slug=slug,
        ), 400
    if is_free_email(email):
        return render_template(
            "form_error.html",
            error=(
                "Encounter requires a work email address. "
                "If you don't have one, please email us directly at hello@encounter.bio."
            ),
            slug=slug,
        ), 400
    if not name or not org:
        return render_template(
            "form_error.html",
            error="Please fill in your name and organization.",
            slug=slug,
        ), 400

    # Record the lead
    append_csv(
        LEADS_RETRO,
        {
            "timestamp": datetime.utcnow().isoformat(),
            "email": email,
            "name": name,
            "organization": org,
            "purpose": purpose,
            "slug": slug,
        },
        fieldnames=["timestamp", "email", "name", "organization", "purpose", "slug"],
    )

    # Notify
    send_notification(
        subject=f"[encounter] new retro reader: {name} ({org})",
        body=(
            f"New retrospective report unlock\n\n"
            f"Name: {name}\n"
            f"Email: {email}\n"
            f"Organization: {org}\n"
            f"Working on: {purpose or '(not provided)'}\n"
            f"Report: {slug}\n"
            f"Time: {datetime.utcnow().isoformat()} UTC\n"
        ),
    )

    # Set cookie and redirect back to the report
    target = url_for("report", slug=slug) if slug else url_for("home")
    resp = make_response(redirect(target))
    resp.set_cookie(
        COOKIE_NAME,
        "1",
        max_age=COOKIE_DAYS * 24 * 3600,
        httponly=False,  # we read this client-side too if needed
        samesite="Lax",
        secure=request.is_secure,
    )
    return resp


@app.route("/lead-prospective", methods=["POST"])
def lead_prospective():
    """Process the contact form on prospective report cards."""
    email = (request.form.get("email") or "").strip().lower()
    name = (request.form.get("name") or "").strip()
    org = (request.form.get("organization") or "").strip()
    role = (request.form.get("role") or "").strip()
    notes = (request.form.get("notes") or "").strip()
    slug = (request.form.get("slug") or "").strip()

    # Validation — same blocklist for prospective leads, no exceptions
    if not email or "@" not in email:
        return render_template(
            "form_error.html",
            error="Please enter a valid email address.",
            slug=slug,
        ), 400
    if is_free_email(email):
        return render_template(
            "form_error.html",
            error=(
                "Encounter requires a work email address for prospective report requests. "
                "Please use your organization's email or contact us directly at hello@encounter.bio."
            ),
            slug=slug,
        ), 400
    if not name or not org or not role:
        return render_template(
            "form_error.html",
            error="Please fill in your name, organization, and role.",
            slug=slug,
        ), 400

    # Record
    append_csv(
        LEADS_PROSPECTIVE,
        {
            "timestamp": datetime.utcnow().isoformat(),
            "email": email,
            "name": name,
            "organization": org,
            "role": role,
            "notes": notes,
            "slug": slug,
        },
        fieldnames=["timestamp", "email", "name", "organization", "role", "notes", "slug"],
    )

    # Notify (high-priority — these are real prospects)
    send_notification(
        subject=f"[encounter PROSPECTIVE] {name} at {org} — {slug}",
        body=(
            f"PROSPECTIVE REPORT REQUEST\n\n"
            f"Name: {name}\n"
            f"Role: {role}\n"
            f"Email: {email}\n"
            f"Organization: {org}\n"
            f"Report: {slug}\n\n"
            f"What they're working on:\n{notes or '(not provided)'}\n\n"
            f"Time: {datetime.utcnow().isoformat()} UTC\n\n"
            f"Action: reply within 2 business days. Open with the price-discovery question.\n"
        ),
    )

    return render_template("lead_thanks.html", name=name)


@app.route("/request-structural-read", methods=["POST"])
def request_structural_read():
    """Process the structured trial brief form on the /service page."""
    email = (request.form.get("email") or "").strip().lower()
    name = (request.form.get("name") or "").strip()
    org = (request.form.get("organization") or "").strip()
    role = (request.form.get("role") or "").strip()
    tier = (request.form.get("tier") or "").strip()
    indication = (request.form.get("indication") or "").strip()
    drug_class = (request.form.get("drug_class") or "").strip()
    trial_phase = (request.form.get("trial_phase") or "").strip()
    design_stage = (request.form.get("design_stage") or "").strip()
    nct = (request.form.get("nct") or "").strip()
    question = (request.form.get("question") or "").strip()
    timeline = (request.form.get("timeline") or "").strip()
    referral = (request.form.get("referral") or "").strip()

    # Validation
    if not email or "@" not in email:
        return render_template(
            "form_error.html",
            error="Please enter a valid email address.",
            back_url=url_for("service"),
        ), 400
    if is_free_email(email):
        return render_template(
            "form_error.html",
            error=(
                "Encounter requires a work email address for proposal requests. "
                "Please use your organization's email or contact us directly at hello@encounter.bio."
            ),
            back_url=url_for("service"),
        ), 400
    if not name or not org or not role:
        return render_template(
            "form_error.html",
            error="Please fill in your name, organization, and role.",
            back_url=url_for("service"),
        ), 400
    if not indication or not drug_class or not trial_phase or not design_stage:
        return render_template(
            "form_error.html",
            error="Please complete the trial details (indication, drug class, phase, stage of design).",
            back_url=url_for("service"),
        ), 400
    if not tier:
        return render_template(
            "form_error.html",
            error="Please select which tier you're interested in (Structural call or Structural read).",
            back_url=url_for("service"),
        ), 400
    if not question or not timeline:
        return render_template(
            "form_error.html",
            error="Please tell us what question you want answered and your timeline.",
            back_url=url_for("service"),
        ), 400

    # Record
    append_csv(
        LEADS_PROSPECTIVE,
        {
            "timestamp": datetime.utcnow().isoformat(),
            "email": email,
            "name": name,
            "organization": org,
            "role": role,
            "notes": (
                f"TIER: {tier} | "
                f"INDICATION: {indication} | DRUG CLASS: {drug_class} | "
                f"PHASE: {trial_phase} | STAGE: {design_stage} | NCT: {nct or 'n/a'} | "
                f"QUESTION: {question} | TIMELINE: {timeline} | REFERRAL: {referral or 'n/a'}"
            ),
            "slug": "structural-read-request",
        },
        fieldnames=["timestamp", "email", "name", "organization", "role", "notes", "slug"],
    )

    # Notify — this is a real proposal request, highest priority
    # Subject prefix shows tier so Tier 2 requests are visually obvious in inbox
    tier_short = "T1" if tier.startswith("Tier 1") else ("T2" if tier.startswith("Tier 2") else "??")
    send_notification(
        subject=f"[encounter PROPOSAL · {tier_short}] {name} at {org} — {indication}",
        body=(
            f"STRUCTURAL READ PROPOSAL REQUEST\n\n"
            f"Tier requested: {tier}\n\n"
            f"From: {name} ({role})\n"
            f"Email: {email}\n"
            f"Organization: {org}\n\n"
            f"--- TRIAL ---\n"
            f"Indication:    {indication}\n"
            f"Drug class:    {drug_class}\n"
            f"Trial phase:   {trial_phase}\n"
            f"Design stage:  {design_stage}\n"
            f"NCT:           {nct or '(not provided)'}\n\n"
            f"--- THE QUESTION ---\n"
            f"{question}\n\n"
            f"--- TIMELINE ---\n"
            f"{timeline}\n\n"
            f"--- HOW THEY HEARD ---\n"
            f"{referral or '(not provided)'}\n\n"
            f"Time: {datetime.utcnow().isoformat()} UTC\n\n"
            f"Action: reply within 2 business days with scope and fixed-fee proposal.\n"
        ),
    )

    return render_template("lead_thanks.html", name=name, is_proposal=True)


@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


# ────────────────────────────────────────────────────────────────────
# Entry point
# ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
