import type { TankMitPlan } from './schema.ts'

/** Invalid or stale preferences resolve to the plan's declared defaults. */
export function tankChoices(plan: TankMitPlan, stored: Record<string, string>, seat: string): Record<string, string> {
  return Object.fromEntries((plan.choices ?? []).map(choice => [choice.id,
    (!choice.seats || choice.seats.includes(seat)) && choice.options.some(option => option.id === stored[choice.id])
      ? stored[choice.id] : choice.default,
  ]))
}

/** Resolve once for every layout, including PiP and the shareable cheatsheet. */
export function availableTankChoices(plan: TankMitPlan, seat: string) {
  return (plan.choices ?? []).filter(choice => !choice.seats || choice.seats.includes(seat)).map(choice => ({
    ...choice, options: choice.options.map(option => ({ ...option, label: option.labelBySeat?.[seat] ?? option.label })),
  }))
}

export function selectTankRoute(plan: TankMitPlan, choices: Record<string, string>, seat: string): TankMitPlan {
  const resolved = tankChoices(plan, choices, seat)
  return {
    ...plan,
    phases: plan.phases.map(phase => ({
      ...phase,
      mechanics: phase.mechanics.filter(row =>
        (!row.seat || row.seat === seat)
        && Object.entries(row.when ?? {}).every(([key, value]) => resolved[key] === value)),
    })),
  }
}
