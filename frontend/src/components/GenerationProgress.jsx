import { useEffect, useState } from 'react'

export function GenerationProgress({ active, label }) {
  const [progress, setProgress] = useState(0)
  const [shown, setShown] = useState(false)

  useEffect(() => {
    if (!active) return undefined
    setShown(true)
    setProgress(8)
    const timer = setInterval(() => {
      setProgress((value) => {
        if (value >= 92) return value
        const step = Math.max(1, Math.round((92 - value) * 0.15))
        return Math.min(92, value + step)
      })
    }, 250)
    return () => clearInterval(timer)
  }, [active])

  useEffect(() => {
    if (active || !shown) return undefined
    setProgress(100)
    const timer = setTimeout(() => {
      setShown(false)
      setProgress(0)
    }, 450)
    return () => clearTimeout(timer)
  }, [active, shown])

  if (!shown) return null

  return (
    <div
      className="mt-2 w-full"
      role="progressbar"
      aria-valuenow={progress}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-label={label}
    >
      <div className="h-1.5 overflow-hidden rounded-full bg-forest/10">
        <div
          className="h-full rounded-full bg-gradient-to-r from-coral via-leaf to-mint transition-[width] duration-300 ease-out"
          style={{ width: `${progress}%` }}
        />
      </div>
      <p className="mt-1 text-right text-[11px] font-medium text-moss">
        {label} {progress}%
      </p>
    </div>
  )
}
