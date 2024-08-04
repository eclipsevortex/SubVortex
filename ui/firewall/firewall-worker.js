let EVENT_SOURCE_URL;
let source;
let eventQueue = [];

const batchInterval = 500;

self.onmessage = function(event) {
    EVENT_SOURCE_URL = event.data;
    initializeEventSource();
};

function initializeEventSource() {
    source = new EventSource(`${EVENT_SOURCE_URL}/firewall`);

    source.onopen = function(event) {
        postMessage({ type: 'status', status: 'open' });
    };

    source.onerror = function(event) {
        postMessage({ type: 'status', status: 'error' });
        source.close();
        setTimeout(() => {
            initializeEventSource();
        }, 1000);
    };

    source.onmessage = function(event) {
        let data = JSON.parse(event.data);
        if (data.type == 'ping') {
            return
        }

        if (data.type == 'log' && Array.isArray(data.data)) {
            data.data.forEach(x => self.postMessage({ type: 'events', data: { "type": data.type, "data": x } }))
            return
        }

        self.postMessage({ type: 'events', data: data });
    };

    setInterval(processEventQueue, batchInterval);
}

function processEventQueue() {
    if (eventQueue.length > 0) {
        self.postMessage({ type: 'events', data: eventQueue });
        eventQueue = [];
    }
}