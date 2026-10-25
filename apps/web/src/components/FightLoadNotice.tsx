import { Alert, Button, Stack, Text } from '@mantine/core'

/** A fight chunk is the only thing this app fetches, and it is same-origin.
 *  The wait is one line of text. A failure keeps the same recovery button the
 *  selection screen uses. No spinner: the assignments themselves do not animate. */
export default function FightLoadNotice({ failed, onRetry }: { failed: boolean; onRetry: () => void }) {
  if (!failed) return <Text ta="center" c="dimmed" py="xl" fz="md" role="status">Loading fight…</Text>
  return <Alert color="red" variant="light" role="alert" my="md">
    <Stack gap="xs" align="flex-start">
      <Text fz="sm">This fight could not be loaded.</Text>
      <Button variant="subtle" color="gray" size="compact-sm" onClick={onRetry}>Retry</Button>
    </Stack>
  </Alert>
}
