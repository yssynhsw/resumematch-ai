import { useEffect, useState } from 'react'
import { api } from '../api'
import { GeminiMark } from './GeminiMark'
import { Alert } from './ui'
import { useI18n } from '../context/I18nContext'

function ScoreRing({ score = 0, size = 88 }) {
  const value = Math.max(0, Math.min(100, Number(score) || 0))
  const radius = 32
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (value / 100) * circumference
  const color = value >= 75 ? '#3a8f6e' : value >= 50 ? '#d4a017' : '#14352b'
  return (
    <div className="relative shrink-0" style={{ width: size, height: size }} aria-hidden>
      <svg viewBox="0 0 80 80" className="h-full w-full -rotate-90">
        <circle cx="40" cy="40" r={radius} fill="none" stroke="#d8e8df" strokeWidth="7" />
        <circle
          cx="40"
          cy="40"
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="7"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
        />
      </svg>
      <div className="absolute inset-0 flex items-center justify-center font-display text-xl font-bold text-forest">{value}</div>
    </div>
  )
}

const CATEGORY_STYLES = {
  technique: 'bg-leaf/15',
  comportementale: 'bg-mint/40',
  motivation: 'bg-amber/20',
  lacune: 'bg-coral/15 text-coral',
  environnement: 'bg-sky-100 text-forest',
}

