/**
 * Custom hook for managing form data in the Chat component
 *
 * Handles form state, input changes, validation, and utility functions.
 */

import { useState, useCallback } from 'react';
import Select from 'react-select';
import CreatableSelect from 'react-select/creatable';
import { toKebabCase as kebabCase, getMissingFields as getMissingFieldsUtil } from '../utils';

const INITIAL_FORM_DATA = {
  "Project Draft Short name": {
    mandatory: true,
    value: ""
  },
  "Main Outcome": {
    mandatory: true,
    value: [],
    type: 'multiselect'
  },
  "Beneficiaries Profile": {
    mandatory: true,
    value: ""
  },
  "Potential Implementing Partner": {
    mandatory: false,
    value: ""
  },
  "Geographical Scope": {
    mandatory: true,
    value: ""
  },
  "Country / Location(s)": {
    mandatory: true,
    value: ""
  },
  "Budget Range": {
    mandatory: true,
    value: ""
  },
  "Duration": {
    mandatory: true,
    value: ""
  },
  "Targeted Donor": {
    mandatory: true,
    value: ""
  },
  "multiple countries": {
    mandatory: false,
    value: false
  },
  "multiple donors": {
    mandatory: false,
    value: false
  }
};

// Outcome ordering for sorted dropdown
export const OUTCOME_ORDER = [
  "OA1. Access to Territory, Registration and Documentation",
  "OA2. Status Determination",
  "OA3. Protection Policy and Law",
  "OA4. Gender-based Violence",
  "OA5. Child Protection",
  "OA6. Safety and Access to Justice",
  "OA7. Community Engagement and Participation",
  "OA8. Well-Being and Basic Needs",
  "OA9. Sustainable housing and Settlements",
  "OA10. Healthy Lives",
  "OA11. Education",
  "OA12. Clean Water, Sanitation and Hygiene",
  "OA13. Self Reliance, Economic Inclusion and Livelihoods",
  "OA14. Voluntary Repatriation and Sustainable Reintegration",
  "OA15. Resettlement and Complementary Pathways",
  "OA16. Local Integration and other Local Solutions",
  "EA17. Systems and Processes",
  "EA18. Operational support and supply chain",
  "EA19. People and culture",
  "EA20. External engagement and resource mobilization",
  "EA21. Leadership and Governance",
  "FA1. Safeguard international protection, including in the context of mixed movements.",
  "FA2. Strengthen accountability to the people we serve, especially women and children.",
  "FA3. Reinforce efforts to strengthen gender-based violence prevention, risk mitigation and response.",
  "FA4. Expand, pursue and adapt options for resettlement and complementary pathways.",
  "FA5. Mainstream development engagement in our responses from the outset, especially by building coalitions with development partners.",
  "FA6. Grow our engagement on responses and solutions for internally displaced people.",
  "FA7. Redouble efforts on statelessness so that the objectives of the #IBelong campaign are best pursued.",
  "FA8. Proactively act to mitigate the effects of the climate change crisis on displacement and in line with our protection mandate."
];

/**
 * Custom hook for form data management
 * @param {Object} initialData - Optional initial form data to override defaults
 * @returns {Object} Form state and handlers
 */
