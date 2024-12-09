let socket: WebSocket | null = null;

// Connect to WebSocket server
function connectWebSocket() {
  socket = new WebSocket('ws://localhost:8000/ws/browser-extension/browsers');
  
  socket.onopen = () => {
    console.log('Connected to Jarvis WebSocket');
    socket.send(JSON.stringify({
      sender: 'browser-extension',
      message_type: 'connect',
      content: {
        url: window.location.href,
        title: document.title
      }
    }));
  };
  
  socket.onmessage = (event) => {
    const message = JSON.parse(event.data);
    handleWebSocketMessage(message);
  };
  
  socket.onclose = () => {
    console.log('Disconnected from Jarvis WebSocket');
    setTimeout(connectWebSocket, 5000); // Reconnect after 5 seconds
  };
}

// Handle incoming WebSocket messages
function handleWebSocketMessage(message: any) {
  switch (message.message_type) {
    case 'browser_command':
      handleBrowserCommand(message.content);
      break;
    case 'interface_action':
      handleInterfaceAction(message.content);
      break;
  }
}

// Handle browser commands
function handleBrowserCommand(content: any) {
  switch (content.command) {
    case 'SCROLL_TO':
      window.scrollTo({
        top: content.position,
        behavior: 'smooth'
      });
      break;
      
    case 'CLICK_ELEMENT':
      const element = document.querySelector(content.selector);
      if (element) {
        (element as HTMLElement).click();
      }
      break;
      
    case 'EXTRACT_TEXT':
      const textContent = document.body.textContent;
      socket?.send(JSON.stringify({
        sender: 'browser-extension',
        message_type: 'browser_response',
        content: {
          command: 'EXTRACT_TEXT',
          text: textContent
        }
      }));
      break;
      
    case 'HIGHLIGHT_ELEMENT':
      const targetElement = document.querySelector(content.selector);
      if (targetElement) {
        const originalBackground = (targetElement as HTMLElement).style.backgroundColor;
        (targetElement as HTMLElement).style.backgroundColor = 'yellow';
        setTimeout(() => {
          (targetElement as HTMLElement).style.backgroundColor = originalBackground;
        }, 2000);
      }
      break;
  }
}

// Handle interface actions
function handleInterfaceAction(content: any) {
  switch (content.command) {
    case 'CAPTURE_SCREENSHOT':
      // Send message to background script to capture screenshot
      chrome.runtime.sendMessage({
        type: 'CAPTURE_SCREENSHOT',
        data: { url: window.location.href }
      });
      break;
      
    case 'MONITOR_CHANGES':
      // Start monitoring DOM changes
      const observer = new MutationObserver((mutations) => {
        socket?.send(JSON.stringify({
          sender: 'browser-extension',
          message_type: 'dom_change',
          content: {
            url: window.location.href,
            changes: mutations.length
          }
        }));
      });
      
      observer.observe(document.body, {
        childList: true,
        subtree: true,
        attributes: true
      });
      break;
  }
}

// Listen for messages from the popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === 'GET_PAGE_INFO') {
    sendResponse({
      url: window.location.href,
      title: document.title,
      content: document.body.textContent
    });
  }
});

// Initialize WebSocket connection
connectWebSocket();