export function LiveInterview({ cvId, kind = 'technical', onScored, autoStart = false, heading = true }) {
  const { t, lang } = useI18n()
  const [attempt, setAttempt] = useState(null)
  const [answers, setAnswers] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    api
      .getApplicantInterview(cvId, kind)
      .then(async (data) => {
        if (cancelled) return
        if (autoStart) {
          const started = await api.startApplicantInterview(cvId, lang, kind)
          if (cancelled) return
          const scoredNow = started.attempt?.state === 'scored'
          setAttempt(started.attempt)
          setAnswers(
            scoredNow
              ? started.attempt.answers || []
              : (started.attempt?.questions || []).map(() => ''),
          )
          onScored?.({
            score: scoredNow ? started.attempt.score : null,
            user_score: started.user_score,
          })
          return
        }
        setAttempt(data.attempt)
        setAnswers(data.attempt?.answers || [])
        if (data.attempt?.state === 'scored') onScored?.({ score: data.attempt.score })
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
  }, [cvId, autoStart, lang, kind])

  const start = async () => {
    setBusy(true)
    setError('')
    try {
      const data = await api.startApplicantInterview(cvId, lang, kind)
      setAttempt(data.attempt)
      setAnswers(data.attempt.questions.map(() => ''))
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const submit = async (event) => {
    event.preventDefault()
    setBusy(true)
    setError('')
    try {
      const data = await api.submitApplicantInterview(cvId, answers, kind)
      setAttempt(data.attempt)
      setAnswers(data.attempt.answers || answers)
      onScored?.({ score: data.attempt.score, user_score: data.user_score })
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const questions = attempt?.questions || []
  const scored = attempt?.state === 'scored'

  return (
    <section>
      {heading && (
        <>
          <div className="flex items-center gap-2">
            <h2 className="font-display text-xl font-semibold text-forest">{t('live.title')}</h2>
            <GeminiMark />
          </div>
          <p className="mt-1 text-sm text-moss">{t('live.hint')}</p>
        </>
      )}
      {error && (
        <div className="mt-3">
          <Alert>{error}</Alert>
        </div>
      )}
      {loading ? (
        <p className="mt-4 text-sm text-moss">{t('common.loading')}</p>
      ) : !attempt ? (
        <button
          type="button"
          onClick={start}
          disabled={busy}
          className="no-print mt-4 rounded-xl bg-coral px-4 py-2 text-sm font-semibold text-white disabled:opacity-50"
        >
          {busy ? t('live.starting') : t('live.start')}
        </button>
      ) : (
        <form onSubmit={submit} className="mt-4 space-y-4">
          {scored && (
            <div className="flex flex-wrap items-center gap-4 rounded-2xl border border-mint bg-white p-4 shadow-sm">
              <ScoreRing score={attempt.score} />
              <div className="min-w-48 flex-1">
                <p className="text-sm text-forest">{t('live.saved')}</p>
                <div className="mt-2 h-2 overflow-hidden rounded-full bg-foam">
                  <div className="h-full rounded-full bg-leaf" style={{ width: `${Math.max(0, Math.min(100, attempt.score || 0))}%` }} />
                </div>
                {attempt.summary && (
                  <p className="mt-2 text-sm text-moss">{attempt.summary.replace(/^.*\n/, '')}</p>
                )}
              </div>
            </div>
          )}
          {scored && Array.isArray(attempt.courses) && attempt.courses.length > 0 && (
            <div className="rounded-2xl border border-forest/10 bg-white p-4 shadow-sm">
              <h3 className="font-display text-lg font-semibold text-forest">{t('live.courses')}</h3>
              <p className="mt-1 text-sm text-moss">{t('live.coursesHint')}</p>
              <ul className="mt-3 grid gap-3 sm:grid-cols-2">
                {attempt.courses.map((course, index) => {
                  const safeUrl = typeof course?.url === 'string' && course.url.startsWith('https://')
                  return (
                    <li key={`${index}-${course?.skill || ''}-${course?.title || ''}`} className="rounded-2xl border border-mint bg-foam/60 p-3">
                      <p className="text-xs font-semibold uppercase tracking-wide text-moss">{course.skill}</p>
                      {safeUrl ? (
                        <a
                          href={course.url}
                          target="_blank"
                          rel="noreferrer noopener"
                          className="mt-1 block text-sm font-semibold text-forest underline decoration-mint underline-offset-2"
                        >
                          {course.title}
                        </a>
                      ) : (
                        <p className="mt-1 text-sm font-semibold text-forest">{course.title}</p>
                      )}
                      {course.reason ? <p className="mt-1 text-xs leading-relaxed text-moss">{course.reason}</p> : null}
                    </li>
                  )
                })}
              </ul>
            </div>
          )}
          {questions.map((question, index) => {
            const points = attempt.question_scores?.find((item) => item.index === index)
            return (
              <div key={`${index}-${question.question}`} className="overflow-hidden rounded-2xl border border-forest/10 bg-white shadow-sm">
                {scored && (
                  <div className="h-1.5 bg-foam">
                    <div
                      className="h-full bg-leaf"
                      style={{ width: `${Math.max(0, Math.min(100, points?.score ?? 0))}%` }}
                    />
                  </div>
                )}
                <div className="p-4">
                <div className="flex flex-wrap items-start justify-between gap-3">
                  <p className="text-sm font-medium text-forest">
                    <span className="mr-2 inline-flex h-7 w-7 items-center justify-center rounded-full bg-forest font-display text-xs font-bold text-sand">
                      {String(index + 1).padStart(2, '0')}
                    </span>
                    {question.question}
                  </p>
                  <span className={`rounded-full px-2 py-0.5 text-xs font-semibold ${CATEGORY_STYLES[question.category] || 'bg-forest/10'}`}>
                    {t(`iv.cat.${question.category}`)}
                  </span>
                </div>
                <div className="mt-3 space-y-2">
                  {scored && (
                    <div className="flex items-center gap-3">
                      <ScoreRing score={points?.score ?? 0} size={52} />
                      <p className="text-sm font-semibold text-forest">{t('live.questionScore', { n: points?.score ?? 0 })}</p>
                    </div>
                  )}
                  {scored && points?.comment && (
                    <p className="text-sm text-moss">
                      <strong className="text-forest">{t('live.errors')}{t('common.colon')}</strong>
                      {points.comment}
                    </p>
                  )}
                  {scored && points?.focus && (
                    <p className="text-sm text-moss">
                      <strong className="text-forest">{t('live.workOn')}{t('common.colon')}</strong>
                      {points.focus}
                    </p>
                  )}
                  <textarea
                    required
                    minLength={8}
                    rows={4}
                    className="w-full rounded-xl border border-forest/15 bg-white px-3 py-2 text-sm text-forest outline-none focus:ring-2 focus:ring-moss/30"
                    placeholder={t('live.placeholder')}
                    value={answers[index] || ''}
                    onChange={(event) =>
                      setAnswers((current) => {
                        const next = questions.map((_, i) => current[i] || '')
                        next[index] = event.target.value
                        return next
                      })
                    }
                  />
                  {scored && question.answer_tips && (
                    <p className="text-sm text-moss">
                      <strong className="text-forest">{t('iv.tips')}{t('common.colon')}</strong>
                      {question.answer_tips}
                    </p>
                  )}
                </div>
                </div>
              </div>
            )
          })}
          <button
            type="submit"
            disabled={busy || questions.length === 0}
            className="no-print rounded-xl bg-forest px-4 py-2 text-sm font-semibold text-sand disabled:opacity-50"
          >
            {busy ? t('live.scoring') : scored ? t('live.update') : t('live.submit')}
          </button>
        </form>
      )}
    </section>
  )
}
