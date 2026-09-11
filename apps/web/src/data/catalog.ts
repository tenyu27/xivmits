import type { Catalog } from '@xivmits/core'
// The Vite plugin validates every JSON file before exposing this bundled module.
import catalog from 'virtual:mit-catalog'
export default catalog as Catalog
