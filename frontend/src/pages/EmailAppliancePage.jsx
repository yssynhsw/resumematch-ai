import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { GenerationProgress } from '../components/GenerationProgress'
import { GeminiMark } from '../components/GeminiMark'
import { AiModeBadge, Alert } from '../components/ui'
import { Loader, PageHeader } from '../components/motion'
import { useI18n } from '../context/I18nContext'

export default function EmailAppliancePage() {
  const { t, lang } = useI18n()
  const [analyses, setAnalyses] = useState([])
  const [emails, setEmails] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [busyId, setBusyId] = useState(null)
  const [savedId, setSavedId] = useState(null)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    Promise.all([api.listAnalyses({ page_size: 100 }), api.listApplicationEmails()])
      .then(([analysisPage, emailRows]) => {
        if (cancelled) return
        setAnalyses(analysisPage.results || [])
        setEmails(emailRows || [])
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
  }, [])

  const latestFor = (analysisId) => emails.find((email) => email.analysis === analysisId)

  const generate = async (analysisId) => {
    setBusyId(`gen-${analysisId}`)
    setError('')
    setSavedId(null)
    try {
      const created = await api.createApplicationEmail(analysisId, lang)
      setEmails((current) => [created, ...current.filter((email) => email.id !== created.id)])
    } catch (err) {
      setError(err.message)
    } finally {
      setBusyId(null)
    }
  }

  const changeEmail = (id, patch) => {
    setSavedId(null)
    setEmails((current) => current.map((email) => (email.id === id ? { ...email, ...patch } : email)))
  }

  const save = async (email) => {
    setBusyId(`save-${email.id}`)
    setError('')
    try {
      const saved = await api.updateApplicationEmail(email.id, { subject: email.subject, body: email.body })
      setEmails((current) => current.map((row) => (row.id === saved.id ? saved : row)))
      setSavedId(saved.id)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusyId(null)
    }
  }

  if (loading) return <Loader label={t('common.loading')} />

  return (
    <div className="mx-auto max-w-4xl px-4 py-10 sm:px-6">
      <PageHeader eyebrow="Email appliance" title="Email appliance" subtitle={t('mail.hint')}>
        <GeminiMark />
      </PageHeader>
      {error && (
        <div className="mt-6">
          <Alert>{error}</Alert>
        </div>
      )}
      {analyses.length === 0 ? (
        <p className="mt-8 text-sm text-moss">{t('mail.empty')}</p>
      ) : (
        <ul className="mt-8 space-y-3">
          {analyses.map((analysis) => {
            const email = latestFor(analysis.id)
            const mailto = email
              ? `mailto:?subject=${encodeURIComponent(email.subject)}&body=${encodeURIComponent(email.body)}`
              : ''
            return (
              <li key={analysis.id} className="rounded-2xl border border-forest/10 bg-white/70 p-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="flex flex-wrap items-center gap-2 font-semibold text-forest">
                      {analysis.job_title}
                      {email && <AiModeBadge mode={email.ai_mode} />}
                      {email && <GeminiMark />}
                      {email?.ai_mode === 'gemini' && (
                        <span className="text-xs font-semibold text-forest">{t('mail.engine.gemini')}</span>
                      )}
                    </p>
                    <p className="text-sm text-moss">{analysis.company || t('common.companyUnknown')}</p>
                  </div>
                  <div className="w-44">
                    <button
                      type="button"
                      onClick={() => generate(analysis.id)}
                      disabled={busyId === `gen-${analysis.id}`}
                      className="w-full rounded-xl bg-coral px-3 py-1.5 text-sm font-semibold text-white disabled:opacity-50"
                    >
                      {busyId === `gen-${analysis.id}` ? t('common.generating') : email ? t('mail.again') : t('mail.create')}
                    </button>
                    <GenerationProgress active={busyId === `gen-${analysis.id}`} label={t('mail.progress')} />
                  </div>
                </div>
                {email && (
                  <div className="mt-3 space-y-3">
                    <label className="block text-sm font-medium text-forest">
                      {t('mail.subject')}
                      <input
                        className="mt-1 w-full rounded-lg border border-forest/15 bg-white px-3 py-2 text-sm text-forest outline-none focus:ring-2 focus:ring-moss/30"
                        value={email.subject}
                        onChange={(event) => changeEmail(email.id, { subject: event.target.value })}
                      />
                    </label>
                    <textarea
                      rows={10}
                      className="w-full rounded-xl border border-forest/15 bg-white px-3 py-3 text-sm leading-relaxed text-forest outline-none focus:ring-2 focus:ring-moss/30"
                      value={email.body}
                      onChange={(event) => changeEmail(email.id, { body: event.target.value })}
                    />
                    <div className="flex flex-wrap items-center gap-3 text-sm">
                      <button
                        type="button"
                        onClick={() => save(email)}
                        disabled={busyId === `save-${email.id}`}
                        className="rounded-lg border border-forest/20 px-3 py-1.5 font-medium text-forest disabled:opacity-50"
                      >
                        {t('res.save')}
                      </button>
                      {savedId === email.id && <span className="text-moss">{t('mail.saved')}</span>}
                      <a href={mailto} className="font-medium text-coral">
                        {t('mail.open')}
                      </a>
                      <Link to={`/resultats/${analysis.id}`} className="font-medium text-forest">
                        {t('inbox.open')}
                      </Link>
                    </div>
                  </div>
                )}
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}
