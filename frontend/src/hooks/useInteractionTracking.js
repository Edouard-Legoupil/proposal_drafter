import { useCallback, useEffect, useRef, useState } from 'react'
import { useLocation } from 'react-router-dom'

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL || '/api'

const authenticatedJsonRequest = (url, options = {}) => fetch(url, {
  ...options,
  credentials: 'include',
  headers: {
    'Content-Type': 'application/json',
    ...options.headers
  }
})

function getBrowserName(userAgent) {
  if (userAgent.includes('Firefox')) return 'Firefox'
  if (userAgent.includes('SamsungBrowser')) return 'Samsung Internet'
  if (userAgent.includes('Opera') || userAgent.includes('OPR')) return 'Opera'
  if (userAgent.includes('Trident') || userAgent.includes('MSIE')) return 'Internet Explorer'
  if (userAgent.includes('Edg')) return 'Edge Chromium'
  if (userAgent.includes('Edge')) return 'Edge'
  if (userAgent.includes('Chrome')) return 'Chrome'
  if (userAgent.includes('Safari')) return 'Safari'
  return 'Unknown'
}

function getDeviceInfo() {
  const userAgent = navigator.userAgent
  const isMobile = /Android|webOS|iPhone|iPod|BlackBerry|IEMobile|Opera Mini/i.test(userAgent)
  const isTablet = /(tablet|ipad|playbook|silk)|(android(?!.*mobile))/i.test(userAgent)
  const browserVersion = userAgent.match(/(Firefox|Chrome|Safari|Edge|OPR)\/(\d+)/)
  const osVersion = userAgent.match(/(Windows NT|Mac OS X|Android|iOS) (\d+[._]\d+)/)

  let osName = 'Unknown'
  if (userAgent.includes('Windows')) osName = 'Windows'
  else if (userAgent.includes('Macintosh') || userAgent.includes('Mac OS X')) osName = 'macOS'
  else if (userAgent.includes('Android')) osName = 'Android'
  else if (userAgent.includes('iPhone') || userAgent.includes('iPad')) osName = 'iOS'
  else if (userAgent.includes('Linux')) osName = 'Linux'

  return {
    user_agent: userAgent,
    device_type: isMobile ? 'mobile' : isTablet ? 'tablet' : 'desktop',
    browser_name: getBrowserName(userAgent),
    browser_version: browserVersion?.[2] || 'Unknown',
    os_name: osName,
    os_version: osVersion?.[2]?.replace('_', '.') || 'Unknown',
    screen_width: window.screen.width,
    screen_height: window.screen.height,
    is_mobile: isMobile
  }
}

function findParentTestId(element, maxDepth = 5) {
  let current = element
  for (let depth = 0; current && depth < maxDepth; depth += 1) {
    const testId = current.getAttribute?.('data-testid')
    if (testId) return testId
    current = current.parentElement
  }
  return null
}

function getComponentName(element) {
  const component = element.getAttribute?.('data-component')
  if (component) return component
  if (typeof element.className === 'string') {
    const match = element.className.match(/\b([A-Z][a-z]+)/)
    if (match) return match[1]
  }
  return element.tagName?.toLowerCase() || 'unknown'
}

function getElementSelector(element) {
  if (element.id) return `#${element.id}`
  if (typeof element.className === 'string' && element.className.trim()) {
    return `.${element.className.trim().split(/\s+/)[0]}`
  }
  return element.tagName?.toLowerCase() || 'unknown'
}

