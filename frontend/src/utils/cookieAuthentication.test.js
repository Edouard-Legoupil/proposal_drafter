import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'

const browserRequestModules = [
  '../context/EnhancedWizardContext.jsx',
  '../screens/MetricsDashboard/InteractionMetrics/WizardUsageMetric.jsx',
  '../screens/MetricsDashboard/InteractionMetrics/ErrorAnalysisMetric.jsx',
  '../screens/MetricsDashboard/InteractionMetrics/UserActivityMetric.jsx'
]

describe('browser authentication contract', () => {
  it.each(browserRequestModules)('%s does not read or send bearer tokens', relativePath => {
    const source = readFileSync(new URL(relativePath, import.meta.url), 'utf8')

    expect(source).not.toMatch(/localStorage/)
    expect(source).not.toMatch(/Authorization/)
    expect(source).toMatch(/credentials:\s*['"]include['"]/)
  })
})
