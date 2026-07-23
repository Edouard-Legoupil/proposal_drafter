/**
 * String Utility Tests
 * Comprehensive test suite for string utility functions
 */

import { toKebabCase } from './string';

describe('String Utilities', () => {
  describe('toKebabCase', () => {
    it('should convert basic camelCase to kebab-case', () => {
      const result = toKebabCase('camelCaseString');
      expect(result).toBe('camel-case-string');
    });

    it('should convert PascalCase to kebab-case', () => {
      const result = toKebabCase('PascalCaseString');
      expect(result).toBe('pascal-case-string');
    });

    it('should handle spaces in strings', () => {
      const result = toKebabCase('String With Spaces');
      expect(result).toBe('string-with-spaces');
    });

    it('should handle mixed case and spaces', () => {
      const result = toKebabCase('MixedCase With Spaces');
      expect(result).toBe('mixed-case-with-spaces');
    });

    it('should handle special characters', () => {
      const result = toKebabCase('String_With_Underscores');
      expect(result).toBe('string-with-underscores');
    });

    it('should handle numbers in strings', () => {
      const result = toKebabCase('String123With456Numbers');
      expect(result).toBe('string123-with456-numbers');
    });

    it('should handle multiple consecutive separators', () => {
      const result = toKebabCase('String  with   multiple  spaces');
      expect(result).toBe('string-with-multiple-spaces');
    });

    it('should trim leading and trailing separators', () => {
      const result = toKebabCase('  String with spaces  ');
      expect(result).toBe('string-with-spaces');
    });

    it('should handle empty string', () => {
      const result = toKebabCase('');
      expect(result).toBe('');
    });

    it('should handle null input', () => {
      const result = toKebabCase(null);
      expect(result).toBe('');
    });

    it('should handle undefined input', () => {
      const result = toKebabCase(undefined);
      expect(result).toBe('');
    });

    it('should handle string with only special characters', () => {
      const result = toKebabCase('!@#$%^&*()');
      expect(result).toBe('');
    });

    it('should handle complex real-world example', () => {
      const result = toKebabCase('My Complex_Section Name 123!');
      expect(result).toBe('my-complex-section-name-123');
    });

    it('should be idempotent', () => {
      const input = 'TestString';
      const firstPass = toKebabCase(input);
      const secondPass = toKebabCase(firstPass);
      expect(firstPass).toBe(secondPass);
    });
  });
});
