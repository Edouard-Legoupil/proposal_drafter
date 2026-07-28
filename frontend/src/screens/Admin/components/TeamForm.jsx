import { useState } from 'react'
import { Alert, Box, Button, TextField } from '@mui/material'

export default function TeamForm({ team, onSubmit, onCancel }) {
  const [name, setName] = useState(team?.name || '')
  const [description, setDescription] = useState(team?.description || '')
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  async function submit(event) {
    event.preventDefault()
    setSaving(true)
    setError('')
    try {
      await onSubmit({ name: name.trim(), description: description.trim() || null })
    } catch (submitError) {
      setError(submitError.message)
    } finally {
      setSaving(false)
    }
  }

  return (
    <Box component="form" onSubmit={submit} sx={{ display: 'grid', gap: 2, my: 2 }}>
      {error && <Alert severity="error">{error}</Alert>}
      <TextField label="Team name" value={name} onChange={(event) => setName(event.target.value)} required />
      <TextField label="Description" value={description} onChange={(event) => setDescription(event.target.value)} />
      <Box><Button type="submit" disabled={saving || !name.trim()}>{team ? 'Save' : 'Create'}</Button><Button onClick={onCancel}>Cancel</Button></Box>
    </Box>
  )
}
