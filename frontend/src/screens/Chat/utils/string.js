/**
 * String utility functions
 */

/**
 * Convert a string to kebab-case
 * @param {string} str - The string to convert
 * @returns {string} The kebab-case version of the string
 * @example toKebabCase("My Section Name") // => "my-section-name"
 * @example toKebabCase("camelCaseString") // => "camel-case-string"
 * @example toKebabCase("PascalCaseString") // => "pascal-case-string"
 */
export function toKebabCase(str) {
  if (!str) return '';

  // First, insert dashes before uppercase letters (for camelCase/PascalCase)
  // but preserve numbers attached to words
  let result = str.replace(/([a-z])([A-Z])/g, '$1-$2')
                   .replace(/([0-9])([A-Z])/g, '$1-$2')
                   .replace(/([A-Z])([0-9])/g, '$1-$2');

  // Then convert to lowercase and replace all non-alphanumeric with dashes
  result = result.toLowerCase()
                 .replace(/[^a-z0-9]+/g, '-')
                 .replace(/^-+|-+$/g, '');

  return result;
}
