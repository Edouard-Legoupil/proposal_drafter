/**
 * Sidebar Component
 *
 * Displays the navigation sidebar with proposal sections.
 */

import React from 'react';

const Sidebar = ({
  isMobile,
  isMobileMenuOpen,
  sidebarOpen,
  selectedSection,
  proposalTemplate,
  proposal,
  onSectionClick,
  toKebabCase
}) => {
  if (!((!isMobile && sidebarOpen) || (isMobile && isMobileMenuOpen))) {
    return null;
  }

  return (
    <aside>
      <ul className='Chat_sidebar' data-testid="chat-sidebar">
        <li
          className={`Chat_sidebarOption ${selectedSection === -1 ? "selectedSection" : ""}`}
          onClick={() => onSectionClick(-1)}
          data-testid="sidebar-option-proposal-prompt"
        >
          Proposal Prompt
        </li>

        {proposalTemplate ?
          proposalTemplate.sections.map((section, i) => (
            <li
              key={i}
              className={`Chat_sidebarOption ${selectedSection === i ? "selectedSection" : ""}`}
              onClick={() => onSectionClick(i)}
              data-testid={`sidebar-option-${toKebabCase(section.section_name)}`}
            >
              {section.section_name}
            </li>
          )) :
          Object.keys(proposal).map((section, i) => (
            <li
              key={i}
              className={`Chat_sidebarOption ${selectedSection === i ? "selectedSection" : ""}`}
              onClick={() => onSectionClick(i)}
              data-testid={`sidebar-option-${toKebabCase(section)}`}
            >
              {section}
            </li>
          ))
        }
      </ul>
    </aside>
  );
};

export default Sidebar;
