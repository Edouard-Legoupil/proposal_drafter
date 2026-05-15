import React from 'react';
import Sidebar from './Sidebar';

const ChatSidebar = ({
  isMobile,
  isMobileMenuOpen,
  sidebarOpen,
  selectedSection,
  proposalTemplate,
  proposal,
  handleSidebarSectionClick,
  toKebabCase,
}) => {
  return (
    <Sidebar
      isMobile={isMobile}
      isMobileMenuOpen={isMobileMenuOpen}
      sidebarOpen={sidebarOpen}
      selectedSection={selectedSection}
      proposalTemplate={proposalTemplate}
      proposal={proposal}
      onSectionClick={handleSidebarSectionClick}
      toKebabCase={toKebabCase}
    />
  );
};

export default ChatSidebar;
