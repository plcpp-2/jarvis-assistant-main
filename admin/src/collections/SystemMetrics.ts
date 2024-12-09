import { CollectionConfig } from 'payload/types'

export const SystemMetrics: CollectionConfig = {
  slug: 'system-metrics',
  admin: {
    useAsTitle: 'timestamp',
    defaultColumns: ['timestamp', 'cpuUsage', 'memoryUsage', 'status'],
    group: 'System',
  },
  access: {
    read: () => true,
  },
  fields: [
    {
      name: 'timestamp',
      type: 'date',
      required: true,
      admin: {
        date: {
          displayFormat: 'yyyy-MM-dd HH:mm:ss',
        },
      },
    },
    {
      name: 'status',
      type: 'select',
      required: true,
      defaultValue: 'normal',
      options: [
        { label: 'Normal', value: 'normal' },
        { label: 'Warning', value: 'warning' },
        { label: 'Critical', value: 'critical' },
      ],
    },
    {
      name: 'resources',
      type: 'group',
      fields: [
        {
          name: 'cpuUsage',
          type: 'number',
          required: true,
          min: 0,
          max: 100,
        },
        {
          name: 'memoryUsage',
          type: 'number',
          required: true,
          min: 0,
          max: 100,
        },
        {
          name: 'diskUsage',
          type: 'number',
          required: true,
          min: 0,
          max: 100,
        },
        {
          name: 'networkIO',
          type: 'group',
          fields: [
            {
              name: 'bytesSent',
              type: 'number',
              required: true,
            },
            {
              name: 'bytesReceived',
              type: 'number',
              required: true,
            },
          ],
        },
      ],
    },
    {
      name: 'tasks',
      type: 'group',
      fields: [
        {
          name: 'activeTasks',
          type: 'number',
          required: true,
          defaultValue: 0,
        },
        {
          name: 'completedTasks',
          type: 'number',
          required: true,
          defaultValue: 0,
        },
        {
          name: 'failedTasks',
          type: 'number',
          required: true,
          defaultValue: 0,
        },
      ],
    },
    {
      name: 'agents',
      type: 'group',
      fields: [
        {
          name: 'activeAgents',
          type: 'number',
          required: true,
          defaultValue: 0,
        },
        {
          name: 'hibernatingAgents',
          type: 'number',
          required: true,
          defaultValue: 0,
        },
        {
          name: 'errorAgents',
          type: 'number',
          required: true,
          defaultValue: 0,
        },
      ],
    },
    {
      name: 'errors',
      type: 'array',
      fields: [
        {
          name: 'errorType',
          type: 'text',
          required: true,
        },
        {
          name: 'count',
          type: 'number',
          required: true,
        },
        {
          name: 'lastOccurrence',
          type: 'date',
        },
      ],
    },
    {
      name: 'alerts',
      type: 'array',
      fields: [
        {
          name: 'type',
          type: 'select',
          options: [
            { label: 'High CPU Usage', value: 'high_cpu' },
            { label: 'High Memory Usage', value: 'high_memory' },
            { label: 'High Disk Usage', value: 'high_disk' },
            { label: 'High Error Rate', value: 'high_errors' },
            { label: 'System Performance', value: 'performance' },
          ],
        },
        {
          name: 'severity',
          type: 'select',
          options: [
            { label: 'Info', value: 'info' },
            { label: 'Warning', value: 'warning' },
            { label: 'Critical', value: 'critical' },
          ],
        },
        {
          name: 'message',
          type: 'text',
        },
      ],
    },
  ],
  timestamps: true,
}
