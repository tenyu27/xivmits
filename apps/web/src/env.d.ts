/// <reference types="vite/client" />
declare module 'virtual:mit-catalog' {
  const catalog: import('@xivmits/core').Catalog
  export default catalog
}
interface Window {
  documentPictureInPicture?: {
    requestWindow(options: { width: number; height: number }): Promise<Window>
  }
}
