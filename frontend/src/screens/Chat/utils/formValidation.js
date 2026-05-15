/**
 * Form validation utilities for Chat component
 */

/**
 * Check which mandatory form fields are missing
 * @param {string} userPrompt - The proposal prompt
 * @param {Object} formData - Form data object with fields and their values
 * @returns {Array<string>} Array of missing field names
 */
export function getMissingFields(userPrompt, formData) {
  const missing = [];

  if (!userPrompt?.trim()) {
    missing.push("Proposal Prompt Details");
  }

  for (const label in formData) {
    const field = formData[label];
    if (field?.mandatory) {
      if (Array.isArray(field.value) && field.value.length === 0) {
        missing.push(label);
      } else if (!field.value || (typeof field.value === 'string' && !field.value.trim())) {
        missing.push(label);
      }
    }
  }

  return missing;
}
