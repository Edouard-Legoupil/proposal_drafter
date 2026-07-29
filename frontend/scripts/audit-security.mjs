import { spawnSync } from 'node:child_process'

const audit = spawnSync('npm', ['audit', '--omit=dev', '--json'], { encoding: 'utf8' })
if (!audit.stdout) {
  process.stderr.write(audit.stderr || 'npm audit produced no report\n')
  process.exit(1)
}

const report = JSON.parse(audit.stdout)
if (report.error || report.message) {
  process.stderr.write(`${audit.stdout}\n`)
  process.exit(1)
}
const vulnerabilities = report.vulnerabilities || {}
const allowedAdvisory = 'https://github.com/advisories/GHSA-qwww-vcr4-c8h2'
const unexpected = Object.entries(vulnerabilities).filter(([name, vulnerability]) => {
  if (name === 'react-router') {
    return vulnerability.via.some(
      (entry) => typeof entry !== 'object' || entry.url !== allowedAdvisory
    )
  }
  if (name === 'react-router-dom') {
    return vulnerability.via.some((entry) => entry !== 'react-router')
  }
  return true
})

if (unexpected.length) {
  process.stderr.write(`${JSON.stringify(report.vulnerabilities, null, 2)}\n`)
  process.exit(1)
}

if (Object.keys(vulnerabilities).length) {
  process.stderr.write(
    'Accepted temporary exception: GHSA-qwww-vcr4-c8h2 affects React Router RSC actions; this build is a client-only Vite SPA.\n'
  )
}
