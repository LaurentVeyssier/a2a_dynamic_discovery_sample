// frontend/main.js - Chat logic and SSE listener for event visualization.
document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatMessages = document.getElementById('chat-messages');
    const flowTimeline = document.getElementById('flow-timeline');
    const clearFlowBtn = document.getElementById('clear-flow');
    const sseStatus = document.getElementById('sse-status');
    const paStatus = document.getElementById('pa-status');

    let isFirstEvent = true;
    let eventList = [];

    // --- SSE Setup ---
    function setupSSE() {
        const eventSource = new EventSource('/api/events');

        eventSource.onopen = () => {
            sseStatus.classList.add('active');
            console.log('SSE connection opened');
        };

        eventSource.onmessage = (event) => {
            const data = JSON.parse(event.data);
            handleAgentEvent(data);
        };

        eventSource.onerror = (err) => {
            sseStatus.classList.remove('active');
            console.error('SSE error:', err);
            eventSource.close();
            // Retry after 3 seconds
            setTimeout(setupSSE, 3000);
        };
    }

    function handleAgentEvent(event) {
        if (isFirstEvent) {
            flowTimeline.innerHTML = '';
            isFirstEvent = false;
        }

        // Add to list if not already present (based on sequence)
        if (!eventList.some(e => e.sequence === event.sequence)) {
            eventList.push(event);
            // Sort by sequence descending (newest first for timeline)
            eventList.sort((a, b) => b.sequence - a.sequence);
            renderTimeline();
        }
    }

    function renderTimeline() {
        flowTimeline.innerHTML = '';
        eventList.forEach(event => {
            const item = document.createElement('div');
            item.className = `flow-item ${event.type}`;

            let icon = 'fa-info-circle';
            if (event.type === 'discovery') icon = 'fa-search';
            if (event.type === 'handshake') icon = 'fa-handshake';
            if (event.type === 'call') icon = 'fa-arrow-right';

            const time = new Date(event.timestamp * 1000).toLocaleTimeString();

            let context = '';
            if (event.type === 'discovery') {
                context = `<span class="initiator">${event.initiator}</span> searching <span class="target">${event.target}</span>`;
            } else {
                context = `<span class="initiator">${event.initiator}</span> <i class="fas fa-long-arrow-alt-right"></i> <span class="target">${event.target}</span>`;
            }

            item.innerHTML = `
                <div class="type">
                    <i class="fas ${icon}"></i>
                    ${event.type.toUpperCase()} • ${time} • #${event.sequence}
                </div>
                <div class="agent">${context}</div>
                <div class="details">${formatDetails(event)}</div>
            `;
            flowTimeline.appendChild(item);
        });
    }

    function formatDetails(event) {
        if (event.type === 'discovery') {
            return `Searching for: "${event.details.query}"<br>Found: ${event.details.results.join(', ') || 'None'}`;
        }
        if (event.type === 'handshake') {
            return `Status: ${event.details.status}`;
        }
        if (event.type === 'call') {
            return `Payload: ${event.details.payload.substring(0, 100)}${event.details.payload.length > 100 ? '...' : ''}`;
        }
        return JSON.stringify(event.details);
    }

    // --- Chat Setup ---
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const message = userInput.value.trim();
        if (!message) return;

        addMessage(message, 'user');
        userInput.value = '';

        // Show typing indicator or state
        const typingIndicator = addMessage('...', 'assistant');

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message })
            });

            const data = await response.json();
            typingIndicator.remove();

            if (data.response) {
                addMessage(data.response, 'assistant');
            } else if (data.error) {
                addMessage(`Error: ${data.error}`, 'assistant');
            }
        } catch (err) {
            typingIndicator.remove();
            addMessage(`Connection error: ${err.message}`, 'assistant');
        }
    });

    function addMessage(text, role) {
        const msgDiv = document.createElement('div');
        msgDiv.className = `message ${role}`;
        msgDiv.innerHTML = `<div class="message-bubble">${text}</div>`;
        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
        return msgDiv;
    }

    // --- UI Helpers ---
    clearFlowBtn.addEventListener('click', () => {
        flowTimeline.innerHTML = '<div class="empty-state"><i class="fas fa-satellite-dish"></i><p>Waiting for agent activity...</p></div>';
        isFirstEvent = true;
        eventList = [];
    });

    // Check PA Agent status
    async function checkPAStatus() {
        try {
            const res = await fetch('/api/health');
            if (res.ok) paStatus.classList.add('active');
            else paStatus.classList.remove('active');
        } catch {
            paStatus.classList.remove('active');
        }
    }

    setupSSE();
    checkPAStatus();
    setInterval(checkPAStatus, 10000);
});
