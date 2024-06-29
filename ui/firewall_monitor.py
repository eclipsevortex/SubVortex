import sys
import json
import signal
from flask import Flask, render_template, jsonify

from subnet.firewall.firewall_factory import create_firewall_tool

app = Flask(__name__)


# Route to serve the main page
@app.route("/")
def index():
    return render_template("firewall-monitor.html")


# Route to fetch the events
@app.route("/events")
def get_events():
    events = []
    with open("events.log", "r") as file:
        for line in file:
            events.append(json.loads(line))
    return jsonify(events)


# Function to handle cleanup
def cleanup():
    print("Cleaning up...")
    tool = create_firewall_tool()
    success = tool.remove_rule(dport=8080, protocol="tcp", allow=True)
    print(f"Rule removed ? {success}")


def signal_handler(sig, frame):
    cleanup()
    sys.exit(0)


if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)   # Handle Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Handle `pm2 stop` and `pm2 delete`

    try:
        tool = create_firewall_tool()

        # Create an ALLOW rule
        tool.create_allow_rule(dport=8080, protocol="tcp")

        app.run(host="0.0.0.0", port=8080)
    finally:
        cleanup()
