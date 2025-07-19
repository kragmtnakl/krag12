from flask import Flask, request, jsonify, redirect, render_template_string
from datetime import datetime, timedelta
import os

app = Flask(__name__)

ip_log = {}
blocked_ips = {}
city_block_log = {}
visitor_behavior = []

dashboard_template = """
<!DOCTYPE html>
<html lang="ar">
<head>
    <meta charset="UTF-8">
    <title>لوحة مراقبة Google Ads</title>
</head>
<body>
    <h2>🛡️ لوحة مراقبة Google Ads</h2>
    <h3>📋 IPs المحظورة:</h3>
    <ul>
        {% for ip, until in blocked_ips.items() %}
            <li>{{ ip }} - حتى {{ until }}</li>
        {% endfor %}
    </ul>
    <h3>🏙️ المدن المحظورة:</h3>
    <ul>
        {% for city, until in city_block_log.items() %}
            <li>{{ city }} - حتى {{ until }}</li>
        {% endfor %}
    </ul>
    <h3>👤 سلوك الزوار المشبوه:</h3>
    <ul>
        {% for entry in visitor_behavior %}
            <li>{{ entry }}</li>
        {% endfor %}
    </ul>
</body>
</html>
"""

@app.route('/')
def dashboard():
    return render_template_string(dashboard_template,
                                  blocked_ips=blocked_ips,
                                  city_block_log=city_block_log,
                                  visitor_behavior=visitor_behavior)

@app.route('/track', methods=['POST'])
def track():
    data = request.json
    ip = request.remote_addr
    user_agent = request.headers.get('User-Agent')
    city = data.get('city', 'unknown')
    action = data.get('action', 'unknown')
    stay_time = data.get('stay', 0)
    contacted = data.get('contacted', False)
    now = datetime.now()

    # إزالة الحظر المنتهي
    for ip_banned in list(blocked_ips.keys()):
        if now > blocked_ips[ip_banned]:
            del blocked_ips[ip_banned]

    for city_name in list(city_block_log.keys()):
        if now > city_block_log[city_name]:
            del city_block_log[city_name]

    # تحقق من الحظر الحالي
    if city in city_block_log:
        return jsonify({'status': 'blocked_city'}), 403

    if ip in blocked_ips:
        return jsonify({'status': 'blocked_ip'}), 403

    # سجل النقرات
    if ip not in ip_log:
        ip_log[ip] = []
    ip_log[ip].append(now)

    # التحقق من عدد النقرات خلال دقيقة
    recent_clicks = [t for t in ip_log[ip] if now - t < timedelta(minutes=1)]
    ip_log[ip] = recent_clicks

    if len(recent_clicks) >= 2:
        blocked_ips[ip] = now + timedelta(minutes=15)
        return jsonify({'status': 'ip_blocked'}), 403

    # التحقق من عدد النقرات من المدينة خلال دقيقتين
    city_clicks = [t for t in ip_log[ip] if now - t < timedelta(minutes=2)]
    if len(city_clicks) >= 5:
        city_block_log[city] = now + timedelta(minutes=15)

    # تسجيل سلوك مريب
    if not contacted or stay_time < 5:
        visitor_behavior.append(f"زائر مريب IP: {ip} - الجهاز: {user_agent} - الوقت: {now.strftime('%Y-%m-%d %H:%M:%S')}")

    # إعادة التوجيه للموقع الأصلي
    return redirect("https://sites.google.com/view/fouadabdoshop", code=302)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
