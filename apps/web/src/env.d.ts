/// <reference types="vite/client" />
declare module 'virtual:mit-index' {
  const catalog: import('./data/catalog').MitIndex
  export default catalog
}
declare module 'virtual:mit-load' {
  export function loadFight(id: string): Promise<import('./data/catalog').FightBundle | null>
}
interface Window {
  documentPictureInPicture?: {
    requestWindow(options: { width: number; height: number }): Promise<Window>
  }
}
