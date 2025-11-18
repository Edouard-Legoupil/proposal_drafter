import { useEffect, useState } from 'react';
import CreatableSelect from 'react-select/creatable';

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL;

export default function ProposalForm({
  formData,
  setFormData,
  userPrompt,
  setUserPrompt,
  associatedKnowledgeCards,
  setAssociatedKnowledgeCards,
  proposalStatus,
  form_expanded,
  setFormExpanded,
  handleGenerateClick,
  buttonEnable,
  generateLoading,
  generateLabel,
}) {
  const [donors, setDonors] = useState([]);
  const [outcomes, setOutcomes] = useState([]);
  const [fieldContexts, setFieldContexts] = useState([]);
  const [filteredFieldContexts, setFilteredFieldContexts] = useState([]);
  const [newDonors, setNewDonors] = useState([]);
  const [newOutcomes, setNewOutcomes] = useState([]);
  const [newFieldContexts, setNewFieldContexts] = useState([]);
  const [newBudgetRanges, setNewBudgetRanges] = useState([]);
  const [newDurations, setNewDurations] = useState([]);

  useEffect(() => {
    async function fetchData() {
      try {
        const [donorsRes, outcomesRes, fieldContextsRes] = await Promise.all([
          fetch(`${API_BASE_URL}/donors`, { credentials: 'include' }),
          fetch(`${API_BASE_URL}/outcomes`, { credentials: 'include' }),
          fetch(`${API_BASE_URL}/field-contexts`, { credentials: 'include' }),
        ]);

        if (donorsRes.ok) {
          const data = await donorsRes.json();
          setDonors(data.donors);
        }
        if (outcomesRes.ok) {
          const data = await outcomesRes.json();
          setOutcomes(data.outcomes);
        }
        if (fieldContextsRes.ok) {
          const data = await fieldContextsRes.json();
          const sortedFieldContexts = data.field_contexts.sort((a, b) =>
            a.name.localeCompare(b.name)
          );
          setFieldContexts(sortedFieldContexts);
          setFilteredFieldContexts(sortedFieldContexts);
        }
      } catch (error) {
        console.error('Error fetching form data:', error);
      }
    }
    fetchData();
  }, []);

  useEffect(() => {
    const scope = formData['Geographical Scope'].value;
    const filtered = scope
      ? fieldContexts.filter((fc) => fc.geographic_coverage === scope)
      : fieldContexts;
    setFilteredFieldContexts(filtered);

    const locationValue = formData['Country / Location(s)'].value;
    if (locationValue) {
      const isLocationStillValid = filtered.some(
        (fc) => fc.id === locationValue
      );
      if (fieldContexts.length > 0 && !isLocationStillValid) {
        handleFormInput({ target: { value: '' } }, 'Country / Location(s)');
      }
    }
  }, [formData['Geographical Scope'].value, fieldContexts]);

  function handleFormInput(e, label) {
    setFormData((p) => ({
      ...p,
      [label]: {
        ...formData[label],
        value: e.target.value,
      },
    }));
  }

  const toKebabCase = (str) => {
    return str.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
  };

  const renderFormField = (label, disabled) => {
    const field = formData[label];
    if (!field) return null;

    const fieldId = toKebabCase(label);

    const getOptions = (label) => {
      switch (label) {
        case 'Main Outcome':
          return [...outcomes, ...newOutcomes].map((o) => ({
            value: o.id,
            label: o.name,
          }));
        case 'Targeted Donor':
          return [...donors, ...newDonors].map((d) => ({
            value: d.id,
            label: d.name,
          }));
        case 'Country / Location(s)':
          return [...filteredFieldContexts, ...newFieldContexts].map((fc) => ({
            value: fc.id,
            label: fc.name,
          }));
        case 'Geographical Scope':
          return [
            'One Country Operation',
            'Multiple Country',
            'One Region',
            'Route-Based-Approach',
            'Area-Based-Approach',
            'Global Coverage',
          ].map((gc) => ({ value: gc, label: gc }));
        case 'Duration':
          const durationOptions = [
            '1 month',
            '3 months',
            '6 months',
            '12 months',
            '18 months',
            '24 months',
            '30 months',
            '36 months',
          ];
          return [
            ...durationOptions.map((d) => ({ value: d, label: d })),
            ...newDurations.map((d) => ({ value: d.id, label: d.name })),
          ];
        case 'Budget Range':
          const budgetOptions = [
            '50k$',
            '100k$',
            '250k$',
            '500k$',
            '1M$',
            '2M$',
            '5M$',
            '10M$',
            '15M$',
            '25M$',
          ];
          return [
            ...budgetOptions.map((b) => ({ value: b, label: b })),
            ...newBudgetRanges.map((b) => ({ value: b.id, label: b.name })),
          ];
        default:
          return [];
      }
    };

    const handleCreate = (inputValue, label) => {
      const newOption = { id: `new_${inputValue}`, name: inputValue };
      switch (label) {
        case 'Main Outcome':
          setNewOutcomes((prev) => [...prev, newOption]);
          handleFormInput(
            { target: { value: [...field.value, newOption.id] } },
            label
          );
          break;
        case 'Targeted Donor':
          setNewDonors((prev) => [...prev, newOption]);
          handleFormInput({ target: { value: newOption.id } }, label);
          break;
        case 'Country / Location(s)':
          setNewFieldContexts((prev) => [...prev, newOption]);
          handleFormInput({ target: { value: newOption.id } }, label);
          break;
        case 'Duration':
          setNewDurations((prev) => [...prev, newOption]);
          handleFormInput({ target: { value: newOption.id } }, label);
          break;
        case 'Budget Range':
          setNewBudgetRanges((prev) => [...prev, newOption]);
          handleFormInput({ target: { value: newOption.id } }, label);
          break;
      }
    };

    const isCreatableSelect = [
      'Targeted Donor',
      'Country / Location(s)',
      'Duration',
      'Budget Range',
    ].includes(label);
    const isCreatableMultiSelect = label === 'Main Outcome';
    const isNormalSelect = label === 'Geographical Scope';

    return (
      <div key={label} className="Chat_form_inputContainer">
        <label className="Chat_form_inputLabel" htmlFor={fieldId}>
          <div className="tooltip-container">
            {label}
            <span
              className={`Chat_form_input_mandatoryAsterisk ${
                !field.mandatory ? 'hidden' : ''
              }`}
            >
              *
            </span>
            {label === 'Project Draft Short name' && (
              <span className="tooltip-text">
                This will be the name used to story your draft on this system
              </span>
            )}
          </div>
        </label>

        {isCreatableSelect ? (
          <div data-testid={`creatable-select-container-${toKebabCase(label)}`}>
            <CreatableSelect
              isClearable
              aria-label={label}
              classNamePrefix={toKebabCase(label)}
              onChange={(option) =>
                handleFormInput({ target: { value: option ? option.value : '' } }, label)
              }
              onCreateOption={(inputValue) => handleCreate(inputValue, label)}
              options={getOptions(label)}
              value={getOptions(label).find((o) => o.value === field.value)}
              isDisabled={disabled}
              inputId={fieldId}
            />
          </div>
        ) : isCreatableMultiSelect ? (
          <div
            data-testid={`creatable-multiselect-container-${toKebabCase(
              label
            )}`}
          >
            <CreatableSelect
              isMulti
              aria-label={label}
              classNamePrefix={toKebabCase(label)}
              onChange={(options) =>
                handleFormInput(
                  { target: { value: options ? options.map((o) => o.value) : [] } },
                  label
                )
              }
              onCreateOption={(inputValue) => handleCreate(inputValue, label)}
              options={getOptions(label)}
              value={field.value
                .map((v) => getOptions(label).find((o) => o.value === v))
                .filter(Boolean)}
              isDisabled={disabled}
              inputId={fieldId}
            />
          </div>
        ) : isNormalSelect ? (
          <select
            className="Chat_form_input"
            id={fieldId}
            name={fieldId}
            value={field.value}
            onChange={(e) => handleFormInput(e, label)}
            disabled={disabled}
            data-testid={fieldId}
          >
            <option value="" disabled>
              Select {label}
            </option>
            {getOptions(label).map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        ) : (
          <input
            type="text"
            className="Chat_form_input"
            id={fieldId}
            name={fieldId}
            placeholder={`Enter ${label}`}
            value={field.value}
            onChange={(e) => handleFormInput(e, label)}
            disabled={disabled}
            data-testid={fieldId}
          />
        )}
      </div>
    );
  };

  return (
    <div className="Chat_inputArea">
      {renderFormField('Project Draft Short name', proposalStatus !== 'draft')}
      <textarea
        id="main-prompt"
        name="main-prompt"
        value={userPrompt}
        onChange={(e) => setUserPrompt(e.target.value)}
        placeholder="Provide as much details as possible on your initial project idea!"
        className="Chat_inputArea_prompt"
        disabled={proposalStatus !== 'draft'}
        data-testid="main-prompt"
      />

      <span
        onClick={() => proposalStatus === 'draft' && setFormExpanded((p) => !p)}
        className={`Chat_inputArea_additionalDetails ${
          form_expanded && 'expanded'
        } ${proposalStatus !== 'draft' ? 'disabled' : ''}`}
        data-testid="specify-parameters-expander"
      >
        Specify Parameters
        <img src={arrow} alt="Arrow" />
      </span>

      {form_expanded ? (
        <form className="Chat_form" data-testid="chat-form">
          <div className="Chat_form_group">
            <div className="tooltip-container">
              <h3 className="Chat_form_group_title">
                Identify Potential Interventions
              </h3>
              <span className="tooltip-text">
                surface Relevant Policies, Strategies and past Evaluation
                Recommendations
              </span>
            </div>
            {renderFormField('Main Outcome', proposalStatus !== 'draft')}
            {renderFormField('Beneficiaries Profile', proposalStatus !== 'draft')}
            {renderFormField(
              'Potential Implementing Partner',
              proposalStatus !== 'draft'
            )}
          </div>
          <div className="Chat_form_group">
            <div className="tooltip-container">
              <h3 className="Chat_form_group_title">Define Field Context</h3>
              <span className="tooltip-text">
                surface Situation Analysis and Needs Assessment
              </span>
            </div>
            {renderFormField('Geographical Scope', proposalStatus !== 'draft')}
            {renderFormField('Country / Location(s)', proposalStatus !== 'draft')}
          </div>
          <div className="Chat_form_group">
            <div className="tooltip-container">
              <h3 className="Chat_form_group_title">Tailor Funding Request</h3>
              <span className="tooltip-text">
                surface Donor profile and apply Formal Requirement for Submission
              </span>
            </div>
            {renderFormField('Budget Range', proposalStatus !== 'draft')}
            {renderFormField('Duration', proposal-status !== 'draft')}
            {renderFormField('Targeted Donor', proposalStatus !== 'draft')}
          </div>
        </form>
      ) : (
        ''
      )}

      <div className="Chat_inputArea_buttonContainer">
        <div style={{ position: 'relative' }}>
          <CommonButton
            onClick={() => setIsAssociateKnowledgeModalOpen(true)}
            label="Manage Knowledge"
            disabled={proposalStatus !== 'draft'}
            icon={knowIcon}
            data-testid="manage-knowledge-button"
          />
          {associatedKnowledgeCards.length > 0 && (
            <div
              className="associated-knowledge-display"
              data-testid="associated-knowledge-cards"
            >
              <h4>Associated Knowledge Cards:</h4>
              <ul>
                {associatedKnowledgeCards.map((card) => {
                  const title = [
                    card.title,
                    card.donor_name,
                    card.outcome_name,
                    card.field_context_name,
                  ]
                    .filter(Boolean)
                    .join(' - ');
                  return (
                    <li key={card.id}>
                      <a
                        href={`/knowledge-card/${card.id}`}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        {title}
                      </a>
                    </li>
                  );
                })}
              </ul>
            </div>
          )}
        </div>

        <div style={{ marginLeft: 'auto' }}>
          <CommonButton
            onClick={handleGenerateClick}
            icon={generateIcon}
            label={generateLabel}
            loading={generateLoading}
            loadingLabel={
              generateLabel === 'Generate'
                ? 'Generating (~ 2 mins of patience...) '
                : 'Regenerating (~ 2 mins of patience...)'
            }
            disabled={!buttonEnable || proposalStatus !== 'draft'}
            data-testid="generate-button"
          />
        </div>
      </div>
    </div>
  );
}
