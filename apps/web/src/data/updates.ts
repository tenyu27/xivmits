// Newest first. The home page and full history share these entries.
export const updates = [
  { date: '2026-09-22', message: 'DSR and DSR Mitty added' },
]

export const updateDate = (date: string) => new Intl.DateTimeFormat('en', {
  month: 'short', day: 'numeric', year: 'numeric', timeZone: 'UTC',
}).format(new Date(`${date}T00:00:00Z`))
