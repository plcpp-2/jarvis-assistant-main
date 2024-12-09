import { CollectionConfig } from 'payload/types'

export const Knowledge: CollectionConfig = {
  slug: 'knowledge',
  admin: {
    useAsTitle: 'title',
    defaultColumns: ['title', 'type', 'createdAt'],
    group: 'Content',
  },
  access: {
    read: () => true,
  },
  fields: [
    {
      name: 'title',
      type: 'text',
      required: true,
    },
    {
      name: 'type',
      type: 'select',
      required: true,
      options: [
        { label: 'Document', value: 'document' },
        { label: 'Image', value: 'image' },
        { label: 'Video', value: 'video' },
        { label: 'Code', value: 'code' },
        { label: 'Other', value: 'other' },
      ],
    },
    {
      name: 'content',
      type: 'richText',
      admin: {
        condition: (data) => data.type === 'document',
      },
    },
    {
      name: 'code',
      type: 'code',
      admin: {
        condition: (data) => data.type === 'code',
        language: 'javascript',
      },
    },
    {
      name: 'media',
      type: 'upload',
      relationTo: 'media',
      admin: {
        condition: (data) => ['image', 'video'].includes(data.type),
      },
    },
    {
      name: 'metadata',
      type: 'group',
      fields: [
        {
          name: 'source',
          type: 'text',
        },
        {
          name: 'author',
          type: 'text',
        },
        {
          name: 'dateCreated',
          type: 'date',
        },
        {
          name: 'tags',
          type: 'array',
          fields: [
            {
              name: 'tag',
              type: 'text',
            },
          ],
        },
      ],
    },
    {
      name: 'embedding',
      type: 'json',
      admin: {
        hidden: true,
      },
    },
    {
      name: 'relations',
      type: 'array',
      fields: [
        {
          name: 'relatedItem',
          type: 'relationship',
          relationTo: 'knowledge',
        },
        {
          name: 'relationType',
          type: 'select',
          options: [
            { label: 'Related to', value: 'related' },
            { label: 'Part of', value: 'part_of' },
            { label: 'References', value: 'references' },
            { label: 'Derived from', value: 'derived_from' },
          ],
        },
      ],
    },
    {
      name: 'status',
      type: 'select',
      defaultValue: 'draft',
      options: [
        { label: 'Draft', value: 'draft' },
        { label: 'Published', value: 'published' },
        { label: 'Archived', value: 'archived' },
      ],
    },
  ],
  timestamps: true,
}
