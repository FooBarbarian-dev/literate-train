import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { vi, describe, it, expect, beforeEach } from 'vitest'

// Mock auth - admin user
let mockUser = { username: 'admin', is_admin: true }

vi.mock('../context/AuthContext', () => ({
  useAuth: () => ({
    user: mockUser,
    loading: false,
  }),
  AuthProvider: ({ children }) => children,
}))

vi.mock('../api/client', () => ({
  default: {
    get: vi.fn(),
    post: vi.fn(),
  },
}))

import client from '../api/client'
import OperationsPage from '../pages/OperationsPage'

function renderOpsPage() {
  return render(
    <BrowserRouter>
      <OperationsPage />
    </BrowserRouter>
  )
}

const mockOps = [
  {
    id: 1,
    name: 'CRIMSON-HAWK',
    description: 'Authorized pentest engagement',
    created_at: '2025-01-01T00:00:00Z',
    is_active: true,
    users: [{ username: 'operator1' }, { username: 'operator2' }],
  },
  {
    id: 2,
    name: 'SILVER-TIDE',
    description: 'CTF exercise',
    created_at: '2025-01-05T00:00:00Z',
    is_active: false,
    users: [{ username: 'operator1' }],
  },
]

describe('OperationsPage', () => {
  beforeEach(() => {
    client.get.mockReset()
    client.post.mockReset()
    mockUser = { username: 'admin', is_admin: true }
  })

  it('renders operations cards', async () => {
    client.get.mockResolvedValue({ data: mockOps })
    renderOpsPage()

    await waitFor(() => {
      expect(screen.getByText('CRIMSON-HAWK')).toBeInTheDocument()
      expect(screen.getByText('SILVER-TIDE')).toBeInTheDocument()
    })
  })

  it('shows Active badge on active operation', async () => {
    client.get.mockResolvedValue({ data: mockOps })
    renderOpsPage()

    await waitFor(() => {
      expect(screen.getByText('Active')).toBeInTheDocument()
    })
  })

  it('shows create button for admins', async () => {
    client.get.mockResolvedValue({ data: mockOps })
    renderOpsPage()

    await waitFor(() => {
      expect(screen.getByText('+ New Operation')).toBeInTheDocument()
    })
  })

  it('hides create button for non-admins', async () => {
    mockUser = { username: 'operator1', is_admin: false }
    client.get.mockResolvedValue({ data: mockOps })
    renderOpsPage()

    await waitFor(() => {
      expect(screen.getByText('CRIMSON-HAWK')).toBeInTheDocument()
    })
    expect(screen.queryByText('+ New Operation')).not.toBeInTheDocument()
  })

  it('opens create modal', async () => {
    client.get.mockResolvedValue({ data: mockOps })
    renderOpsPage()

    await waitFor(() => {
      expect(screen.getByText('+ New Operation')).toBeInTheDocument()
    })

    fireEvent.click(screen.getByText('+ New Operation'))

    await waitFor(() => {
      expect(screen.getByText('New Operation')).toBeInTheDocument()
    })
  })

  it('shows empty state', async () => {
    client.get.mockResolvedValue({ data: [] })
    renderOpsPage()

    await waitFor(() => {
      expect(screen.getByText(/no operations found/i)).toBeInTheDocument()
    })
  })
})
