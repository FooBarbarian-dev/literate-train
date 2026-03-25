import axios from 'axios'

const client = axios.create({
  baseURL: '/api',
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
})

// In-memory CSRF token storage.  The token value is returned in the login
// response body (the matching _csrf cookie is httponly so JS cannot read it
// directly).  We store it here and attach it as X-CSRF-Token on every
// mutating request so the server's double-submit cookie check passes even
// when the JWT bypass is not in effect.
let _csrfToken = null

export function setCsrfToken(token) {
  _csrfToken = token
}

export function clearCsrfToken() {
  _csrfToken = null
}

const SAFE_METHODS = new Set(['get', 'head', 'options', 'trace'])

client.interceptors.request.use((config) => {
  if (_csrfToken && !SAFE_METHODS.has(config.method?.toLowerCase())) {
    config.headers['X-CSRF-Token'] = _csrfToken
  }
  return config
})

client.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      if (!window.location.pathname.startsWith('/login')) {
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  }
)

export default client
