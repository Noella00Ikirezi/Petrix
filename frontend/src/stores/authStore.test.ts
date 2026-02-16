import { describe, it, expect, beforeEach } from 'vitest'
import { useAuthStore } from './authStore'

describe('useAuthStore', () => {
  beforeEach(() => {
    useAuthStore.setState({
      token: null,
      user: null,
      isAuthenticated: false,
    })
  })

  it('initial state has null token, null user, isAuthenticated false', () => {
    const state = useAuthStore.getState()
    expect(state.token).toBeNull()
    expect(state.user).toBeNull()
    expect(state.isAuthenticated).toBe(false)
  })

  it('setAuth sets token, user, and isAuthenticated to true', () => {
    const mockUser = {
      id: 'user-1',
      email: 'test@example.com',
      first_name: 'John',
      last_name: 'Doe',
      role: 'admin',
    }

    useAuthStore.getState().setAuth('test-token-123', mockUser)

    const state = useAuthStore.getState()
    expect(state.token).toBe('test-token-123')
    expect(state.user).toEqual(mockUser)
    expect(state.isAuthenticated).toBe(true)
  })

  it('logout resets all state to initial values', () => {
    const mockUser = {
      id: 'user-2',
      email: 'admin@example.com',
      first_name: 'Jane',
      last_name: 'Smith',
      role: 'editor',
    }

    // First set auth
    useAuthStore.getState().setAuth('some-token', mockUser)

    // Verify it was set
    expect(useAuthStore.getState().isAuthenticated).toBe(true)

    // Now logout
    useAuthStore.getState().logout()

    const state = useAuthStore.getState()
    expect(state.token).toBeNull()
    expect(state.user).toBeNull()
    expect(state.isAuthenticated).toBe(false)
  })

  it('setAuth then logout returns to initial state', () => {
    const mockUser = {
      id: 'user-3',
      email: 'user@example.com',
      first_name: null,
      last_name: null,
      role: 'viewer',
    }

    // Set auth
    useAuthStore.getState().setAuth('jwt-token-abc', mockUser)

    // Verify authenticated
    let state = useAuthStore.getState()
    expect(state.token).toBe('jwt-token-abc')
    expect(state.user).toEqual(mockUser)
    expect(state.isAuthenticated).toBe(true)

    // Logout
    useAuthStore.getState().logout()

    // Verify reset to initial state
    state = useAuthStore.getState()
    expect(state.token).toBeNull()
    expect(state.user).toBeNull()
    expect(state.isAuthenticated).toBe(false)
  })
})
