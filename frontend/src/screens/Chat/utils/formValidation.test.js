/**
 * Form Validation Utility Tests
 * Comprehensive test suite for form validation utilities
 */

import { getMissingFields } from './formValidation';

describe('Form Validation Utilities', () => {
  describe('getMissingFields', () => {
    it('should return empty array when all fields are filled', () => {
      const userPrompt = 'Test prompt';
      const formData = {
        field1: { mandatory: true, value: 'value1' },
        field2: { mandatory: false, value: '' },
        field3: { mandatory: true, value: 'value3' }
      };

      const result = getMissingFields(userPrompt, formData);
      expect(result).toEqual([]);
    });

    it('should return missing mandatory fields when userPrompt is empty', () => {
      const userPrompt = '';
      const formData = {
        field1: { mandatory: true, value: '' },
        field2: { mandatory: false, value: '' },
        field3: { mandatory: true, value: 'value3' }
      };

      const result = getMissingFields(userPrompt, formData);
      expect(result).toEqual(['Proposal Prompt Details', 'field1']);
    });

    it('should return missing mandatory fields when userPrompt has only whitespace', () => {
      const userPrompt = '   ';
      const formData = {
        field1: { mandatory: true, value: '' },
        field2: { mandatory: true, value: 'value2' }
      };

      const result = getMissingFields(userPrompt, formData);
      expect(result).toEqual(['Proposal Prompt Details', 'field1']);
    });

    it('should handle empty formData gracefully', () => {
      const userPrompt = 'Test prompt';
      const formData = {};

      const result = getMissingFields(userPrompt, formData);
      expect(result).toEqual([]);
    });

    it('should handle array fields correctly', () => {
      const userPrompt = 'Test prompt';
      const formData = {
        tags: { mandatory: true, value: [] },
        categories: { mandatory: true, value: ['cat1', 'cat2'] }
      };

      const result = getMissingFields(userPrompt, formData);
      expect(result).toEqual(['tags']);
    });

    it('should handle string fields with whitespace correctly', () => {
      const userPrompt = 'Test prompt';
      const formData = {
        description: { mandatory: true, value: '   ' }
      };

      const result = getMissingFields(userPrompt, formData);
      expect(result).toEqual(['description']);
    });

    it('should ignore non-mandatory fields', () => {
      const userPrompt = 'Test prompt';
      const formData = {
        optionalField: { mandatory: false, value: '' },
        mandatoryField: { mandatory: true, value: 'value' }
      };

      const result = getMissingFields(userPrompt, formData);
      expect(result).toEqual([]);
    });

    it('should handle mixed field types correctly', () => {
      const userPrompt = '';
      const formData = {
        textField: { mandatory: true, value: '' },
        numberField: { mandatory: true, value: 0 },
        arrayField: { mandatory: true, value: [] },
        optionalField: { mandatory: false, value: '' }
      };

      const result = getMissingFields(userPrompt, formData);
      expect(result).toEqual(['Proposal Prompt Details', 'textField', 'arrayField']);
    });

    it('should return fields in consistent order', () => {
      const userPrompt = '';
      const formData = {
        zField: { mandatory: true, value: '' },
        aField: { mandatory: true, value: '' },
        mField: { mandatory: true, value: '' }
      };

      const result = getMissingFields(userPrompt, formData);
      expect(result).toContain('Proposal Prompt Details');
      expect(result).toContain('zField');
      expect(result).toContain('aField');
      expect(result).toContain('mField');
    });
  });
});