export function useInteractionTracking(user, enabled = true) {
  const location = useLocation()
  const locationRef = useRef(location)
  const previousPathRef = useRef(location.pathname)
  const sessionRef = useRef(null)
  const mountedRef = useRef(true)
  const [sessionId, setSessionId] = useState(null)
  const userId = user?.id

  locationRef.current = location

  const sendInteraction = useCallback(async interaction => {
    if (!enabled || !sessionRef.current) return null
    try {
      const response = await authenticatedJsonRequest(`${API_BASE_URL}/interactions/log/`, {
        method: 'POST',
        body: JSON.stringify(interaction)
      })
      if (!response.ok) {
        console.error('Failed to log interaction:', await response.text())
        return null
      }
      const data = await response.json()
      return data.interaction_id || null
    } catch (error) {
      console.error('Network error logging interaction:', error)
      return null
    }
  }, [enabled])

  const baseInteraction = useCallback((interactionType, details = {}) => ({
    session_id: sessionRef.current,
    user_id: userId,
    interaction_type: interactionType,
    page_url: window.location.href,
    page_title: document.title,
    metadata: { timestamp: new Date().toISOString(), ...details.metadata },
    ...details
  }), [userId])

  const logPageView = useCallback(() => {
    if (!sessionRef.current || !enabled) return Promise.resolve(null)
    const currentLocation = locationRef.current
    return sendInteraction(baseInteraction('page_view', {
      component_name: 'page',
      element_type: 'document',
      element_test_id: 'document',
      element_text: document.title,
      event_data: {
        referrer: document.referrer,
        path: currentLocation.pathname,
        search: currentLocation.search,
        hash: currentLocation.hash
      },
      metadata: {
        screen_width: window.screen.width,
        screen_height: window.screen.height
      }
    }))
  }, [baseInteraction, enabled, sendInteraction])

  const logNavigation = useCallback((from, to) => {
    if (!sessionRef.current || !enabled) return Promise.resolve(null)
    return sendInteraction(baseInteraction('navigation', {
      component_name: 'router',
      element_type: 'navigation',
      element_test_id: 'navigation',
      element_text: `Navigated from ${from} to ${to}`,
      event_data: { from_url: from, to_url: to, navigation_type: 'route_change' }
    }))
  }, [baseInteraction, enabled, sendInteraction])

  const logClick = useCallback(event => {
    if (!sessionRef.current || !enabled) return Promise.resolve(null)
    const target = event.target
    return sendInteraction(baseInteraction('click', {
      component_name: getComponentName(target),
      element_type: target.tagName?.toLowerCase() || 'unknown',
      element_selector: getElementSelector(target),
      element_test_id: target.getAttribute?.('data-testid') || findParentTestId(target) || 'unknown',
      element_text: target.textContent?.trim() || target.value || '',
      event_data: {
        button: event.button,
        ctrlKey: event.ctrlKey,
        shiftKey: event.shiftKey,
        altKey: event.altKey,
        metaKey: event.metaKey
      },
      metadata: { clientX: event.clientX, clientY: event.clientY }
    }))
  }, [baseInteraction, enabled, sendInteraction])

  const logFormSubmission = useCallback((formElement, success = true) => {
    if (!sessionRef.current || !enabled) return Promise.resolve(null)
    return sendInteraction(baseInteraction('form_submission', {
      component_name: getComponentName(formElement),
      element_type: 'form',
      element_selector: getElementSelector(formElement),
      element_test_id: formElement.getAttribute('data-testid') || 'form',
      element_text: formElement.getAttribute('name') || 'form',
      event_data: {
        form_id: formElement.id,
        form_name: formElement.name,
        field_count: formElement.elements.length,
        success
      }
    }))
  }, [baseInteraction, enabled, sendInteraction])

  const logSearch = useCallback((query, resultsCount) => {
    if (!sessionRef.current || !enabled) return Promise.resolve(null)
    return sendInteraction(baseInteraction('search', {
      component_name: 'search',
      element_type: 'input',
      element_test_id: 'search-input',
      element_text: query,
      event_data: { search_query: query, results_count: resultsCount, search_type: 'global' }
    }))
  }, [baseInteraction, enabled, sendInteraction])

  const logWizardInteraction = useCallback(async wizardData => {
    if (!sessionRef.current || !enabled) return null
    const interactionId = await sendInteraction(baseInteraction('wizard_interaction', {
      component_name: 'wizard',
      element_type: 'wizard',
      element_test_id: 'wizard',
      element_text: `Wizard interaction: ${wizardData.action_type}`,
      event_data: { action_type: wizardData.action_type, context: wizardData.context }
    }))
    if (!interactionId) return null

    try {
      await authenticatedJsonRequest(`${API_BASE_URL}/interactions/wizard/log/`, {
        method: 'POST',
        body: JSON.stringify({
          interaction_id: interactionId,
          session_id: sessionRef.current,
          user_id: userId,
          ...wizardData
        })
      })
    } catch (error) {
      console.error('Failed to log wizard details:', error)
    }
    return interactionId
  }, [baseInteraction, enabled, sendInteraction, userId])

  const logError = useCallback((error, context = {}) => {
    if (!sessionRef.current || !enabled) return Promise.resolve(null)
    return sendInteraction(baseInteraction('error', {
      component_name: context.component || 'unknown',
      element_type: context.element_type || 'unknown',
      element_selector: context.selector || 'unknown',
      element_test_id: context.test_id || 'unknown',
      element_text: context.message || error.message || 'Unknown error',
      event_data: {
        error_type: error.name,
        error_message: error.message,
        error_code: context.code
      },
      metadata: { stack_trace: error.stack?.substring(0, 1000) },
      was_successful: false,
      error_message: error.message,
      error_stack: error.stack
    }))
  }, [baseInteraction, enabled, sendInteraction])

  const flush = useCallback(() => Promise.resolve(), [])

  useEffect(() => {
    mountedRef.current = true
    if (!enabled || !userId) return undefined
    let cancelled = false

    const startSession = async () => {
      try {
        const response = await authenticatedJsonRequest(`${API_BASE_URL}/interactions/sessions/`, {
          method: 'POST',
          body: JSON.stringify(getDeviceInfo())
        })
        if (!response.ok || cancelled) return
        const data = await response.json()
        if (cancelled) return
        sessionRef.current = data.session_id
        if (mountedRef.current) setSessionId(data.session_id)
        await logPageView()
      } catch (error) {
        if (!cancelled) console.error('Failed to start interaction session:', error)
      }
    }

    startSession()
    const handleClick = event => logClick(event)
    document.addEventListener('click', handleClick, true)

    return () => {
      cancelled = true
      mountedRef.current = false
      document.removeEventListener('click', handleClick, true)
      const endingSession = sessionRef.current
      sessionRef.current = null
      if (endingSession) {
        authenticatedJsonRequest(`${API_BASE_URL}/interactions/sessions/${endingSession}/end`, {
          method: 'PUT'
        }).catch(error => console.error('Failed to end interaction session:', error))
      }
    }
  }, [enabled, logClick, logPageView, userId])

  useEffect(() => {
    const previousPath = previousPathRef.current
    const currentPath = location.pathname
    if (previousPath !== currentPath && sessionRef.current) {
      logNavigation(previousPath, currentPath)
      logPageView()
    }
    previousPathRef.current = currentPath
  }, [location.pathname, logNavigation, logPageView])

  return {
    sessionId,
    logPageView,
    logClick,
    logFormSubmission,
    logNavigation,
    logSearch,
    logWizardInteraction,
    logError,
    flush,
    isTracking: enabled && Boolean(sessionId)
  }
}
