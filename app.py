from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import os

app = Flask(__name__)
ip_log = {}
blocked_ips = {}
city_block_log = {}

@app.route('/')
def home():
    return "📡 حماية Google Ads فعالة"

@app.route('/track', methods=['POST'])
def track():
    data = request.json
    ip = request.remote_addr
    user_agent = request.headers.get('User-Agent')
    city = data.get('city', 'unknown')
    action = data.get('action', 'unknown')
    now = datetime.now()

    for ip_banned in list(blocked_ips.keys()):
        if now > blocked_ips[ip_banned]:
            del blocked_ips[ip_banned]

    if city in city_block_log and city_block_log[city] > now:
        return jsonify({'status': 'blocked_city', 'message': 'تم حظر المدينة مؤقتًا'}), 403

    if ip in blocked_ips:
        return jsonify({'status': 'blocked', 'message': 'IP محظور مؤقتًا'}), 403

    if ip not in ip_log:
        ip_log[ip] = []

    ip_log[ip].append(now)

    recent = [t for t in ip_log[ip] if now - t < timedelta(minutes=2)]
    ip_log[ip] = recent

    if len(recent) >= 3:
        blocked_ips[ip] = now + timedelta(minutes=4)
        return jsonify({'status': 'paused', 'message': 'تم إيقاف الإعلان مؤقتًا'}), 403

    city_clicks = [t for t in ip_log[ip] if now - t < timedelta(minutes=2)]
    if len(city_clicks) >= 5:
        city_block_log[city] = now + timedelta(minutes=30)

    return jsonify({
        'status': 'ok',
        'ip': ip,
        'city': city,
        'action': action,
        'device': user_agent,
        'time': now.strftime("%Y-%m-%d %H:%M:%S")
    })

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
