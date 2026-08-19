from flask import Flask, request, jsonify, render_template_string
import discord
from discord.ext import commands
import asyncio
import threading
from datetime import datetime, timedelta
import os
import requests

app = Flask(__name__)

# المتغيرات العامة
client = None
afk_active = False
start_time = None
voice_client = None
current_channel = None
current_guild = None

# HTML الواجهة
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Discord AFK Tool</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .container {
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            max-width: 500px;
            width: 100%;
            padding: 40px;
        }
        
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .header h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 28px;
        }
        
        .header p {
            color: #666;
            font-size: 14px;
        }
        
        .input-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            color: #333;
            font-weight: 600;
            font-size: 14px;
        }
        
        input {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        
        input:focus {
            outline: none;
            border-color: #667eea;
            background-color: #f8f9ff;
        }
        
        .user-info {
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            margin-top: 30px;
            display: none;
        }
        
        .user-info.show {
            display: block;
        }
        
        .user-header {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .user-avatar {
            width: 80px;
            height: 80px;
            border-radius: 50%;
            background: #667eea;
            object-fit: cover;
            border: 3px solid #667eea;
        }
        
        .user-details h2 {
            color: #333;
            font-size: 18px;
            margin-bottom: 5px;
        }
        
        .user-details p {
            color: #666;
            font-size: 13px;
            margin-bottom: 3px;
        }
        
        .user-id {
            background: white;
            padding: 10px;
            border-radius: 5px;
            font-size: 12px;
            color: #667eea;
            word-break: break-all;
            margin-top: 10px;
            font-family: 'Courier New', monospace;
        }
        
        button {
            width: 100%;
            padding: 12px;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            margin-top: 10px;
        }
        
        .btn-login {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .btn-login:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(102, 126, 234, 0.4);
        }
        
        .btn-login:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .btn-start {
            background: #10b981;
            color: white;
        }
        
        .btn-start:hover {
            background: #059669;
            transform: translateY(-2px);
            box-shadow: 0 10px 25px rgba(16, 185, 129, 0.4);
        }
        
        .btn-logout {
            background: #ef4444;
            color: white;
        }
        
        .btn-logout:hover {
            background: #dc2626;
        }
        
        .status {
            margin-top: 15px;
            padding: 12px;
            border-radius: 8px;
            text-align: center;
            display: none;
            font-size: 14px;
        }
        
        .status.show {
            display: block;
        }
        
        .status.success {
            background: #dcfce7;
            color: #166534;
            border-left: 4px solid #10b981;
        }
        
        .status.error {
            background: #fee2e2;
            color: #991b1b;
            border-left: 4px solid #ef4444;
        }
        
        .status.loading {
            background: #dbeafe;
            color: #1e40af;
            border-left: 4px solid #3b82f6;
        }
        
        .spinner {
            display: inline-block;
            width: 14px;
            height: 14px;
            border: 2px solid transparent;
            border-top-color: currentColor;
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
            margin-right: 8px;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .timer {
            font-size: 12px;
            color: #666;
            margin-top: 10px;
        }
        
        .warning {
            background: #fef3c7;
            border-left: 4px solid #f59e0b;
            color: #92400e;
            padding: 12px;
            border-radius: 5px;
            margin-bottom: 20px;
            font-size: 12px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎮 Discord AFK</h1>
            <p>خليك AFK في الفويس لمدة 24 ساعة</p>
        </div>
        
        <div class="warning">
            ⚠️ تحذير: استخدام Self-Bot قد يؤدي لحظر حسابك!
        </div>
        
        <div id="loginForm">
            <div class="input-group">
                <label for="token">User Token:</label>
                <input type="password" id="token" placeholder="أدخل توكنك هنا">
            </div>
            
            <div class="input-group">
                <label for="serverId">Server ID:</label>
                <input type="text" id="serverId" placeholder="أدخل رقم السيرفر">
            </div>
            
            <div class="input-group">
                <label for="voiceId">Voice Channel ID:</label>
                <input type="text" id="voiceId" placeholder="أدخل رقم روم الفويس">
            </div>
            
            <button class="btn-login" onclick="login()">تحقق من البيانات</button>
            <div id="status" class="status"></div>
        </div>
        
        <div id="userSection" class="user-info">
            <div class="user-header">
                <img id="userAvatar" class="user-avatar" src="" alt="Profile">
                <div class="user-details">
                    <h2 id="userName"></h2>
                    <p>الحالة: <span id="userStatus"></span></p>
                    <div class="user-id">ID: <span id="userId"></span></div>
                </div>
            </div>
            
            <button class="btn-start" onclick="startAFK()">🚀 بدء الشتغيل</button>
            <button class="btn-logout" onclick="logout()">تسجيل خروج</button>
            
            <div id="afkStatus" class="timer"></div>
        </div>
    </div>

    <script>
        let currentToken = localStorage.getItem('discordToken');
        let currentServerId = localStorage.getItem('serverId');
        let currentVoiceId = localStorage.getItem('voiceId');
        let statusInterval = null;

        function showStatus(message, type = 'loading') {
            const status = document.getElementById('status');
            status.className = `status show ${type}`;
            
            if (type === 'loading') {
                status.innerHTML = `<span class="spinner"></span>${message}`;
            } else {
                status.textContent = message;
            }
        }

        async function login() {
            const token = document.getElementById('token').value;
            const serverId = document.getElementById('serverId').value;
            const voiceId = document.getElementById('voiceId').value;

            if (!token || !serverId || !voiceId) {
                showStatus('❌ الرجاء ملء جميع الحقول', 'error');
                return;
            }

            showStatus('جاري التحقق من البيانات...');

            try {
                const response = await fetch('/api/login', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        token: token,
                        server_id: serverId,
                        voice_id: voiceId
                    })
                });

                const data = await response.json();

                if (!response.ok) {
                    showStatus('❌ ' + data.error, 'error');
                    return;
                }

                currentToken = token;
                currentServerId = serverId;
                currentVoiceId = voiceId;

                localStorage.setItem('discordToken', token);
                localStorage.setItem('serverId', serverId);
                localStorage.setItem('voiceId', voiceId);

                displayUserInfo(data.user);
                showStatus('✅ تم التحقق بنجاح!', 'success');
                
                document.getElementById('loginForm').style.display = 'none';
                document.getElementById('userSection').classList.add('show');

            } catch (error) {
                showStatus('❌ خطأ: ' + error.message, 'error');
            }
        }

        function displayUserInfo(user) {
            document.getElementById('userName').textContent = user.username + '#' + user.discriminator;
            document.getElementById('userStatus').textContent = user.bot ? 'بوت 🤖' : 'مستخدم 👤';
            document.getElementById('userId').textContent = user.id;
            
            if (user.avatar) {
                document.getElementById('userAvatar').src = user.avatar;
            }
        }

        async function startAFK() {
            const btn = event.target;
            btn.disabled = true;
            btn.textContent = '⏳ جاري الاتصال...';

            try {
                const response = await fetch('/api/start_afk', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        token: currentToken,
                        server_id: currentServerId,
                        voice_id: currentVoiceId
                    })
                });

                const data = await response.json();

                if (!response.ok) {
                    btn.disabled = false;
                    btn.textContent = '🚀 بدء الشتغيل';
                    alert('❌ خطأ: ' + data.error);
                    return;
                }

                btn.textContent = '✅ جاري البث...';
                btn.disabled = true;
                
                // شغّل العداد
                startTimer();

            } catch (error) {
                btn.disabled = false;
                btn.textContent = '🚀 بدء الشتغيل';
                alert('❌ خطأ: ' + error.message);
            }
        }

        function startTimer() {
            const afkStatus = document.getElementById('afkStatus');
            const startTime = Date.now();
            
            afkStatus.innerHTML = '⏱️ وقت البث: 0 ثانية';
            
            if (statusInterval) clearInterval(statusInterval);
            
            statusInterval = setInterval(async () => {
                const elapsed = Math.floor((Date.now() - startTime) / 1000);
                const hours = Math.floor(elapsed / 3600);
                const minutes = Math.floor((elapsed % 3600) / 60);
                const secs = elapsed % 60;
                
                afkStatus.innerHTML = `✅ البث نشط: ${hours}س ${minutes}د ${secs}ث<br>سيتوقف تلقائياً بعد 24 ساعة`;
                
                // تحقق من الحالة كل دقيقة
                if (elapsed % 60 === 0) {
                    try {
                        const res = await fetch('/api/status');
                        const status = await res.json();
                        if (!status.active) {
                            clearInterval(statusInterval);
                            afkStatus.innerHTML = '⏰ انتهى وقت البث (24 ساعة)';
                        }
                    } catch (e) {
                        console.log('خطأ في التحقق:', e);
                    }
                }
            }, 1000);
        }

        function logout() {
            if (statusInterval) clearInterval(statusInterval);
            
            fetch('/api/logout', { method: 'POST' });
            
            localStorage.removeItem('discordToken');
            localStorage.removeItem('serverId');
            localStorage.removeItem('voiceId');
            
            currentToken = null;
            currentServerId = null;
            currentVoiceId = null;
            
            document.getElementById('loginForm').style.display = 'block';
            document.getElementById('userSection').classList.remove('show');
            document.getElementById('status').classList.remove('show');
            document.getElementById('token').value = '';
            document.getElementById('serverId').value = '';
            document.getElementById('voiceId').value = '';
            document.getElementById('afkStatus').innerHTML = '';
        }

        // Load saved data if available
        if (currentToken && currentServerId && currentVoiceId) {
            document.getElementById('token').value = currentToken;
            document.getElementById('serverId').value = currentServerId;
            document.getElementById('voiceId').value = currentVoiceId;
            login();
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/login', methods=['POST'])
def api_login():
    global client
    
    data = request.json
    token = data.get('token')
    server_id = int(data.get('server_id'))
    voice_id = int(data.get('voice_id'))
    
    try:
        # تحقق من التوكن بطلب HTTP
        import requests
        headers = {'Authorization': token}
        response = requests.get('https://discord.com/api/v10/users/@me', headers=headers)
        
        if response.status_code != 200:
            return jsonify({'error': 'التوكن غير صحيح أو منتهي الصلاحية'}), 400
        
        user_data = response.json()
        
        # احفظ التوكن والـ IDs للاستخدام لاحقاً
        app.config['TOKEN'] = token
        app.config['SERVER_ID'] = server_id
        app.config['VOICE_ID'] = voice_id
        
        avatar_url = None
        if user_data.get('avatar'):
            avatar_url = f"https://cdn.discordapp.com/avatars/{user_data['id']}/{user_data['avatar']}.png"
        
        return jsonify({
            'success': True,
            'user': {
                'id': user_data['id'],
                'username': user_data['username'],
                'discriminator': user_data['discriminator'],
                'avatar': avatar_url,
                'bot': user_data.get('bot', False)
            }
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/start_afk', methods=['POST'])
def api_start_afk():
    global afk_active, voice_client
    
    data = request.json
    token = data.get('token')
    server_id = int(data.get('server_id'))
    voice_id = int(data.get('voice_id'))
    
    try:
        if afk_active:
            return jsonify({'error': 'البوت متصل بالفعل'}), 400
        
        # شغّل اتصال الفويس في thread منفصل
        def start_afk_thread():
            global afk_active, start_time, voice_client, current_channel, current_guild, client
            
            async def afk_task():
                global afk_active, start_time, voice_client, current_channel, current_guild
                
                try:
                    # أنشئ client جديد
                    intents = discord.Intents.default()
                    intents.voice_states = True
                    local_client = discord.Client(intents=intents)
                    
                    @local_client.event
                    async def on_ready():
                        try:
                            guild = local_client.get_guild(server_id)
                            if not guild:
                                print("❌ السيرفر غير موجود")
                                afk_active = False
                                return
                            
                            channel = guild.get_channel(voice_id)
                            if not isinstance(channel, discord.VoiceChannel):
                                print("❌ روم الفويس غير موجود")
                                afk_active = False
                                return
                            
                            try:
                                voice_client = await channel.connect()
                                afk_active = True
                                start_time = datetime.now()
                                current_channel = channel
                                current_guild = guild
                                print(f"✅ تم الدخول لروم الفويس: {channel.name}")
                                
                                # انتظر 24 ساعة
                                await asyncio.sleep(24 * 60 * 60)
                                
                                if voice_client:
                                    await voice_client.disconnect()
                                afk_active = False
                                await local_client.close()
                                print("✅ انتهت 24 ساعة")
                            
                            except Exception as e:
                                print(f"❌ خطأ في الاتصال: {e}")
                                afk_active = False
                                await local_client.close()
                        
                        except Exception as e:
                            print(f"❌ خطأ في on_ready: {e}")
                            afk_active = False
                    
                    # دخّل البوت
                    await local_client.start(token)
                
                except Exception as e:
                    print(f"❌ خطأ عام: {e}")
                    afk_active = False
            
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(afk_task())
        
        thread = threading.Thread(target=start_afk_thread, daemon=True)
        thread.start()
        
        return jsonify({'success': True, 'message': 'جاري الدخول للفويس...'})

@app.route('/api/status')
def api_status():
    global afk_active, start_time
    
    status = {
        'active': afk_active,
        'start_time': start_time.isoformat() if start_time else None
    }
    
    if afk_active and start_time:
        elapsed = (datetime.now() - start_time).total_seconds()
        remaining = (24 * 60 * 60) - elapsed
        status['elapsed'] = int(elapsed)
        status['remaining'] = int(remaining)
    
    return jsonify(status)

@app.route('/api/logout', methods=['POST'])
def api_logout():
    global afk_active, voice_client
    
    afk_active = False
    if voice_client:
        try:
            # محاولة قطع الاتصال
            if voice_client.is_connected():
                asyncio.create_task(voice_client.disconnect())
        except:
            pass
    
    return jsonify({'success': True, 'message': 'تم تسجيل الخروج'})

if __name__ == '__main__':
    print("""
╔════════════════════════════════════════════════════════╗
║  Discord AFK Web Tool
║  http://localhost:5000
╚════════════════════════════════════════════════════════╝
    """)
    app.run(debug=True, port=5000)
