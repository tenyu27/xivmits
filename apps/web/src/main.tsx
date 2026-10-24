import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
// Component styles only. The full `@mantine/core/styles.css` ships every
// widget in the library, and this page uses a handful. Order matches
// Mantine's own bundle: variables, then baseline, then components.
// index.css aliases product tokens onto those variables and has to come after.
import '@mantine/core/styles/baseline.css'
import '@mantine/core/styles/default-css-variables.css'
import '@mantine/core/styles/global.css'
import '@mantine/core/styles/UnstyledButton.css'
import '@mantine/core/styles/Button.css'
import '@mantine/core/styles/CloseButton.css'
import '@mantine/core/styles/Alert.css'
import '@mantine/core/styles/Anchor.css'
import '@mantine/core/styles/Badge.css'
import '@mantine/core/styles/Container.css'
import '@mantine/core/styles/Divider.css'
import '@mantine/core/styles/Group.css'
import '@mantine/core/styles/Stack.css'
import '@mantine/core/styles/Input.css'
import '@mantine/core/styles/Combobox.css'
import '@mantine/core/styles/Text.css'
import '@mantine/core/styles/Title.css'
import '@mantine/core/styles/Tooltip.css'
import '@mantine/core/styles/FloatingIndicator.css'
import '@mantine/core/styles/SegmentedControl.css'
import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
