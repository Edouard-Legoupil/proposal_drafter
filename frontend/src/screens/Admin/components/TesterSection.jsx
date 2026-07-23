import React from 'react'
import SubjectPicker from './SubjectPicker'

/**
 * Reusable tester section: form and result display.
 */
export default function TesterSection({
  tester,
  setTester,
  testerResult,
  statusMessage,
  actionLoading,
  onTest,
  operationOptions,
  users,
  options,
  subjectTypeOptions = ['user', 'team', 'donor_group'],
}) {
  return (
    <>
      <form className="tester-form" onSubmit={onTest}>
        <div className="form-row">
          {subjectTypeOptions.length > 0 && (
            <label>
              Subject type
              <select
                value={tester.subjectType}
                onChange={(e) => setTester((prev) => ({ ...prev, subjectType: e.target.value, subjectId: '' }))}
              >
                {subjectTypeOptions.map((type) => (
                  <option key={type} value={type}>{type.replace('_', ' ')}</option>
                ))}
              </select>
            </label>
          )}
          <label>
            Subject
            <SubjectPicker
              subjectType={tester.subjectType}
              value={tester.subjectId}
              onChange={(val) => setTester((prev) => ({ ...prev, subjectId: val }))}
              users={users}
              options={options}
            />
          </label>
          <label>
            Operation
            <select
              value={tester.operation}
              onChange={(e) => setTester((prev) => ({ ...prev, operation: e.target.value }))}
            >
              {operationOptions.map((opt) => (
                <option key={opt.value} value={opt.value}>{opt.label}</option>
              ))}
            </select>
          </label>
        </div>
        <button type="submit" className="primary-button" disabled={actionLoading}>Run test</button>
        {statusMessage && <p className="status-msg">{statusMessage}</p>}
      </form>
      {testerResult && (
        <article className="tester-result">
          <p><strong>{testerResult.allowed ? '✅ Allowed' : '❌ Denied'}</strong> — {testerResult.reason || 'No reason provided'}</p>
          {testerResult.source && <p>Source: {testerResult.source}</p>}
          {testerResult.http_status && <p>HTTP status: {testerResult.http_status}</p>}
          {testerResult.data_scope && <p>Scope: {testerResult.data_scope}</p>}
        </article>
      )}
    </>
  )
}
