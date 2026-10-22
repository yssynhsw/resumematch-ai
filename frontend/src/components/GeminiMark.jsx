import { useId } from 'react'
import { useSystemStatus } from '../context/SystemStatusContext'

export function GeminiMark({ className }) {
  const { status } = useSystemStatus()
  const gradientId = `gemini-spark-${useId().replace(/[^a-zA-Z0-9_-]/g, '')}`
  const provider = status?.provider
  const show = (provider === 'gemini' || provider === 'google') && status?.llm_mode !== 'mock'
  if (!show) return null

  return (
    <span
      title="Gemini"
      aria-label="Gemini"
      className={['inline-flex items-center gap-1 rounded-md bg-forest/10 px-2 py-0.5 text-[11px] font-medium text-forest', className]
        .filter(Boolean)
        .join(' ')}
    >
      <svg width="14" height="14" viewBox="0 0 28 28" aria-hidden="true">
        <defs>
          <linearGradient id={gradientId} x1="0" y1="0" x2="28" y2="28" gradientUnits="userSpaceOnUse">
            <stop offset="0" stopColor="#4B90FF" />
            <stop offset="0.5" stopColor="#FF5546" />
            <stop offset="1" stopColor="#FFB800" />
          </linearGradient>
        </defs>
        <path
          fill={`url(#${gradientId})`}
          d="M14 28c0-7.732 6.268-14 14-14-7.732 0-14-6.268-14-14 0 7.732-6.268 14-14 14 7.732 0 14 6.268 14 14z"
        />
      </svg>
      Gemini
    </span>
  )
}
