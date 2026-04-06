from flask import Flask, jsonify, render_template
from dotenv import load_dotenv
from services.security_onion import get_dashboard_data

load_dotenv()

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/health")
def health():
    return jsonify({"status": "ok"})


@app.route("/api/dashboard")
def dashboard():
    try:
        data = get_dashboard_data()
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "data": {
                "connected": False,
                "status": f"Error: {e}",
                "total_alerts": 0,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "timeline": [],
                "top_ips": [],
                "recent_alerts": [],
                "last_update": "-",
                "es_version": "-",
                "index_count": 0,
                "active_index_pattern": "-"
            }
        }), 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8050, debug=True)