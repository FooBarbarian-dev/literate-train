import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { vi, describe, it, expect, beforeEach } from 'vitest'

// Mock the auth context
const mockLogin = vi.fn()
const mockLogout = vi.fn()
let mockUser = null

vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({
    user: mockUser,
    loading: false,
    login: mockLogin,
    logout: mockLogout,
  }),
  AuthProvider: ({ children }) => children,
}))

// Mock navigate
const mockNavigate = vi.fn()
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom')
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  }
})

import LoginPage from '../pages/LoginPage'

function renderLogin() {
  return render(
    <BrowserRouter>
      <LoginPage />
    </BrowserRouter>
  )
}

describe('LoginPage', () => {
  beforeEach(() => {
    mockUser = null
    mockLogin.mockReset()
    mockNavigate.mockReset()
  })

  it('renders login form with username and password fields', () => {
    renderLogin()
    expect(screen.getByLabelText(/username/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /sign in/i })).toBeInTheDocument()
  })

  it('renders CLIO branding', () => {
    renderLogin()
    expect(screen.getByText('CLIO')).toBeInTheDocument()
    expect(screen.getByText(/security operations logger/i)).toBeInTheDocument()
  })

  it('shows error message on failed login', async () => {
    mockLogin.mockRejectedValue({
      response: { data: { message: 'Invalid credentials' } },
    })

    renderLogin()

    fireEvent.change(screen.getByLabelText(/username/i), {
      target: { value: 'baduser' },
    })
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: 'badpass' },
    })
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(screen.getByText('Invalid credentials')).toBeInTheDocument()
    })
  })

  it('navigates to /logs on successful login', async () => {
    mockLogin.mockResolvedValue({ user: { username: 'admin' } })

    renderLogin()

    fireEvent.change(screen.getByLabelText(/username/i), {
      target: { value: 'admin' },
    })
    fireEvent.change(screen.getByLabelText(/password/i), {
      target: { value: 'password' },
    })
    fireEvent.click(screen.getByRole('button', { name: /sign in/i }))

    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/logs', { replace: true })
    })
  })

  it('redirects when already authenticated', () => {
    mockUser = { username: 'admin' }
    renderLogin()
    expect(mockNavigate).toHaveBeenCalledWith('/logs', { replace: true })
  })

  it('shows authorized personnel footer', () => {
    renderLogin()
    expect(screen.getByText(/authorized personnel only/i)).toBeInTheDocument()
  })
})
