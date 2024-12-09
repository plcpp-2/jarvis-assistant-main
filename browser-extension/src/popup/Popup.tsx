import React, { useEffect, useState } from 'react';
import {
  Box,
  VStack,
  HStack,
  Text,
  Button,
  Input,
  IconButton,
  useColorMode,
  Divider,
} from '@chakra-ui/react';
import { FiSun, FiMoon, FiSettings, FiRefreshCw } from 'react-icons/fi';
import { browser } from 'webextension-polyfill-ts';
import { useQuery, useMutation } from 'react-query';
import { ApiClient } from '../api/client';

const api = new ApiClient({
  baseUrl: process.env.API_URL || 'http://localhost:8000',
});

export default function Popup() {
  const { colorMode, toggleColorMode } = useColorMode();
  const [query, setQuery] = useState('');
  const [apiStatus, setApiStatus] = useState<'connected' | 'disconnected'>('connected');

  const { data: tasks, isLoading: tasksLoading } = useQuery(
    'recentTasks',
    () => api.tasks.getRecent(),
    { refetchInterval: 30000 }
  );

  const { data: metrics } = useQuery(
    'systemMetrics',
    () => api.system.getMetrics(),
    { refetchInterval: 5000 }
  );

  const createTask = useMutation(
    (taskData: any) => api.tasks.create(taskData),
    {
      onSuccess: () => {
        setQuery('');
      },
    }
  );

  useEffect(() => {
    browser.storage.local.get('apiStatus').then((result) => {
      setApiStatus(result.apiStatus || 'connected');
    });

    const listener = (changes: any) => {
      if (changes.apiStatus) {
        setApiStatus(changes.apiStatus.newValue);
      }
    };

    browser.storage.local.onChanged.addListener(listener);
    return () => browser.storage.local.onChanged.removeListener(listener);
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    createTask.mutate({
      title: query,
      type: 'user_query',
      priority: 3,
    });
  };

  return (
    <Box w="400px" p={4}>
      <VStack spacing={4} align="stretch">
        {/* Header */}
        <HStack justify="space-between">
          <Text fontSize="xl" fontWeight="bold">Jarvis Assistant</Text>
          <HStack>
            <IconButton
              aria-label="Toggle color mode"
              icon={colorMode === 'light' ? <FiMoon /> : <FiSun />}
              onClick={toggleColorMode}
              size="sm"
            />
            <IconButton
              aria-label="Settings"
              icon={<FiSettings />}
              onClick={() => browser.runtime.openOptionsPage()}
              size="sm"
            />
          </HStack>
        </HStack>

        {/* Status Indicator */}
        <HStack>
          <Box
            w={2}
            h={2}
            borderRadius="full"
            bg={apiStatus === 'connected' ? 'green.500' : 'red.500'}
          />
          <Text fontSize="sm" color={apiStatus === 'connected' ? 'green.500' : 'red.500'}>
            {apiStatus === 'connected' ? 'Connected' : 'Disconnected'}
          </Text>
          {apiStatus === 'disconnected' && (
            <IconButton
              aria-label="Reconnect"
              icon={<FiRefreshCw />}
              onClick={() => api.system.checkConnection()}
              size="sm"
            />
          )}
        </HStack>

        {/* Query Input */}
        <form onSubmit={handleSubmit}>
          <Input
            placeholder="Ask Jarvis..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            disabled={apiStatus === 'disconnected'}
          />
        </form>

        <Divider />

        {/* Recent Tasks */}
        <VStack align="stretch" spacing={2}>
          <Text fontSize="sm" fontWeight="bold">Recent Tasks</Text>
          {tasksLoading ? (
            <Text fontSize="sm">Loading...</Text>
          ) : tasks?.map((task: any) => (
            <HStack key={task.id} justify="space-between">
              <Text fontSize="sm" noOfLines={1}>{task.title}</Text>
              <Text fontSize="xs" color="gray.500">{task.status}</Text>
            </HStack>
          ))}
        </VStack>

        <Divider />

        {/* System Metrics */}
        {metrics && (
          <VStack align="stretch" spacing={2}>
            <Text fontSize="sm" fontWeight="bold">System Status</Text>
            <HStack justify="space-between">
              <Text fontSize="xs">CPU: {metrics.cpu_percent}%</Text>
              <Text fontSize="xs">Memory: {metrics.memory_percent}%</Text>
              <Text fontSize="xs">Tasks: {metrics.active_tasks}</Text>
            </HStack>
          </VStack>
        )}
      </VStack>
    </Box>
  );
}
