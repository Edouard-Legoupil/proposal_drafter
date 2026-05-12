# Refactoring Implementation Guide

## Overview

This guide provides step-by-step instructions to refactor the `Chat.jsx` component into smaller, maintainable modules. The refactoring follows best practices for React component organization.

## Current State
- **File**: `frontend/src/screens/Chat/Chat.jsx`
- **Size**: 2,272 lines
- **Issues**: Too large, hard to debug, poor separation of concerns

## Target Structure

```
frontend/src/screens/Chat/
├── Chat.jsx                      (Main container, ~500 lines)
├── Chat.css                      (Styles - keep as is for now)
├── components/
│   ├── index.js                  (Barrel export)
│   ├── Modals/
│   │   ├── index.js
│   │   ├── FollowUpModal.jsx
│   │   ├── ValidationModal.jsx
│   │   ├── ProgressModal.jsx
│   │   ├── KnowledgeModal.jsx
│   │   ├── TransferModal.jsx
│   │   └── PeerReviewModal.jsx
│   ├── ProposalForm.jsx
│   ├── ProposalSections.jsx
│   ├── Sidebar.jsx
│   └── Header.jsx
├── hooks/
│   ├── index.js
│   ├── useProposal.js
│   ├── useFormData.js
│   └── usePolling.js
├── utils/
│   ├── index.js
│   ├── formValidation.js
│   └── string.js
├── types.js
└── constants.js
```

---

## Step 1: Create Directory Structure (DONE)

```bash
mkdir -p frontend/src/screens/Chat/components/Modals
mkdir -p frontend/src/screens/Chat/hooks
mkdir -p frontend/src/screens/Chat/utils
```

---

## Step 2: Extract Utility Functions (DONE)

### `utils/formValidation.js`
```javascript
/**
 * Check which mandatory form fields are missing
 * @param {string} userPrompt - The proposal prompt
 * @param {Object} formData - Form data object with fields and their values
 * @returns {Array} Array of missing field names
 */
export function getMissingFields(userPrompt, formData) {
  const missing = [];
  if (!userPrompt?.trim()) {
    missing.push("Proposal Prompt Details");
  }
  for (const label in formData) {
    const field = formData[label];
    if (field.mandatory) {
      if (Array.isArray(field.value) && field.value.length === 0) {
        missing.push(label);
      } else if (!field.value || (typeof field.value === 'string' && !field.value.trim())) {
        missing.push(label);
      }
    }
  }
  return missing;
}
```

### `utils/string.js`
```javascript
/**
 * Convert a string to kebab-case
 * @param {string} str - The string to convert
 * @returns {string} The kebab-case version
 */
export function toKebabCase(str) {
  return str.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
}
```

### `utils/index.js`
```javascript
export * from './formValidation';
export * from './string';
```

---

## Step 3: Extract FollowUpModal Component (READY)

### `components/Modals/FollowUpModal.jsx`

```jsx
/**
 * Follow-up Instructions Modal Component
 * 
 * Shown when users want to regenerate a proposal with additional instructions.
 */

import React from 'react';
import CommonButton from '../../../components/CommonButton/CommonButton';

const FollowUpModal = ({
  isOpen,
  onClose,
  onSkip,
  onSaveForLater,
  onRegenerate,
  instruction,
  setInstruction,
  regenerateCloseIcon,
  generateIcon
}) => {
  return (
    <dialog 
      open={isOpen} 
      className="Chat_regenerate" 
      style={{ 
        height: 'auto', 
        maxHeight: '80vh', 
        top: '10%', 
        width: '60vw', 
        maxWidth: '800px' 
      }} 
      data-testid="followup-modal"
    >
      <header className="Chat_regenerate_header">
        Provide Follow-up Instructions
        <img 
          src={regenerateCloseIcon} 
          alt="" 
          onClick={onClose} 
          style={{ cursor: 'pointer' }} 
        />
      </header>
      <main className="Chat_right" style={{ padding: '20px' }}>
        <p style={{ marginBottom: '15px', color: '#666' }}>
          Please provide any follow-up instructions or refinements you'd like to make.
          The AI will use the existing content as context and apply your instructions to improve it.
        </p>
        <textarea
          id="followup-instruction"
          name="followup-instruction"
          value={instruction}
          onChange={e => setInstruction(e.target.value)}
          className='Chat_inputArea_prompt'
          placeholder="e.g., 'Make the budget section more detailed', 'Focus more on gender equality', 'Revise the timeline to be more realistic'..."
          style={{ minHeight: '100px', marginBottom: '20px' }}
          data-testid="followup-instruction-input"
        />
        <div className="Chat_inputArea_buttonContainer" style={{ display: 'flex', gap: '10px', justifyContent: 'flex-end' }}>
          <CommonButton 
            onClick={onSkip} 
            label="Skip" 
            data-testid="followup-skip-button" 
          />
          <CommonButton
            onClick={onSaveForLater}
            label="Save for Later"
            data-testid="followup-save-button"
          />
          <CommonButton
            icon={generateIcon}
            onClick={onRegenerate}
            label="Regenerate Now"
            disabled={!instruction}
            data-testid="followup-regenerate-button"
          />
        </div>
      </main>
    </dialog>
  );
};

export default FollowUpModal;
```

