import { useState } from 'react'
import { useWebSocket } from '@/lib/websocket'
import { Card } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Textarea } from '@/components/ui/textarea'
import { Switch } from '@/components/ui/switch'
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form'
import { zodResolver } from '@hookform/resolvers/zod'
import { useForm } from 'react-hook-form'
import * as z from 'zod'

const taskSchema = z.object({
  taskType: z.enum(['browser_action', 'file_operation', 'api_call', 'ml_inference']),
  priority: z.number().min(1).max(10),
  timeout: z.number().min(0).optional(),
  retryEnabled: z.boolean(),
  maxRetries: z.number().min(0).max(5),
  parameters: z.record(z.any()),
  dependencies: z.array(z.string()).optional(),
})

export function TaskCreator() {
  const [selectedTaskType, setSelectedTaskType] = useState<string>('browser_action')
  const websocket = useWebSocket()
  
  const form = useForm<z.infer<typeof taskSchema>>({
    resolver: zodResolver(taskSchema),
    defaultValues: {
      priority: 5,
      timeout: 30,
      retryEnabled: true,
      maxRetries: 3,
      parameters: {},
      dependencies: [],
    },
  })

  const onSubmit = (data: z.infer<typeof taskSchema>) => {
    websocket.sendMessage({
      sender: 'interface',
      message_type: 'task_request',
      content: {
        task_id: `task-${Date.now()}`,
        ...data,
      },
    })
    
    form.reset()
  }

  const renderParameterFields = () => {
    switch (selectedTaskType) {
      case 'browser_action':
        return (
          <>
            <FormField
              control={form.control}
              name="parameters.action"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Action</FormLabel>
                  <Select
                    onValueChange={field.onChange}
                    defaultValue={field.value}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select action" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="CLICK">Click Element</SelectItem>
                      <SelectItem value="INPUT">Input Text</SelectItem>
                      <SelectItem value="SCROLL">Scroll To</SelectItem>
                      <SelectItem value="EXTRACT">Extract Data</SelectItem>
                    </SelectContent>
                  </Select>
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="parameters.selector"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>CSS Selector</FormLabel>
                  <FormControl>
                    <Input {...field} placeholder="#button-id or .class-name" />
                  </FormControl>
                </FormItem>
              )}
            />
          </>
        )

      case 'file_operation':
        return (
          <>
            <FormField
              control={form.control}
              name="parameters.operation"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Operation</FormLabel>
                  <Select
                    onValueChange={field.onChange}
                    defaultValue={field.value}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select operation" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="read">Read</SelectItem>
                      <SelectItem value="write">Write</SelectItem>
                      <SelectItem value="delete">Delete</SelectItem>
                    </SelectContent>
                  </Select>
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="parameters.path"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>File Path</FormLabel>
                  <FormControl>
                    <Input {...field} placeholder="/path/to/file" />
                  </FormControl>
                </FormItem>
              )}
            />
          </>
        )

      case 'api_call':
        return (
          <>
            <FormField
              control={form.control}
              name="parameters.method"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>HTTP Method</FormLabel>
                  <Select
                    onValueChange={field.onChange}
                    defaultValue={field.value}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select method" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="GET">GET</SelectItem>
                      <SelectItem value="POST">POST</SelectItem>
                      <SelectItem value="PUT">PUT</SelectItem>
                      <SelectItem value="DELETE">DELETE</SelectItem>
                    </SelectContent>
                  </Select>
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="parameters.url"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>URL</FormLabel>
                  <FormControl>
                    <Input {...field} placeholder="https://api.example.com" />
                  </FormControl>
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="parameters.data"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Request Body (JSON)</FormLabel>
                  <FormControl>
                    <Textarea
                      {...field}
                      placeholder="{}"
                      className="font-mono"
                    />
                  </FormControl>
                </FormItem>
              )}
            />
          </>
        )

      case 'ml_inference':
        return (
          <>
            <FormField
              control={form.control}
              name="parameters.model"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Model</FormLabel>
                  <Select
                    onValueChange={field.onChange}
                    defaultValue={field.value}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select model" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="text-classification">
                        Text Classification
                      </SelectItem>
                      <SelectItem value="token-classification">
                        Token Classification
                      </SelectItem>
                      <SelectItem value="question-answering">
                        Question Answering
                      </SelectItem>
                    </SelectContent>
                  </Select>
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="parameters.input"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Input Text</FormLabel>
                  <FormControl>
                    <Textarea
                      {...field}
                      placeholder="Enter text for inference..."
                    />
                  </FormControl>
                </FormItem>
              )}
            />
          </>
        )
    }
  }

  return (
    <Card className="p-6">
      <h3 className="text-lg font-semibold mb-4">Create Task</h3>
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
          <FormField
            control={form.control}
            name="taskType"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Task Type</FormLabel>
                <Select
                  onValueChange={(value) => {
                    field.onChange(value)
                    setSelectedTaskType(value)
                  }}
                  defaultValue={field.value}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select task type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="browser_action">Browser Action</SelectItem>
                    <SelectItem value="file_operation">File Operation</SelectItem>
                    <SelectItem value="api_call">API Call</SelectItem>
                    <SelectItem value="ml_inference">ML Inference</SelectItem>
                  </SelectContent>
                </Select>
              </FormItem>
            )}
          />

          <div className="grid grid-cols-2 gap-4">
            <FormField
              control={form.control}
              name="priority"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Priority (1-10)</FormLabel>
                  <FormControl>
                    <Input
                      type="number"
                      {...field}
                      onChange={(e) => field.onChange(parseInt(e.target.value))}
                    />
                  </FormControl>
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="timeout"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Timeout (seconds)</FormLabel>
                  <FormControl>
                    <Input
                      type="number"
                      {...field}
                      onChange={(e) => field.onChange(parseInt(e.target.value))}
                    />
                  </FormControl>
                </FormItem>
              )}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <FormField
              control={form.control}
              name="retryEnabled"
              render={({ field }) => (
                <FormItem className="flex items-center space-x-2">
                  <FormControl>
                    <Switch
                      checked={field.value}
                      onCheckedChange={field.onChange}
                    />
                  </FormControl>
                  <FormLabel>Enable Retries</FormLabel>
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="maxRetries"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Max Retries</FormLabel>
                  <FormControl>
                    <Input
                      type="number"
                      {...field}
                      onChange={(e) => field.onChange(parseInt(e.target.value))}
                      disabled={!form.watch('retryEnabled')}
                    />
                  </FormControl>
                </FormItem>
              )}
            />
          </div>

          <div className="space-y-4">
            {renderParameterFields()}
          </div>

          <Button type="submit" className="w-full">
            Create Task
          </Button>
        </form>
      </Form>
    </Card>
  )
}
