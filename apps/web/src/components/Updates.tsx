import { Anchor, Box, Divider, Group, Stack, Text, Title } from '@mantine/core'
import { updateDate, updates } from '../data/updates'

export const updatesPath = `${import.meta.env.BASE_URL}updates/`

export function LatestUpdate() {
  const latest = updates[0]
  return <Box component="section" aria-labelledby="latest-update" w="100%" maw={480} mx="auto" mt="auto" pt="xl">
    <Divider color="var(--border)" mb="md" />
    <Stack gap="xs">
      <Group gap="xs">
        <Title id="latest-update" order={2} fz="sm" fw={600}>Latest update</Title>
        <Text component="time" dateTime={latest.date} fz="xs" c="dimmed">{updateDate(latest.date)}</Text>
      </Group>
      <Text fz="sm">{latest.message}</Text>
      <Anchor href={updatesPath} fz="sm">View all updates →</Anchor>
    </Stack>
  </Box>
}

export function UpdatesPage() {
  return <Stack w="100%" maw={480} mx="auto" gap="xl">
    <Title order={1}>Updates</Title>
    {updates.map(update => <Stack component="article" key={update.date} gap="xs">
      <Title order={2} fz="sm" c="dimmed">
        <time dateTime={update.date}>{updateDate(update.date)}</time>
      </Title>
      <Text>{update.message}</Text>
    </Stack>)}
    <Anchor href={import.meta.env.BASE_URL} fz="sm">Back to fights</Anchor>
  </Stack>
}
