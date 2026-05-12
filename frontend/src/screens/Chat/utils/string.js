/**
 * String utility functions
 */

/**
 * Convert a string to kebab-case
 * @param {string} str - The string to convert
 * @returns {string} The kebab-case version of the string
 * @example toKebabCase("My Section Name") // => "my-section-name"
 */
export function toKebabCase(str) {
  if (!str) return '';
  return str.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
}
