import { browser } from 'webextension-polyfill-ts';
import { setupContextMenus } from './utils/contextMenus';
import { setupNotifications } from './utils/notifications';
import { setupWebRequest } from './utils/webRequest';
import { ApiClient } from './api/client';

// Initialize API client
const api = new ApiClient({
  baseUrl: process.env.API_URL || 'http://localhost:8000',
});

// Setup context menus
browser.runtime.onInstalled.addListener(() => {
  setupContextMenus();
});

// Handle context menu clicks
browser.contextMenus.onClicked.addListener(async (info, tab) => {
  if (info.menuItemId === 'addToKnowledge') {
    try {
      await api.knowledge.addDocument({
        title: tab?.title || 'Untitled',
        content: info.selectionText || '',
        url: tab?.url,
        tags: ['web-clip'],
      });
      
      await browser.notifications.create({
        type: 'basic',
        iconUrl: 'icons/icon48.png',
        title: 'Content Saved',
        message: 'Selected content has been added to your knowledge base',
      });
    } catch (error) {
      console.error('Error saving content:', error);
    }
  }
});

// Handle messages from content scripts
browser.runtime.onMessage.addListener(async (message, sender) => {
  switch (message.type) {
    case 'ANALYZE_PAGE':
      try {
        const analysis = await api.analyze.page({
          url: sender.tab?.url,
          content: message.payload.content,
        });
        return { success: true, data: analysis };
      } catch (error) {
        return { success: false, error };
      }
      
    case 'CREATE_TASK':
      try {
        const task = await api.tasks.create({
          title: message.payload.title,
          description: message.payload.description,
          type: message.payload.type,
          priority: message.payload.priority,
        });
        return { success: true, data: task };
      } catch (error) {
        return { success: false, error };
      }
      
    default:
      return { success: false, error: 'Unknown message type' };
  }
});

// Setup web request monitoring
setupWebRequest();

// Setup notification system
setupNotifications();

// Handle extension updates
browser.runtime.onUpdateAvailable.addListener((details) => {
  console.log('Update available:', details);
  browser.runtime.reload();
});

// Handle connectivity changes
browser.webRequest.onCompleted.addListener(
  (details) => {
    if (details.url === api.baseUrl) {
      browser.storage.local.set({ apiStatus: 'connected' });
    }
  },
  { urls: [api.baseUrl + '/*'] }
);

browser.webRequest.onErrorOccurred.addListener(
  (details) => {
    if (details.url === api.baseUrl) {
      browser.storage.local.set({ apiStatus: 'disconnected' });
    }
  },
  { urls: [api.baseUrl + '/*'] }
);
