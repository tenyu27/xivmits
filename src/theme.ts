import {
  NativeSelect, createTheme, defaultVariantColorsResolver,
  type MantineColorsTuple, type VariantColorsResolver,
} from '@mantine/core'

// Mantine owns the palette. index.css aliases the product tokens onto the
// variables Mantine generates, so there is exactly one source of truth and the
// PiP document (which clones stylesheets, not React state) still resolves them.
const accent: MantineColorsTuple = [
  '#eff5ff', '#e6efff', '#c9dcfd', '#93b4fb', '#60a5fa',
  '#3b82f6', '#2563eb', '#1d4ed8', '#1e40af', '#16273f',
]

// Overrides Mantine's stock greys with the surfaces from DESIGN.md §3.
// Index order is Mantine's: 0 is the lightest text, 7 the page background.
// Index 1 is the secondary text shade, tuned so a mechanic name reads a clear
// step below an ability name (1.6x) without dropping to note level.
const dark: MantineColorsTuple = [
  '#e8edf4', '#b3bfcd', '#9aa6b6', '#929faf', '#3d4959',
  '#2b3542', '#161b22', '#0d1117', '#0a0e13', '#06090c',
]

// Index 5 is the faint text shade (timestamps). It is darker than a stock grey
// ramp would put it because #8b94a3 on white measures 3.06:1 - under the 4.5:1
// DESIGN.md §3 requires.
// Warm neutrals for the mechanic (cast) name. The ability text is cool-tinted,
// so shifting the cast warm separates the two by hue as well as by contrast -
// they stop reading as the same kind of text at a glance. Not an accent: these
// are neutrals, and nothing else in the app uses them.
const sand: MantineColorsTuple = [
  '#f5f1ea', '#e8e1d6', '#d8cfc0', '#c6bcab', '#b3a892',
  '#9e9179', '#877a62', '#6b5f4b', '#4e4336', '#332b21',
]

const gray: MantineColorsTuple = [
  '#f7f8fa', '#eef0f4', '#e2e6ec', '#d8dce4', '#b9c0cc',
  '#697383', '#5a6473', '#3d4653', '#232a34', '#14181f',
]

// Mantine's stock `outline` picks a very pale shade in dark mode, and `subtle`
// a near-white one. DESIGN.md wants the accent itself and muted text - resolve
// those here so variant colors stay owned by the theme, not by overrides.
const variantColorResolver: VariantColorsResolver = input => {
  const resolved = defaultVariantColorsResolver(input)
  // Mantine resolves theme colors to CSS variables, so it cannot measure their
  // luminance and falls back to white text on `filled`. The theme already
  // computes the right contrast color from autoContrast - use it.
  if (input.variant === 'filled' && (!input.color || input.color === 'accent')) {
    return { ...resolved, color: 'var(--mantine-primary-color-contrast)' }
  }
  if (input.variant === 'outline') {
    return { ...resolved, color: 'var(--accent)', border: '1px solid var(--accent-border)', hover: 'var(--accent-soft)', hoverColor: 'var(--accent)' }
  }
  if (input.variant === 'subtle' && input.color === 'gray') {
    return { ...resolved, color: 'var(--text-muted)', hover: 'var(--surface-alt)', hoverColor: 'var(--text)' }
  }
  return resolved
}

export const theme = createTheme({
  variantColorResolver,
  fontFamily: 'ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif',
  fontFamilyMonospace: 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace',
  colors: { accent, dark, gray, sand },
  primaryColor: 'accent',
  primaryShade: { light: 6, dark: 4 },
  defaultRadius: 'md',
  // Picks a readable text color on filled accents - dark text on the light
  // blue in dark mode, white on the deep blue in light. DESIGN.md's --on-accent.
  autoContrast: true,
  luminanceThreshold: 0.3,
  radius: { xs: '2px', sm: '4px', md: '8px', lg: '12px', xl: '16px' },
  spacing: { xs: '4px', sm: '8px', md: '16px', lg: '24px', xl: '32px' },
  fontSizes: { xs: '0.75rem', sm: '0.875rem', md: '1rem', lg: '1.25rem', xl: '1.5rem' },
  lineHeights: { xs: '1.2', sm: '1.2', md: '1.5', lg: '1.5', xl: '1.5' },
  headings: { fontWeight: '650', sizes: { h1: { fontSize: '2rem', lineHeight: '1.2' }, h2: { fontSize: '1.25rem', lineHeight: '1.2' }, h3: { fontSize: '0.875rem', lineHeight: '1.2' } } },
  components: {
    // Mantine's own class names are hashed, so give the select input a stable
    // hook we control - the control row needs to set a shared height on it.
    NativeSelect: NativeSelect.extend({ defaultProps: { classNames: { input: 'control-input' } } }),
  },
  focusRing: 'auto',
  cursorType: 'pointer',
  respectReducedMotion: true,
})
