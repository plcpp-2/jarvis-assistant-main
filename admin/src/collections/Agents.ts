import { CollectionConfig } from 'payload/types'

export const Agents: CollectionConfig = {
  slug: 'agents',
  admin: {
    useAsTitle: 'name',
    defaultColumns: ['name', 'status', 'type', 'lastActive'],
    group: 'System',
  },
  access: {
    read: () => true,
  },
  fields: [
    {
      name: 'name',
      type: 'text',
      required: true,
    },
    {
      name: 'type',
      type: 'select',
      required: true,
      options: [
        { label: 'Admin Agent', value: 'admin' },
        { label: 'Task Agent', value: 'task' },
        { label: 'Knowledge Agent', value: 'knowledge' },
        { label: 'File Agent', value: 'file' },
        { label: 'Custom Agent', value: 'custom' },
      ],
    },
    {
      name: 'status',
      type: 'select',
      required: true,
      defaultValue: 'inactive',
      options: [
        { label: 'Active', value: 'active' },
        { label: 'Inactive', value: 'inactive' },
        { label: 'Hibernating', value: 'hibernating' },
        { label: 'Error', value: 'error' },
      ],
    },
    {
      name: 'description',
      type: 'textarea',
    },
    {
      name: 'capabilities',
      type: 'array',
      fields: [
        {
          name: 'capability',
          type: 'text',
        },
      ],
    },
    {
      name: 'configuration',
      type: 'json',
    },
    {
      name: 'metrics',
      type: 'group',
      fields: [
        {
          name: 'tasksCompleted',
          type: 'number',
          defaultValue: 0,
        },
        {
          name: 'tasksFailed',
          type: 'number',
          defaultValue: 0,
        },
        {
          name: 'averageResponseTime',
          type: 'number',
          defaultValue: 0,
        },
        {
          name: 'lastError',
          type: 'text',
        },
      ],
    },
    {
      name: 'lastActive',
      type: 'date',
    },
  ],
  timestamps: true,
}
