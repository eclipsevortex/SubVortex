const http = require('http');
const fs = require('fs');
const WebSocket = require('ws');
const path = require('path');

const server = http.createServer((req, res) => {
    if (req.url === '/') {
        fs.readFile(path.join(__dirname, 'firewall-monitor.html'), (err, data) => {
            if (err) {
                res.writeHead(500);
                res.end('Error loading HTML file');
            } else {
                res.writeHead(200, { 'Content-Type': 'text/html' });
                res.end(data);
            }
        });
    } else {
        res.writeHead(404);
        res.end();
    }
});

const wss = new WebSocket.Server({ server });

wss.on('connection', (ws) => {
    console.log('Client connected');
    ws.send(JSON.stringify({
        timestamp: Math.floor(Date.now() / 1000),
        action: 'connected',
        ip: '127.0.0.1',
        port: '8080',
        reason: 'Client connected successfully'
    }));

    ws.on('message', (message) => {
        console.log('received: %s', message);
    });

    ws.on('close', () => {
        console.log('Client disconnected');
    });
});

server.listen(8080, () => {
    console.log('Server is listening on port 8080');
});
