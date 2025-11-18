export default function ChatSidebar({
  proposal,
  proposalTemplate,
  selectedSection,
  handleSidebarSectionClick,
}) {
  const toKebabCase = (str) => {
    return str.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-+|-+$/g, '');
  };

  return (
    <aside>
      <ul className="Chat_sidebar" data-testid="chat-sidebar">
        <li
          className={`Chat_sidebarOption ${
            selectedSection === -1 ? 'selectedSection' : ''
          }`}
          onClick={() => handleSidebarSectionClick(-1)}
          data-testid="sidebar-option-proposal-prompt"
        >
          Proposal Prompt
        </li>

        {(proposalTemplate
          ? proposalTemplate.sections.map((section) => section.section_name)
          : Object.keys(proposal)
        ).map((section, i) => (
          <li
            key={i}
            className={`Chat_sidebarOption ${
              selectedSection === i ? 'selectedSection' : ''
            }`}
            onClick={() => handleSidebarSectionClick(i)}
            data-testid={`sidebar-option-${toKebabCase(section)}`}
          >
            {section}
          </li>
        ))}
      </ul>
    </aside>
  );
}
