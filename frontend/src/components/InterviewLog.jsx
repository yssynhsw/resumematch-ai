import { useEffect, useState } from 'react'
import { api } from '../api'
import { useI18n } from '../context/I18nContext'
import { Alert } from './ui'

const FORMATS = ['phone', 'video', 'onsite']
const OUTCOMES = ['pending', 'passed', 'rejected']

const emptyForm = {
  held_on: '',
  format: 'video',
  questions: '',
  feedback: '',
  outcome: 'pending',
}

function formatIsoDate(iso, locale) {
  if (!iso) return ''
  const [year, month, day] = iso.split('-').map(Number)
  if (!year || !month || !day) return iso
  return new Date(year, month - 1, day).toLocaleDateString(locale)
}

const fieldClass =
  'mt-1 w-full rounded-lg border border-forest/15 bg-white/80 px-3 py-2 text-sm text-forest outline-none focus:ring-2 focus:ring-moss/30'

export function InterviewLog({ analysisId }) {
  const { t, locale } = useI18n()
  const [items, setItems] = useState([])
  const [form, setForm] = useState(emptyForm)
  const [editingId, setEditingId] = useState(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    api
      .listInterviews(analysisId)
      .then((data) => {
        if (!cancelled) setItems(data || [])
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

  const setField = (name, value) => setForm((current) => ({ ...current, [name]: value }))

  const reset = () => {
    setForm(emptyForm)
    setEditingId(null)
  }

  const onSubmit = async (event) => {
    event.preventDefault()
    if (!form.held_on) return
    setSaving(true)
    setError('')
    try {
      if (editingId) {
        const updated = await api.updateInterview(analysisId, editingId, form)
        setItems((list) =>
          list
            .map((item) => (item.id === editingId ? updated : item))
            .sort((a, b) => a.held_on.localeCompare(b.held_on) || a.id - b.id),
        )
      } else {
        const created = await api.createInterview(analysisId, form)
        setItems((list) =>
          [...list, created].sort((a, b) => a.held_on.localeCompare(b.held_on) || a.id - b.id),
        )
      }
      reset()
    } catch (err) {
      setError(err.message)
    } finally {
      setSaving(false)
    }
  }

  const onEdit = (item) => {
    setEditingId(item.id)
    setForm({
      held_on: item.held_on,
      format: item.format,
      questions: item.questions || '',
      feedback: item.feedback || '',
      outcome: item.outcome,
    })
  }

  const onDelete = async (item) => {
    if (!confirm(t('log.deleteConfirm'))) return
    setError('')
    try {
      await api.deleteInterview(analysisId, item.id)
      setItems((list) => list.filter((entry) => entry.id !== item.id))
      if (editingId === item.id) reset()
    } catch (err) {
      setError(err.message)
    }
  }

  return (
    <section>
      <h2 className="font-display text-xl font-semibold text-forest">{t('log.title')}</h2>
      <p className="mt-1 text-sm text-moss">{t('log.hint')}</p>
      {error && (
        <div className="mt-3">
          <Alert>{error}</Alert>
        </div>
      )}

      {loading ? (
        <p className="mt-4 text-sm text-moss">{t('common.loading')}</p>
      ) : items.length === 0 ? (
        <p className="mt-4 text-sm text-moss">{t('log.empty')}</p>
      ) : (
        <ul className="mt-4 space-y-3">
          {items.map((item) => (
            <li key={item.id} className="rounded-xl border border-forest/10 bg-white/60 p-4">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <p className="font-semibold text-forest">
                  {formatIsoDate(item.held_on, locale)}
                  <span className="ml-2 text-sm font-normal text-moss">{t(`log.format.${item.format}`)}</span>
                </p>
                <span className="rounded-md bg-mint/40 px-2 py-0.5 text-xs font-semibold text-forest">
                  {t(`log.outcome.${item.outcome}`)}
                </span>
              </div>
              {item.questions && <p className="mt-2 whitespace-pre-wrap text-sm text-forest">{item.questions}</p>}
              {item.feedback && <p className="mt-2 whitespace-pre-wrap text-sm text-moss">{item.feedback}</p>}
              <div className="no-print mt-3 flex gap-2">
                <button type="button" onClick={() => onEdit(item)} className="text-sm font-medium text-forest hover:text-coral">
                  {t('log.edit')}
                </button>
                <button type="button" onClick={() => onDelete(item)} className="text-sm font-medium text-coral">
                  {t('common.delete')}
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}

      <form onSubmit={onSubmit} className="no-print mt-5 grid gap-3 sm:grid-cols-2">
        <label className="text-sm font-medium text-forest">
          {t('log.date')}
          <input
            type="date"
            required
            className={fieldClass}
            value={form.held_on}
            onChange={(e) => setField('held_on', e.target.value)}
          />
        </label>
        <label className="text-sm font-medium text-forest">
          {t('log.format')}
          <select className={fieldClass} value={form.format} onChange={(e) => setField('format', e.target.value)}>
            {FORMATS.map((value) => (
              <option key={value} value={value}>
                {t(`log.format.${value}`)}
              </option>
            ))}
          </select>
        </label>
        <label className="text-sm font-medium text-forest sm:col-span-2">
          {t('log.questions')}
          <textarea
            rows={3}
            className={fieldClass}
            value={form.questions}
            onChange={(e) => setField('questions', e.target.value)}
          />
        </label>
        <label className="text-sm font-medium text-forest sm:col-span-2">
          {t('log.feedback')}
          <textarea
            rows={3}
            className={fieldClass}
            value={form.feedback}
            onChange={(e) => setField('feedback', e.target.value)}
          />
        </label>
        <label className="text-sm font-medium text-forest">
          {t('log.outcome')}
          <select className={fieldClass} value={form.outcome} onChange={(e) => setField('outcome', e.target.value)}>
            {OUTCOMES.map((value) => (
              <option key={value} value={value}>
                {t(`log.outcome.${value}`)}
              </option>
            ))}
          </select>
        </label>
        <div className="flex items-end gap-2">
          <button
            type="submit"
            disabled={saving}
            className="rounded-xl bg-forest px-4 py-2 text-sm font-semibold text-sand disabled:opacity-50"
          >
            {saving ? t('res.saving') : editingId ? t('log.save') : t('log.add')}
          </button>
          {editingId && (
            <button type="button" onClick={reset} className="rounded-xl border border-forest/20 px-4 py-2 text-sm text-forest">
              {t('log.cancel')}
            </button>
          )}
        </div>
      </form>
    </section>
  )
}

export function formatInterviewDate(iso, locale) {
  return formatIsoDate(iso, locale)
}
