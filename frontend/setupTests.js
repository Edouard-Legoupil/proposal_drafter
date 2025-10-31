// setupTests.js
import { server } from './src/mocks/server'
import { beforeAll, beforeEach, afterAll, afterEach } from 'vitest'
import { cleanup } from '@testing-library/react'
import '@testing-library/jest-dom/vitest'

beforeAll(() => {
        // Establish API mocking before all tests.
        server.listen({ onUnhandledRequest: 'warn' })

        // Mock scrollIntoView as it is not implemented in JSDOM
        window.HTMLElement.prototype.scrollIntoView = () => {}
        HTMLFormElement.prototype.requestSubmit = function() {
                this.submit()
        }
})

beforeEach(() => {
        sessionStorage.clear()
        sessionStorage.setItem('session_id', 'test-session-123')
})

afterEach(() => {
        server.resetHandlers()
        cleanup()
        sessionStorage.clear()
})

afterAll(() => {
        server.close()
})
