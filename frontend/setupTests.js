// setupTests.js
import { server } from './src/mocks/server'
import { beforeAll, beforeEach, afterAll, afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'

beforeAll(() => {
        window.HTMLElement.prototype.scrollIntoView = () => {}
})

beforeEach(() => {
        sessionStorage.clear()
        sessionStorage.setItem('session_id', 'test-session-123')
})

beforeAll(() => {
        server.listen({ onUnhandledRequest: 'warn' })
})

afterEach(() => {
        server.resetHandlers()
        cleanup()
        sessionStorage.clear()
})

afterAll(() => {
        server.close()
})
