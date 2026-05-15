import React from 'react';
import Header from './Header';

const ChatHeader = ({
  titleName,
  documentType,
  setDocumentType,
  proposalStatus,
  fileIcon,
  userPrompt,
  setUserPrompt,
  formExpanded,
  setFormExpanded,
  renderFormField,
  formData,
  setFormData,
}) => {
  return (
    <Header
      titleName={titleName}
      documentType={documentType}
      setDocumentType={setDocumentType}
      proposalStatus={proposalStatus}
      fileIcon={fileIcon}
      userPrompt={userPrompt}
      setUserPrompt={setUserPrompt}
      formExpanded={formExpanded}
      setFormExpanded={setFormExpanded}
      renderFormField={renderFormField}
      formData={formData}
      setFormData={setFormData}
    />
  );
};

export default ChatHeader;