### `components/Modals/index.js`
```javascript
export { default as FollowUpModal } from './FollowUpModal';
```

### `components/index.js`
```javascript
export * from './Modals';
```

---

## Step 4: Update Chat.jsx to Use Extracted Modal

### Add Import

```javascript
// Near other imports at the top of Chat.jsx
import { FollowUpModal } from './components';
```

### Replace Modal (Lines 1780-1824)

**Remove:** The entire dialog element (lines 1780-1824)

**Replace with:**
```javascript
{/* Follow-up Instruction Modal - Shown when regenerating a proposal */}
<FollowUpModal
  isOpen={showFollowUpModal}
  onClose={() => setShowFollowUpModal(false)}
  onSkip={() => {
    setShowFollowUpModal(false);
    setGenerateLabel("Regenerate");
  }}
  onSaveForLater={() => {
    setShowFollowUpModal(false);
    setGenerateLabel("Regenerate");
  }}
  onRegenerate={handleRegenerateWithFollowUp}
  instruction={followUpInstruction}
  setInstruction={setFollowUpInstruction}
  regenerateCloseIcon={regenerateClose}
  generateIcon={generateIcon}
/>
```

---

## Step 5: Verify Changes

1. Check that the modal still appears when clicking Regenerate
2. Check that all buttons (Skip, Save for Later, Regenerate Now) work
3. Check that the modal closes properly
4. Run tests if available

---

## Step 6: Continue with Other Modals

Repeat the same process for:
- ValidationModal
- ProgressModal
- KnowledgeModal (AssociateKnowledgeModal)
- TransferModal
- PeerReviewModal

Each modal follows the same pattern:
1. Create component file
2. Add to Modals/index.js
3. Import in Chat.jsx
4. Replace inline dialog with component

---

## Step 7: Extract Other Components

### ProposalSections.jsx
Extract the section rendering logic (lines ~2050-2200)

### Sidebar.jsx
Extract sidebar rendering (lines ~1825-1900)

### Header.jsx
Extract header with title and document type selector

### ProposalForm.jsx
Extract form fields rendering (lines ~260-500)

---

## Step 8: Extract Hooks

### useProposal.js
- proposal state
- generateLabel state
- generateLoading state
- Generation handlers

### useFormData.js
- formData state
- formExpanded state
- Form input handlers

### usePolling.js
- Polling logic for generation progress
- Progress state

---

## Step 9: Create Type Definitions

### types.js
```javascript
/** @typedef {Object} FormField */
/** @typedef {Object} ProposalSection */
/** @typedef {Object} User */
/** @typedef {Object} ReviewComment */
```

---

## Step 10: Final Cleanup

1. Remove all inline function definitions that are now in separate files
2. Ensure all imports are correct
3. Verify all functionality works
4. Run tests
5. Commit changes

---

## Estimated Results

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Chat.jsx lines | 2,272 | ~500 | -78% |
| Number of files | 1 | 15+ | +1400% |
| Component size | 2,272 | <200 each | Better |
| Debugging time | High | Low | Significant |
| Testability | Poor | Good | Significant |

---

## Quick Start

To begin the refactoring **right now**, run these commands:

```bash
# 1. Create directories (if not already done)
mkdir -p frontend/src/screens/Chat/components/Modals
mkdir -p frontend/src/screens/Chat/hooks
mkdir -p frontend/src/screens/Chat/utils

# 2. The utility files are already created

# 3. Create the FollowUpModal component (copy from above)

# 4. Update Chat.jsx imports and replace the modal
```

---

## Need Help?

The refactoring files have been created in:
- `frontend/src/screens/Chat/components/Modals/FollowUpModal.jsx`
- `frontend/src/screens/Chat/components/Modals/index.js`
- `frontend/src/screens/Chat/components/index.js`
- `frontend/src/screens/Chat/utils/formValidation.js`
- `frontend/src/screens/Chat/utils/string.js`
- `frontend/src/screens/Chat/utils/index.js`

**Next step:** Update `Chat.jsx` to import and use the `FollowUpModal` component (see Step 4 above).

Would you like me to:
1. **Apply the Chat.jsx changes** for you (replacing the modal)!
2. **Continue extracting more components** (ValidationModal, ProgressModal, etc.)
3. **Create the custom hooks** (useProposal, useFormData, etc.)
4. **Provide a git branch** with all changes ready to merge
