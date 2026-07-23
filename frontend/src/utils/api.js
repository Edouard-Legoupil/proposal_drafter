const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || '/api'

async function request(method, path, body) {
  const options = {
    method,
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' }
  }

  if (body !== undefined) {
    options.body = JSON.stringify(body)
  }

  const response = await fetch(`${API_BASE_URL}${path}`, options)
  const responseText = await response.text()
  let data = null

  if (responseText) {
    try {
      data = JSON.parse(responseText)
    } catch {
      data = responseText
    }
  }

  if (!response.ok) {
    const error = new Error(data?.detail || `Request failed with status ${response.status}`)
    error.response = { status: response.status, data }
    throw error
  }

  return { data, status: response.status }
}

export const api = {
  get: (path) => request('GET', path),
  post: (path, body) => request('POST', path, body),
  put: (path, body) => request('PUT', path, body),
  delete: (path) => request('DELETE', path)
}
