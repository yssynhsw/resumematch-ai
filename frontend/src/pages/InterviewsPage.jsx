import { useEffect, useState } from 'react'
import { api } from '../api'
import { Alert, ScoreGauge } from '../components/ui'
import { GeminiMark } from '../components/GeminiMark'
import { LiveInterview } from '../components/LiveInterview'
import { formatInterviewDate } from '../components/InterviewLog'
import { Loader, PageHeader } from '../components/motion'
import { useAuth } from '../context/AuthContext'
import { useI18n } from '../context/I18nContext'
import { Link, useLocation } from 'react-router-dom'

const INTERVIEW_KINDS = ['technical', 'soft']

function TechnicalInterviewIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden>
      <path d="M8 7 4 12l4 5M16 7l4 5-4 5M14 5l-4 14" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function SoftInterviewIcon() {
  return (
    <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.8" aria-hidden>
      <circle cx="8" cy="8" r="2.25" />
      <circle cx="16" cy="8" r="2.25" />
      <path d="M3.5 18.5c.7-2.6 2.6-4 4.5-4s3.8 1.4 4.5 4M11.5 18.5c.7-2.6 2.6-4 4.5-4s3.8 1.4 4.5 4" strokeLinecap="round" />
    </svg>
  )
}

export default function InterviewsPage() {
  const { t, locale } = useI18n()
  const { user, refreshUser } = useAuth()
  const { hash } = useLocation()
  const [cvs, setCvs] = useState([])
  const [scores, setScores] = useState({})
  const [notes, setNotes] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    Promise.all([api.listCvs(), api.listAllInterviews()])
      .then(([cvRows, interviewNotes]) => {
        if (cancelled) return
        setCvs(cvRows || [])
        setNotes(interviewNotes || [])
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

  useEffect(() => {
    if (loading) return
    const id = hash.replace('#', '')
    if (id !== 'technical' && id !== 'soft') return
    document.getElementById(id)?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }, [hash, loading])

  if (loading) return <Loader label={t('common.loading')} />

  return (
    <div className="mx-auto max-w-4xl px-4 py-10 sm:px-6">
      <PageHeader eyebrow={t('inbox.eyebrow')} title={t('inbox.title')} subtitle={t('inbox.subtitle')} />
      {user?.score != null && (
        <div className="mt-6 flex flex-wrap items-center gap-6 rounded-3xl border border-forest/10 bg-white/80 p-5 shadow-sm">
          <ScoreGauge score={user.score} size={128} />
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-moss">{t('dash.userScore')}</p>
            <p className="mt-1 max-w-sm text-sm text-forest">{t('inbox.subtitle')}</p>
          </div>
        </div>
      )}
      {error && (
        <div className="mt-6">
          <Alert>{error}</Alert>
        </div>
      )}
      {cvs.length === 0 ? (
        <p className="mt-8 text-sm text-moss">{t('inbox.empty')}</p>
      ) : (
        <ul className="mt-8 space-y-6">
          {cvs.map((cv, index) => (
            <li key={cv.id} className="overflow-hidden rounded-3xl border border-forest/10 bg-white/80 shadow-sm">
              <div className="flex flex-wrap items-center justify-between gap-4 border-b border-forest/10 bg-foam/80 px-5 py-4">
                <div>
                  <p className="font-display text-lg font-semibold text-forest">{cv.original_filename || t('inbox.cv')}</p>
                  <p className="text-sm text-moss">{t('inbox.independent')}</p>
                </div>
                <div className="flex gap-3">
                  {INTERVIEW_KINDS.map((kind) => {
                    const value = scores[`${cv.id}:${kind}`]
                    if (value == null) return null
                    return (
                      <div key={kind} className="min-w-24 rounded-2xl bg-white px-3 py-2 text-center shadow-sm">
                        <p className="text-[11px] font-semibold uppercase tracking-wide text-moss">{t(`live.type.${kind}`)}</p>
                        <p className="font-display text-2xl font-bold text-forest">{value}</p>
                      </div>
                    )
                  })}
                </div>
              </div>
              <div className="space-y-4 p-4">
                {INTERVIEW_KINDS.map((kind) => (
                  <div
                    key={kind}
                    className={`rounded-2xl border p-4 ${
                      kind === 'technical' ? 'border-moss/20 bg-foam/50' : 'border-amber/30 bg-amber/10'
                    }`}
                  >
                    <h3
                      id={index === 0 ? kind : undefined}
                      className="flex scroll-mt-24 items-center gap-3 font-semibold text-forest"
                    >
                      <span
                        className={`flex h-10 w-10 items-center justify-center rounded-xl text-white ${
                          kind === 'technical' ? 'bg-forest' : 'bg-amber text-forest'
                        }`}
                      >
                        {kind === 'technical' ? <TechnicalInterviewIcon /> : <SoftInterviewIcon />}
                      </span>
                      <GeminiMark />
                      {t(`live.type.${kind}`)}
                    </h3>
                    <LiveInterview
                      cvId={cv.id}
                      kind={kind}
                      autoStart
                      heading={false}
                      onScored={(patch) => {
                        setScores((current) => ({ ...current, [`${cv.id}:${kind}`]: patch.score }))
                        if (patch.user_score !== undefined) refreshUser()
                      }}
                    />
                  </div>
                ))}
              </div>
            </li>
          ))}
        </ul>
      )}

      <section className="mt-12">
        <h2 className="font-display text-xl font-semibold text-forest">{t('inbox.notesTitle')}</h2>
        <p className="mt-1 text-sm text-moss">{t('inbox.notesHint')}</p>
        {notes.length === 0 ? (
          <p className="mt-4 text-sm text-moss">{t('inbox.notesEmpty')}</p>
        ) : (
          <ul className="mt-4 space-y-3">
            {notes.map((item) => (
              <li key={item.id} className="rounded-2xl border border-forest/10 border-l-4 border-l-moss bg-white/80 p-4 shadow-sm">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <div>
                    <p className="font-semibold text-forest">{item.job_title}</p>
                    <p className="text-sm text-moss">
                      {item.company || t('common.companyUnknown')}
                      {' · '}
                      {formatInterviewDate(item.held_on, locale)}
                      {' · '}
                      {t(`log.format.${item.format}`)}
                    </p>
                  </div>
                  <span className="rounded-md bg-mint/40 px-2 py-0.5 text-xs font-semibold text-forest">
                    {t(`log.outcome.${item.outcome}`)}
                  </span>
                </div>
                {item.questions && <p className="mt-2 whitespace-pre-wrap text-sm text-forest">{item.questions}</p>}
                <Link to={`/resultats/${item.analysis_id}`} className="mt-3 inline-block text-sm font-medium text-coral">
                  {t('inbox.open')}
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}
