import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { vi, describe, it, expect, beforeEach } from 'vitest'

// Mock auth context
vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({
    user: { username: 'operator1', is_admin: false },
    loading: false,
  }),
  AuthProvider: ({ children }) => children,
}))

// Mock API client
vi.mock('../api/client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}))

import client from '../api/client'
import LogsPage from '../pages/LogsPage'

function renderLogsPage() {
  return render(
    <BrowserRouter>
      <LogsPage />
    </BrowserRouter>
  )
}

const mockLogs = {
  results: [
    {
      id: 1,
      hostname: 'WORKSTATION-01',
      ip_address: '10.0.0.5',
      command: 'whoami',
      status: 'success',
      timestamp: '2025-01-15T10:30:00Z',
      created_at: '2025-01-15T10:30:00Z',
      tags: [{ name: 'discovery', color: '#3b82f6' }],
      operator: { username: 'operator1' },
      action: 'enumeration',
    },
    {
      id: 2,
      hostname: 'DC01',
      ip_address: '10.0.0.1',
      command: 'net user /domain',
      status: 'failed',
      timestamp: '2025-01-15T11:00:00Z',
      created_at: '2025-01-15T11:00:00Z',
      tags: [],
      operator: { username: 'operator2' },
      action: 'discovery',
    },
  ],
  count: 2,
  page_size: 25,
}

describe('LogsPage', () => {
  beforeEach(() => {
    client.get.mockReset()
    client.post.mockReset()
  })

  it('shows loading spinner initially', () => {
    client.get.mockReturnValue(new Promise(() => {})) // never resolves
    renderLogsPage()
    expect(screen.getByText(/loading logs/i)).toBeInTheDocument()
  })

  it('renders log table with data', async () => {
    client.get.mockResolvedValue({ data: mockLogs })
    renderLogsPage()

    await waitFor(() => {
      expect(screen.getByText('WORKSTATION-01')).toBeInTheDocument()
      expect(screen.getByText('DC01')).toBeInTheDocument()
    })
  })

  it('shows empty state when no logs', async () => {
    client.get.mockResolvedValue({ data: { results: [], count: 0 } })
    renderLogsPage()

    await waitFor(() => {
      expect(screen.getByText(/no log entries found/i)).toBeInTheDocument()
    })
  })

  it('opens create modal on button click', async () => {
    client.get.mockResolvedValue({ data: mockLogs })
    renderLogsPage()

    await waitFor(() => {
      expect(screen.getByText('WORKSTATION-01')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('+ New Log'))

    await waitFor(() => {
      expect(screen.getByText('New Log Entry')).toBeInTheDocument()
    })
  })

  it('shows status badges with correct labels', async () => {
    client.get.mockResolvedValue({ data: mockLogs })
    renderLogsPage()

    await waitFor(() => {
      expect(screen.getByText('success')).toBeInTheDocument()
      expect(screen.getByText('failed')).toBeInTheDocument()
    })
  })

  it('shows filter inputs', async () => {
    client.get.mockResolvedValue({ data: mockLogs })
    renderLogsPage()

    await waitFor(() => {
      expect(screen.getByPlaceholderText(/filter by hostname/i)).toBeInTheDocument()
      expect(screen.getByPlaceholderText(/filter by ip/i)).toBeInTheDocument()
    })
  })

  it('shows error state on fetch failure', async () => {
    client.get.mockRejectedValue(new Error('Network error'))
    renderLogsPage()

    await waitFor(() => {
      expect(screen.getByText(/failed to fetch logs/i)).toBeInTheDocument()
    })
  })
})
