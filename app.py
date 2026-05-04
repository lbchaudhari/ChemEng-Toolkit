"""Flask app for ChemEng Toolkit."""
from __future__ import annotations
import os
import traceback
from flask import Flask, jsonify, render_template, request, abort, send_file

import chatbot
import report
from registry import CALCULATORS, grouped

app = Flask(__name__)


def _nav_context(active=None):
    return {"groups": grouped(), "active": active}


@app.route("/")
def home():
    return render_template("home.html", **_nav_context("home"))


@app.route("/calc/<calc_id>")
def calculator(calc_id):
    spec = CALCULATORS.get(calc_id)
    if not spec:
        abort(404)
    return render_template(
        "calculator.html",
        calc_id=calc_id,
        spec=spec,
        **_nav_context(calc_id),
    )


@app.post("/api/calc/<calc_id>")
def api_calc(calc_id):
    spec = CALCULATORS.get(calc_id)
    if not spec:
        return jsonify({"error": "Unknown calculator."}), 404
    payload = request.get_json(silent=True) or {}
    try:
        result = spec["compute"](payload)
        result.setdefault("results", [])
        result.setdefault("notes", [])
        return jsonify(result)
    except (ValueError, KeyError, TypeError) as e:
        return jsonify({"error": str(e)}), 400
    except Exception:
        traceback.print_exc()
        return jsonify({"error": "Internal error during calculation."}), 500


@app.post("/api/report/<calc_id>")
def api_report(calc_id):
    """Run the calculation and return a PDF report."""
    spec = CALCULATORS.get(calc_id)
    if not spec:
        return jsonify({"error": "Unknown calculator."}), 404
    payload = request.get_json(silent=True) or {}
    try:
        result = spec["compute"](payload)
    except (ValueError, KeyError, TypeError) as e:
        return jsonify({"error": str(e)}), 400
    except Exception:
        traceback.print_exc()
        return jsonify({"error": "Internal error during calculation."}), 500

    pdf_bytes = report.build_pdf(
        spec=spec,
        calc_id=calc_id,
        inputs=payload,
        results=result.get("results", []),
        notes=result.get("notes", []),
        datasheet=result.get("datasheet", []),
    )
    return send_file(
        _bytes_io(pdf_bytes),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=f"chemeng_{calc_id}_report.pdf",
    )


def _bytes_io(b):
    import io
    return io.BytesIO(b)


@app.route("/reports")
def reports_page():
    return render_template("reports.html", **_nav_context("reports"))


@app.route("/chatbot")
def chatbot_page():
    return render_template("chatbot.html", **_nav_context("chatbot"))


@app.post("/api/chat")
def api_chat():
    payload = request.get_json(silent=True) or {}
    msg = (payload.get("message") or "").strip()
    if not msg:
        return jsonify({"reply": "Ask me about a chemical engineering formula or calculation."})
    return jsonify(chatbot.answer(msg))


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5001"))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
