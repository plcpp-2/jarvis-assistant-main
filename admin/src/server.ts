import express from 'express'
import payload from 'payload'
import { resolve } from 'path'
import { config } from 'dotenv'

// Load environment variables
config()

const app = express()

// Initialize Payload
const start = async () => {
  await payload.init({
    secret: process.env.PAYLOAD_SECRET || 'your-secret-key',
    express: app,
    onInit: async () => {
      payload.logger.info(`Payload Admin URL: ${payload.getAdminURL()}`)
    },
  })

  // Add custom routes here
  app.get('/health', (_, res) => {
    res.status(200).json({ status: 'healthy' })
  })

  const port = process.env.PORT || 3000
  app.listen(port, async () => {
    payload.logger.info(`Server listening on port ${port}`)
  })
}

start()
