import { browser } from 'webextension-polyfill-ts';

interface TaskExecutorConfig {
  maxConcurrentTasks: number;
  defaultTimeout: number;
  retryAttempts: number;
}

class TaskExecutor {
  private socket: WebSocket;
  private activeTaskCount: number = 0;
  private config: TaskExecutorConfig;
  private taskQueue: Array<any> = [];

  constructor(config: TaskExecutorConfig) {
    this.config = config;
    this.initializeWebSocket();
  }

  private initializeWebSocket() {
    this.socket = new WebSocket('ws://localhost:8000/ws/browser-extension/browsers');
    
    this.socket.onmessage = async (event) => {
      const message = JSON.parse(event.data);
      if (message.message_type === 'task_request') {
        await this.handleTaskRequest(message.content);
      }
    };

    this.socket.onclose = () => {
      setTimeout(() => this.initializeWebSocket(), 5000);
    };
  }

  private async handleTaskRequest(task: any) {
    if (this.activeTaskCount >= this.config.maxConcurrentTasks) {
      this.taskQueue.push(task);
      return;
    }

    this.activeTaskCount++;
    try {
      const result = await this.executeTask(task);
      this.sendTaskResult(task.id, 'completed', result);
    } catch (error) {
      this.sendTaskResult(task.id, 'failed', null, error);
    }
    this.activeTaskCount--;

    if (this.taskQueue.length > 0) {
      const nextTask = this.taskQueue.shift();
      await this.handleTaskRequest(nextTask);
    }
  }

  private async executeTask(task: any) {
    switch (task.type) {
      case 'DOM_MANIPULATION':
        return await this.executeDOMTask(task);
      case 'NETWORK_INTERCEPT':
        return await this.executeNetworkTask(task);
      case 'UI_AUTOMATION':
        return await this.executeUITask(task);
      case 'DATA_EXTRACTION':
        return await this.executeDataExtractionTask(task);
      default:
        throw new Error(`Unknown task type: ${task.type}`);
    }
  }

  private async executeDOMTask(task: any) {
    const { action, selector, value } = task.parameters;

    switch (action) {
      case 'CLICK':
        return await this.executeInPage((selector: string) => {
          const element = document.querySelector(selector);
          if (element) {
            (element as HTMLElement).click();
            return true;
          }
          return false;
        }, selector);

      case 'INPUT':
        return await this.executeInPage((selector: string, value: string) => {
          const element = document.querySelector(selector) as HTMLInputElement;
          if (element) {
            element.value = value;
            element.dispatchEvent(new Event('input', { bubbles: true }));
            return true;
          }
          return false;
        }, selector, value);

      case 'SCROLL':
        return await this.executeInPage((selector: string) => {
          const element = document.querySelector(selector);
          if (element) {
            element.scrollIntoView({ behavior: 'smooth' });
            return true;
          }
          return false;
        }, selector);

      default:
        throw new Error(`Unknown DOM action: ${action}`);
    }
  }

  private async executeNetworkTask(task: any) {
    const { url, method, headers, body } = task.parameters;

    return await fetch(url, {
      method,
      headers,
      body: JSON.stringify(body),
    }).then(response => response.json());
  }

  private async executeUITask(task: any) {
    const { action, parameters } = task.parameters;

    switch (action) {
      case 'OPEN_POPUP':
        return await browser.windows.create({
          url: parameters.url,
          type: 'popup',
          width: parameters.width,
          height: parameters.height,
        });

      case 'SHOW_NOTIFICATION':
        return await browser.notifications.create({
          type: 'basic',
          iconUrl: parameters.icon,
          title: parameters.title,
          message: parameters.message,
        });

      default:
        throw new Error(`Unknown UI action: ${action}`);
    }
  }

  private async executeDataExtractionTask(task: any) {
    const { type, selector } = task.parameters;

    switch (type) {
      case 'TEXT':
        return await this.executeInPage((selector: string) => {
          const elements = document.querySelectorAll(selector);
          return Array.from(elements).map(el => el.textContent);
        }, selector);

      case 'ATTRIBUTES':
        return await this.executeInPage((selector: string, attributes: string[]) => {
          const element = document.querySelector(selector);
          if (!element) return null;
          
          return attributes.reduce((acc: any, attr) => {
            acc[attr] = element.getAttribute(attr);
            return acc;
          }, {});
        }, selector, task.parameters.attributes);

      case 'SCREENSHOT':
        return await browser.tabs.captureVisibleTab();

      default:
        throw new Error(`Unknown extraction type: ${type}`);
    }
  }

  private async executeInPage(func: Function, ...args: any[]) {
    const [tab] = await browser.tabs.query({ active: true, currentWindow: true });
    if (!tab.id) throw new Error('No active tab');

    return await browser.tabs.sendMessage(tab.id, {
      type: 'EXECUTE_IN_PAGE',
      function: func.toString(),
      arguments: args,
    });
  }

  private sendTaskResult(taskId: string, status: string, result: any = null, error: any = null) {
    this.socket.send(JSON.stringify({
      message_type: 'task_result',
      content: {
        task_id: taskId,
        status,
        result,
        error: error ? error.message : null,
        timestamp: new Date().toISOString(),
      },
    }));
  }
}

export const taskExecutor = new TaskExecutor({
  maxConcurrentTasks: 5,
  defaultTimeout: 30000,
  retryAttempts: 3,
});
