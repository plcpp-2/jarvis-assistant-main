import { buildConfig } from 'payload/config'
import path from 'path'
import { mongooseAdapter } from '@payloadcms/db-mongodb'
import { slateEditor } from '@payloadcms/richtext-slate'
import { webpackBundler } from '@payloadcms/bundler-webpack'
import { Tasks } from './collections/Tasks'
import { Agents } from './collections/Agents'
import { Knowledge } from './collections/Knowledge'
import { SystemMetrics } from './collections/SystemMetrics'
import { Users } from './collections/Users'

export default buildConfig({
  serverURL: process.env.PAYLOAD_PUBLIC_SERVER_URL || 'http://localhost:3000',
  admin: {
    user: Users.slug,
    bundler: webpackBundler(),
    meta: {
      titleSuffix: '- Jarvis Assistant',
      favicon: '/assets/favicon.ico',
      ogImage: '/assets/og-image.jpg',
    },
    components: {
      // Add custom components here
    },
  },
  editor: slateEditor({}),
  db: mongooseAdapter({
    url: process.env.MONGODB_URI || 'mongodb://localhost/jarvis-assistant',
  }),
  collections: [
    Tasks,
    Agents,
    Knowledge,
    SystemMetrics,
    Users,
  ],
  typescript: {
    outputFile: path.resolve(__dirname, 'payload-types.ts'),
  },
  graphQL: {
    schemaOutputFile: path.resolve(__dirname, 'generated-schema.graphql'),
  },
})
