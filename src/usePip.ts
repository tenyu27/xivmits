import { useEffect, useRef, useState } from 'react'

// `scheme` is the opener's already-resolved 'light' | 'dark'. The PiP window
// follows it rather than its own OS preference - see DESIGN.md §8.
export function usePip(scheme: string) {
  const [pipWindow, setPipWindow] = useState<Window | null>(null)
  const [error, setError] = useState('')
  const current = useRef<Window | null>(null)
  const opening = useRef(false)
  useEffect(() => () => { current.current?.close() }, [])
  useEffect(() => {
    if (current.current) current.current.document.documentElement.dataset.mantineColorScheme = scheme
  }, [pipWindow, scheme])
  async function open() {
    if (current.current && !current.current.closed) { current.current.focus(); return }
    if (opening.current || !window.documentPictureInPicture) return
    opening.current = true
    setError('')
    try {
      const next = await window.documentPictureInPicture.requestWindow({ width: 400, height: 600 })
      next.document.title = 'XIVMits'
      next.document.documentElement.lang = 'en'
      next.document.documentElement.dataset.mantineColorScheme = scheme
      document.querySelectorAll('style, link[rel="stylesheet"]').forEach(style => next.document.head.append(style.cloneNode(true)))
      next.document.body.className = 'pip-body'
      current.current = next
      next.addEventListener('pagehide', () => {
        if (current.current === next) { current.current = null; setPipWindow(null) }
      }, { once: true })
      setPipWindow(next)
    } catch { setError("Picture-in-Picture couldn't open. Try again from this tab.") }
    finally { opening.current = false }
  }
  function close() { current.current?.close(); current.current = null; setPipWindow(null) }
  return { pipWindow, error, open, close, supported: 'documentPictureInPicture' in window }
}
