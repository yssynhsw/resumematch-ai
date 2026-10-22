import { useEffect, useState } from 'react'
import { api } from '../api'
import { useI18n } from '../context/I18nContext'
import { GenerationProgress } from './GenerationProgress'
import { GeminiMark } from './GeminiMark'
import { AiModeBadge, Alert } from './ui'

export function ApplicationEmail({ analysisId }) {
  const { t, lang } = useI18n()
  const [email, setEmail] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    let cancelled = false
    api
      .listApplicationEmails(analysisId)
      .then((rows) => {
        if (!cancelled) setEmail(rows?.[0] || null)
      })
      .catch((err) => {
        if (!cancelled) setError(err.message)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [analysisId])

  const generate = async () => {
    setBusy(true)
    setGenerating(true)
    setError('')
    try {
      setEmail(await api.createApplicationEmail(analysisId, lang))
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
      setGenerating(false)
    }
  }

  const save = async () => {
    if (!email) return
    setBusy(true)
    setError('')
    try {
      setEmail(await api.updateApplicationEmail(email.id, { subject: email.subject, body: email.body }))
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const copy = async () => {
    if (!email) return
    try {
      await navigator.clipboard.writeText(`Subject: ${email.subject}\n\n${email.body}`)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    } catch {
      setCopied(false)
    }
  }

  const mailto = email
    ? `mailto:?subject=${encodeURIComponent(email.subject)}&body=${encodeURIComponent(email.body)}`
    : '#'

  return (
    <section>
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="font-display text-xl font-semibold text-forest">{t('mail.title')}</h2>
            <GeminiMark />
          </div>
          <p className="mt-1 text-sm text-moss">{t('mail.hint')}</p>
        </div>
        <div className="no-print w-full sm:w-56">
          <button
            type="button"
            onClick={generate}
            disabled={busy}
            className="w-full rounded-xl bg-coral px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
          >
            {generating ? t('common.generating') : email ? t('mail.again') : t('mail.create')}
          </button>
          <GenerationProgress active={generating} label={t('mail.progress')} />
        </div>
      </div>
      {error && (
        <div className="mt-3">
          <Alert>{error}</Alert>
        </div>
      )}
      {loading ? (
        <p className="mt-4 text-sm text-moss">{t('common.loading')}</p>
      ) : (
        email && (
          <div className="mt-4 space-y-3">
            <p className="flex flex-wrap items-center gap-2 text-xs text-moss">
              <span>
                {email.used_interview ? t('mail.withInterview') : t('mail.withoutInterview')}
                {email.skills?.length ? ` · ${email.skills.slice(0, 4).join(', ')}` : ''}
              </span>
              <AiModeBadge mode={email.ai_mode} />
              {email.ai_mode === 'gemini' && (
                <span className="text-xs font-semibold text-forest">{t('mail.engine.gemini')}</span>
              )}
            </p>
            <label className="block text-sm font-medium text-forest">
              {t('mail.subject')}
              <input
                className="mt-1 w-full rounded-lg border border-forest/15 bg-white/80 px-3 py-2 text-sm text-forest outline-none focus:ring-2 focus:ring-moss/30"
                value={email.subject}
                onChange={(event) => setEmail({ ...email, subject: event.target.value })}
              />
            </label>
            <textarea
              rows={12}
              className="w-full rounded-xl border border-forest/15 bg-white/80 px-3 py-3 text-sm leading-relaxed text-forest outline-none focus:ring-2 focus:ring-moss/30"
              value={email.body}
              onChange={(event) => setEmail({ ...email, body: event.target.value })}
            />
            <div className="no-print flex flex-wrap gap-2">
              <button type="button" onClick={save} disabled={busy} className="rounded-lg border border-forest/20 px-3 py-1.5 text-sm font-medium text-forest">
                {t('res.save')}
              </button>
              <button type="button" onClick={copy} className="rounded-lg border border-forest/20 px-3 py-1.5 text-sm font-medium text-forest">
                {copied ? t('common.copied') : t('mail.copy')}
              </button>
              <a href={mailto} className="rounded-lg bg-forest px-3 py-1.5 text-sm font-semibold text-sand">
                {t('mail.open')}
              </a>
            </div>
          </div>
        )
      )}
    </section>
  )
}
