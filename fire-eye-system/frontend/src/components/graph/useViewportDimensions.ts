import { useEffect, useState } from 'react'

interface ViewportDimensions {
  width: number
  height: number
}

export default function useViewportDimensions(): ViewportDimensions {
  const [dimensions, setDimensions] = useState<ViewportDimensions>({ width: 1200, height: 780 })

  useEffect(() => {
    const updateDimensions = () => {
      const width = window.innerWidth >= 1024 ? window.innerWidth - 64 : window.innerWidth - 24
      const height = window.innerWidth >= 1024 ? window.innerHeight - 210 : window.innerHeight - 260

      setDimensions({
        width: Math.max(width, 320),
        height: Math.max(height, 420),
      })
    }

    updateDimensions()
    window.addEventListener('resize', updateDimensions)

    return () => window.removeEventListener('resize', updateDimensions)
  }, [])

  return dimensions
}
