import { CollectionConfig } from 'payload/types'

export const Users: CollectionConfig = {
  slug: 'users',
  auth: true,
  admin: {
    useAsTitle: 'email',
    defaultColumns: ['email', 'role', 'lastLogin'],
    group: 'Admin',
  },
  access: {
    read: () => true,
  },
  fields: [
    {
      name: 'role',
      type: 'select',
      required: true,
      defaultValue: 'user',
      options: [
        { label: 'Admin', value: 'admin' },
        { label: 'Manager', value: 'manager' },
        { label: 'User', value: 'user' },
      ],
    },
    {
      name: 'name',
      type: 'group',
      fields: [
        {
          name: 'first',
          type: 'text',
          required: true,
        },
        {
          name: 'last',
          type: 'text',
          required: true,
        },
      ],
    },
    {
      name: 'avatar',
      type: 'upload',
      relationTo: 'media',
    },
    {
      name: 'preferences',
      type: 'group',
      fields: [
        {
          name: 'theme',
          type: 'select',
          defaultValue: 'light',
          options: [
            { label: 'Light', value: 'light' },
            { label: 'Dark', value: 'dark' },
            { label: 'System', value: 'system' },
          ],
        },
        {
          name: 'notifications',
          type: 'group',
          fields: [
            {
              name: 'email',
              type: 'checkbox',
              defaultValue: true,
            },
            {
              name: 'push',
              type: 'checkbox',
              defaultValue: true,
            },
            {
              name: 'desktop',
              type: 'checkbox',
              defaultValue: true,
            },
          ],
        },
      ],
    },
    {
      name: 'lastLogin',
      type: 'date',
      admin: {
        position: 'sidebar',
        date: {
          displayFormat: 'yyyy-MM-dd HH:mm:ss',
        },
      },
    },
    {
      name: 'apiKeys',
      type: 'array',
      admin: {
        condition: (data) => ['admin', 'manager'].includes(data.role),
      },
      fields: [
        {
          name: 'name',
          type: 'text',
          required: true,
        },
        {
          name: 'key',
          type: 'text',
          required: true,
          admin: {
            readOnly: true,
          },
        },
        {
          name: 'expiresAt',
          type: 'date',
        },
        {
          name: 'lastUsed',
          type: 'date',
        },
      ],
    },
  ],
  timestamps: true,
}