export const useFormData = (initialData = null) => {
  const [formData, setFormData] = useState(initialData || INITIAL_FORM_DATA);
  const [formExpanded, setFormExpanded] = useState(true);

  /**
   * Handles form input changes
   * @param {Event|Object} e - Event object or value
   * @param {string} label - The form field label
   */
  const handleFormInput = useCallback((e, label) => {
    setFormData(p => ({
      ...p,
      [label]: {
        ...(p[label] || {}),
        value: e?.target ? e.target.value : e
      }
    }));
  }, []);

  /**
   * Gets the list of missing mandatory fields
   * @param {string} userPrompt - The main user prompt value
   * @returns {Array} Array of missing field labels
   */
  const getMissingFields = useCallback((userPrompt = '') => {
    return getMissingFieldsUtil(userPrompt, formData);
  }, [formData]);

  /**
   * Gets sorted options for a form field based on its type
   * @param {string} label - The form field label
   * @param {Array} outcomes - Available outcomes
   * @param {Array} donors - Available donors
   * @param {Array} filteredFieldContexts - Filtered field contexts
   * @param {Array} geographicCoverages - Available geographic coverages
   * @param {Array} newDurations - Custom duration options
   * @param {Array} newBudgetRanges - Custom budget range options
   * @returns {Array} Sorted options array
   */
  const getOptions = useCallback((label, outcomes, donors, filteredFieldContexts, geographicCoverages, newDurations, newBudgetRanges) => {
    switch (label) {
      case "Main Outcome": {
        const options = outcomes.map(o => ({ value: o.id, label: o.name }));
        return options.sort((a, b) => {
          const indexA = OUTCOME_ORDER.indexOf(a.label);
          const indexB = OUTCOME_ORDER.indexOf(b.label);
          if (indexA !== -1 && indexB !== -1) return indexA - indexB;
          if (indexA !== -1) return -1;
          if (indexB !== -1) return 1;
          return a.label.localeCompare(b.label);
        });
      }
      case "Targeted Donor":
        return donors.map(d => ({ value: d.id, label: d.name })).sort((a, b) => a.label.localeCompare(b.label));
      case "Country / Location(s)":
        return filteredFieldContexts.map(fc => ({ value: fc.id, label: fc.name })).sort((a, b) => a.label.localeCompare(b.label));
      case "Geographical Scope":
        return geographicCoverages.map(gc => ({ value: gc, label: gc })).sort((a, b) => a.label.localeCompare(b.label));
      case "Duration": {
        const durationOptions = ["1 month", "3 months", "6 months", "12 months", "18 months", "24 months", "30 months", "36 months"];
        return [...durationOptions.map(d => ({ value: d, label: d })), ...newDurations.map(d => ({ value: d.id, label: d.name }))];
      }
      case "Budget Range": {
        const budgetOptions = ["50k$", "100k$", "250k$", "500k$", "1M$", "2M$", "5M$", "10M$", "15M$", "25M$"];
        return [...budgetOptions.map(b => ({ value: b, label: b })), ...newBudgetRanges.map(b => ({ value: b.id, label: b.name }))];
      }
      default:
        return [];
    }
  }, []);

  /**
   * Creates a new option for creatable select fields
   * @param {string} inputValue - The new option value
   * @param {string} label - The form field label
   * @param {Function} setNewDurations - Setter for custom durations
   * @param {Function} setNewBudgetRanges - Setter for custom budget ranges
   * @param {Function} handleFormInput - Form input handler
   */
  const handleCreate = useCallback((inputValue, label, setNewDurations, setNewBudgetRanges, handleFormInput) => {
    const newOption = { id: `new_${inputValue}`, name: inputValue };
    switch (label) {
      case "Duration":
        setNewDurations(prev => [...prev, newOption]);
        handleFormInput({ target: { value: newOption.id } }, label);
        break;
      case "Budget Range":
        setNewBudgetRanges(prev => [...prev, newOption]);
        handleFormInput({ target: { value: newOption.id } }, label);
        break;
    }
  }, []);

  /**
   * Renders a form field based on its type
   * @param {string} label - The form field label
   * @param {boolean} disabled - Whether the field is disabled
   * @param {Object} formData - Current form data
   * @param {Function} handleFormInput - Form input handler
   * @param {Array} outcomes - Available outcomes
   * @param {Array} donors - Available donors
   * @param {Array} filteredFieldContexts - Filtered field contexts
   * @param {Array} geographicCoverages - Available geographic coverages
   * @param {Array} newDurations - Custom duration options
   * @param {Array} newBudgetRanges - Custom budget range options
   * @param {Function} setNewDurations - Setter for custom durations
   * @param {Function} setNewBudgetRanges - Setter for custom budget ranges
   * @param {boolean} formDataMultipleCountries - Whether multiple countries is selected
   * @param {boolean} formDataMultipleDonors - Whether multiple donors is selected
   * @returns {JSX.Element} The rendered form field
   */
  const renderFormField = useCallback((
    label,
    disabled,
    formData,
    handleFormInput,
    outcomes,
    donors,
    filteredFieldContexts,
    geographicCoverages,
    newDurations,
    newBudgetRanges,
    setNewDurations,
    setNewBudgetRanges
  ) => {
    const field = formData[label];
    if (!field) return null;

    const fieldId = kebabCase(label);
    const isCreatableSelect = ["Duration", "Budget Range"].includes(label);
    const isSelect = ["Targeted Donor", "Country / Location(s)"].includes(label);
    const isMultiSelect = label === "Main Outcome" ||
      (label === "Targeted Donor" && formData["multiple donors"]?.value) ||
      (label === "Country / Location(s)" && formData["multiple countries"]?.value);
    const isNormalSelect = label === "Geographical Scope";

    const options = getOptions(label, outcomes, donors, filteredFieldContexts, geographicCoverages, newDurations, newBudgetRanges);

    return (
      <div key={label} className='Chat_form_inputContainer'>
        <label className='Chat_form_inputLabel' htmlFor={fieldId}>
          <div className="tooltip-container">
            {label}
            <span className={`Chat_form_input_mandatoryAsterisk ${!field.mandatory ? "hidden" : ""}`}>*</span>
            {label === "Project Draft Short name" && <span className="tooltip-text">This will be the name used to story your draft on this system</span>}
          </div>
        </label>

        {isCreatableSelect ? (
          <div data-testid={`creatable-select-container-${fieldId}`}>
            <CreatableSelect
              isClearable
              aria-label={label}
              classNamePrefix={fieldId}
              onChange={option => handleFormInput({ target: { value: option ? option.value : "" } }, label)}
              onCreateOption={inputValue => handleCreate(inputValue, label, setNewDurations, setNewBudgetRanges, handleFormInput)}
              options={options}
              value={options.find(o => o.value === field.value)}
              isDisabled={disabled}
              inputId={fieldId}
            />
          </div>
        ) : isSelect ? (
          <div data-testid={`select-container-${fieldId}`}>
            <Select
              isMulti={isMultiSelect}
              isClearable
              aria-label={label}
              classNamePrefix={fieldId}
              onChange={option => {
                if (isMultiSelect) {
                  handleFormInput({ target: { value: option ? option.map(o => o.value) : [] } }, label)
                } else {
                  handleFormInput({ target: { value: option ? option.value : "" } }, label)
                }
              }}
              options={options}
              value={isMultiSelect
                ? (Array.isArray(field.value) ? field.value.map(v => options.find(o => o.value === v)).filter(Boolean) : [])
                : options.find(o => o.value === field.value)}
              isDisabled={disabled}
              inputId={fieldId}
            />
          </div>
        ) : isMultiSelect ? (
          <div data-testid={`multiselect-container-${fieldId}`}>
            <Select
              isMulti
              aria-label={label}
              classNamePrefix={fieldId}
              onChange={options => handleFormInput({ target: { value: options ? options.map(o => o.value) : [] } }, label)}
              options={options}
              value={field.value.map(v => options.find(o => o.value === v)).filter(Boolean)}
              isDisabled={disabled}
              inputId={fieldId}
            />
          </div>
        ) : isNormalSelect ? (
          <select
            className='Chat_form_input'
            id={fieldId}
            name={fieldId}
            value={field.value}
            onChange={e => handleFormInput(e, label)}
            disabled={disabled}
            data-testid={fieldId}
          >
            <option value="" disabled>Select {label}</option>
            {options.map(option => (
              <option key={option.value} value={option.value}>{option.label}</option>
            ))}
          </select>
        ) : (
          <input
            type="text"
            className='Chat_form_input'
            id={fieldId}
            name={fieldId}
            placeholder={`Enter ${label}`}
            value={field.value}
            onChange={e => handleFormInput(e, label)}
            disabled={disabled}
            data-testid={fieldId}
          />
        )}
      </div>
    );
  }, [getOptions, handleCreate]);

  return {
    formData,
    setFormData,
    formExpanded,
    setFormExpanded,
    handleFormInput,
    getMissingFields,
    getOptions,
    handleCreate,
    renderFormField
  };
};

export default useFormData;
export { kebabCase as toKebabCase };
