/// <reference types="vite/client" />
declare module 'virtual:mit-catalog' {
  const catalog: import('./data/schema').Catalog
  export default catalog
}
interface Window {
  documentPictureInPicture?: {
    requestWindow(options: { width: number; height: number }): Promise<Window>
  }
}
