import React from 'react';
import {
  Box,
  SimpleGrid,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatArrow,
  Progress,
  useColorModeValue,
} from '@chakra-ui/react';
import { useQuery } from 'react-query';
import { getSystemMetrics } from '../../api/system';

interface MetricCardProps {
  title: string;
  value: number;
  change?: number;
  unit?: string;
  showProgress?: boolean;
}

function MetricCard({ title, value, change, unit = '%', showProgress = true }: MetricCardProps) {
  const bg = useColorModeValue('white', 'gray.700');
  const borderColor = useColorModeValue('gray.200', 'gray.600');

  return (
    <Box
      p={5}
      bg={bg}
      rounded="lg"
      borderWidth="1px"
      borderColor={borderColor}
      shadow="sm"
    >
      <Stat>
        <StatLabel fontSize="sm" color="gray.500">
          {title}
        </StatLabel>
        <StatNumber fontSize="2xl">
          {value.toFixed(1)}{unit}
        </StatNumber>
        {change !== undefined && (
          <StatHelpText>
            <StatArrow type={change >= 0 ? 'increase' : 'decrease'} />
            {Math.abs(change).toFixed(1)}%
          </StatHelpText>
        )}
        {showProgress && (
          <Progress
            value={value}
            colorScheme={value > 80 ? 'red' : value > 60 ? 'yellow' : 'green'}
            size="sm"
            mt={2}
          />
        )}
      </Stat>
    </Box>
  );
}

export default function SystemMetrics() {
  const { data, isLoading, error } = useQuery('systemMetrics', getSystemMetrics, {
    refetchInterval: 5000, // Refresh every 5 seconds
  });

  if (isLoading) return <Box>Loading metrics...</Box>;
  if (error) return <Box>Error loading metrics</Box>;

  return (
    <SimpleGrid columns={{ base: 1, md: 2, lg: 4 }} spacing={4}>
      <MetricCard
        title="CPU Usage"
        value={data.cpu_percent}
        change={data.cpu_change}
      />
      <MetricCard
        title="Memory Usage"
        value={data.memory_percent}
        change={data.memory_change}
      />
      <MetricCard
        title="Disk Usage"
        value={data.disk_percent}
        change={data.disk_change}
      />
      <MetricCard
        title="Network Load"
        value={data.network_load}
        unit=" Mbps"
        showProgress={false}
      />
      <MetricCard
        title="Active Agents"
        value={data.active_agents}
        unit=""
        showProgress={false}
      />
      <MetricCard
        title="Task Queue"
        value={data.queued_tasks}
        unit=""
        showProgress={false}
      />
      <MetricCard
        title="Error Rate"
        value={data.error_rate}
        change={data.error_rate_change}
      />
      <MetricCard
        title="Response Time"
        value={data.response_time}
        unit=" ms"
        showProgress={false}
      />
    </SimpleGrid>
  );
}
