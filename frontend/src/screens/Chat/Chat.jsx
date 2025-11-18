import './Chat.css';

import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import Base from '../../components/Base/Base';
import CommonButton from '../../components/CommonButton/CommonButton';
import MultiSelectModal from '../../components/MultiSelectModal/MultiSelectModal';
import AssociateKnowledgeModal from '../../components/AssociateKnowledgeModal/AssociateKnowledgeModal';
import PdfUploadModal from '../../components/PdfUploadModal/PdfUploadModal';
import ProposalForm from './components/ProposalForm';
import ProposalDisplay from './components/ProposalDisplay';
import ChatSidebar from './components/ChatSidebar';

import fileIcon from '../../assets/images/chat-titleIcon.svg';
import resultsIcon from '../../assets/images/Chat_resultsIcon.svg';
import word_icon from '../../assets/images/word.svg';
import excel_icon from '../../assets/images/excel.svg';

const API_BASE_URL = import.meta.env.VITE_BACKEND_URL;

export default function Chat(props) {
  const navigate = useNavigate();

  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  useEffect(() => {
    function handleResize() {
      setIsMobile(window.innerWidth < 768);
    }

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const [titleName, setTitleName] = useState(
    props?.title ?? 'Generate Draft Proposal'
  );

  const [userPrompt, setUserPrompt] = useState('');

  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isPeerReviewModalOpen, setIsPeerReviewModalOpen] = useState(false);
  const [isAssociateKnowledgeModalOpen, setIsAssociateKnowledgeModalOpen] =
    useState(false);
  const [isPdfUploadModalOpen, setIsPdfUploadModalOpen] = useState(false);
  const [users, setUsers] = useState([]);
  const [selectedUsers, setSelectedUsers] = useState([]);
  const [associatedKnowledgeCards, setAssociatedKnowledgeCards] = useState([]);

  const [form_expanded, setFormExpanded] = useState(true);
  const [formData, setFormData] = useState({
    'Project Draft Short name': {
      mandatory: true,
      value: '',
    },
    'Main Outcome': {
      mandatory: true,
      value: [],
      type: 'multiselect',
    },
    'Beneficiaries Profile': {
      mandatory: true,
      value: '',
    },
    'Potential Implementing Partner': {
      mandatory: false,
      value: '',
    },
    'Geographical Scope': {
      mandatory: true,
      value: '',
    },
    'Country / Location(s)': {
      mandatory: true,
      value: '',
    },
    'Budget Range': {
      mandatory: true,
      value: '',
    },
    Duration: {
      mandatory: true,
      value: '',
    },
    'Targeted Donor': {
      mandatory: true,
      value: '',
    },
  });

  const [buttonEnable, setButtonEnable] = useState(false);
  useEffect(() => {
    if (userPrompt) {
      setButtonEnable(true);

      for (const property in formData) {
        const field = formData[property];
        if (field.mandatory) {
          if (Array.isArray(field.value) && field.value.length === 0) {
            setButtonEnable(false);
            return;
          } else if (!field.value) {
            setButtonEnable(false);
            return;
          }
        }
      }
    } else setButtonEnable(false);
  }, [userPrompt, formData]);

  const [proposal, setProposal] = useState({});
  const [generateLoading, setGenerateLoading] = useState(false);
  const [generateLabel, setGenerateLabel] = useState('Generate');
  const isGenerating = useRef(false);

  useEffect(() => {
    if (sidebarOpen) {
      if (titleName === 'Generate Draft Proposal')
        setTitleName('Generate Draft Proposal');
    }
  }, [sidebarOpen]);

  useEffect(() => {
    if (
      !generateLoading &&
      proposal &&
      Object.values(proposal).every((section) => section.content)
    ) {
      topRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  }, [generateLoading, proposal]);

  useEffect(() => {
    const pollStatus = async () => {
      const proposalId = sessionStorage.getItem('proposal_id');
      if (!proposalId || !generateLoading) return;

      try {
        const response = await fetch(
          `${API_BASE_URL}/proposals/${proposalId}/status`,
          { credentials: 'include' }
        );
        if (response.ok) {
          const data = await response.json();
          if (data.status !== 'generating_sections') {
            setGenerateLoading(false);
            setGenerateLabel('Regenerate');
            const sectionState = {};
            Object.entries(data.generated_sections).forEach(([key, value]) => {
              sectionState[key] = {
                content: value,
                open: true,
              };
            });
            setProposal(sectionState);
          }
        }
      } catch (error) {
        console.error('Error polling for status:', error);
        setGenerateLoading(false);
      }
    };

    const intervalId = setInterval(pollStatus, 5000);

    return () => clearInterval(intervalId);
  }, [generateLoading]);

  async function fetchAndAssociateKnowledgeCards() {
    const donorId = formData['Targeted Donor'].value;
    const outcomeIds = formData['Main Outcome'].value;
    const fieldContextId = formData['Country / Location(s)'].value;

    const fetchPromises = [];

    if (donorId && !donorId.startsWith('new_')) {
      fetchPromises.push(
        fetch(`${API_BASE_URL}/knowledge-cards?donor_id=${donorId}`, {
          credentials: 'include',
        })
          .then((res) => (res.ok ? res.json() : Promise.resolve({ knowledge_cards: [] })))
          .then((data) =>
            data.knowledge_cards.length > 0 ? data.knowledge_cards[0] : null
          )
      );
    }

    if (fieldContextId && !fieldContextId.startsWith('new_')) {
      fetchPromises.push(
        fetch(`${API_BASE_URL}/knowledge-cards?field_context_id=${fieldContextId}`, {
          credentials: 'include',
        })
          .then((res) => (res.ok ? res.json() : Promise.resolve({ knowledge_cards: [] })))
          .then((data) =>
            data.knowledge_cards.length > 0 ? data.knowledge_cards[0] : null
          )
      );
    }

    if (outcomeIds && outcomeIds.length > 0) {
      const validOutcomeIds = outcomeIds.filter((id) => !id.startsWith('new_'));
      if (validOutcomeIds.length > 0) {
        const queryParams = new URLSearchParams();
        validOutcomeIds.forEach((id) => queryParams.append('outcome_id', id));
        fetchPromises.push(
          fetch(`${API_BASE_URL}/knowledge-cards?${queryParams.toString()}`, {
            credentials: 'include',
          })
            .then((res) => (res.ok ? res.json() : Promise.resolve({ knowledge_cards: [] })))
            .then((data) => data.knowledge_cards)
        );
      }
    }

    try {
      const results = await Promise.all(fetchPromises);
      const newAssociatedCards = results.flat().filter(Boolean);

      const combinedCards = [...associatedKnowledgeCards, ...newAssociatedCards];
      const uniqueAssociatedCards = Array.from(
        new Map(combinedCards.map((card) => [card.id, card])).values()
      );

      setAssociatedKnowledgeCards(uniqueAssociatedCards);
      return uniqueAssociatedCards;
    } catch (error) {
      console.error('Error auto-associating knowledge cards:', error);
      return associatedKnowledgeCards;
    }
  }

  async function handleGenerateClick() {
    setGenerateLoading(true);
    setFormExpanded(false);

    try {
      const finalAssociatedCards = await fetchAndAssociateKnowledgeCards();
      const updatedFormData = {
        ...Object.fromEntries(
          Object.entries(formData).map((item) => [item[0], item[1].value])
        ),
      };

      const createNewOption = async (endpoint, value) => {
        let body = { name: value.substring(4) };
        if (endpoint === 'field-contexts') {
          body.geographic_coverage = formData['Geographical Scope'].value;
          body.category = 'Country';
        }

        const response = await fetch(`${API_BASE_URL}/${endpoint}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(body),
          credentials: 'include',
        });

        if (!response.ok) {
          const errorData = await response.json();
          console.error('Failed to create new option:', errorData);
          throw new Error(`Failed to create new ${endpoint}`);
        }

        const data = await response.json();
        return data.id;
      };

      if (
        updatedFormData['Targeted Donor'] &&
        updatedFormData['Targeted Donor'].startsWith('new_')
      ) {
        updatedFormData['Targeted Donor'] = await createNewOption(
          'donors',
          updatedFormData['Targeted Donor']
        );
      }
      if (
        updatedFormData['Country / Location(s)'] &&
        updatedFormData['Country / Location(s)'].startsWith('new_')
      ) {
        updatedFormData['Country / Location(s)'] = await createNewOption(
          'field-contexts',
          updatedFormData['Country / Location(s)']
        );
      }
      if (updatedFormData['Main Outcome']) {
        updatedFormData['Main Outcome'] = await Promise.all(
          updatedFormData['Main Outcome'].map((o) =>
            o.startsWith('new_') ? createNewOption('outcomes', o) : o
          )
        );
      }

      const response = await fetch(`${API_BASE_URL}/create-session`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_description: userPrompt,
          form_data: updatedFormData,
          associated_knowledge_cards: finalAssociatedCards,
        }),
        credentials: 'include',
      });

      if (!response.ok) {
        throw new Error('Failed to create a new session.');
      }

      const data = await response.json();

      sessionStorage.setItem('session_id', data.session_id);
      sessionStorage.setItem('proposal_id', data.proposal_id);
      if (data.proposal_template) {
        setProposalTemplate(data.proposal_template);
        sessionStorage.setItem(
          'proposal_template',
          JSON.stringify(data.proposal_template)
        );
      }

      const sectionState = {};
      if (data.proposal_template && data.proposal_template.sections) {
        data.proposal_template.sections.forEach((section) => {
          sectionState[section.section_name] = {
            content: '',
            open: true,
          };
        });
      }

      setProposal(sectionState);
      setSidebarOpen(true);

      const generateResponse = await fetch(
        `${API_BASE_URL}/generate-proposal-sections/${data.session_id}`,
        {
          method: 'POST',
          credentials: 'include',
        }
      );

      if (!generateResponse.ok) {
        throw new Error('Failed to start proposal generation.');
      }
    } catch (error) {
      console.error('Error during proposal generation:', error);
      setGenerateLoading(false);
      setGenerateLabel('Generate');
    }
  }

  const [selectedSection, setSelectedSection] = useState(-1);
  const topRef = useRef();
  const proposalRef = useRef();
  function handleSidebarSectionClick(sectionIndex) {
    setSelectedSection(sectionIndex);

    if (sectionIndex === -1 && topRef?.current)
      topRef?.current?.scroll({ top: 0, behavior: 'smooth' });
    else if (proposalRef.current)
      proposalRef?.current?.children[sectionIndex]?.scrollIntoView({
        behavior: 'smooth',
      });
  }

  const [isCopied, setIsCopied] = useState(false);
  async function handleCopyClick(section, content) {
    setSelectedSection(section);
    setIsCopied(true);

    const timeoutId = setTimeout(() => {
      setIsCopied(false);
    }, [3000]);

    return () => clearTimeout(timeoutId);
  }

  const dialogRef = useRef();
  const [regenerateInput, setRegenerateInput] = useState('');
  const handleRegenerateIconClick = (sectionIndex) => {
    setSelectedSection(sectionIndex);
    dialogRef.current.showModal();
  };
  const [regenerateSectionLoading, setRegenerateSectionLoading] =
    useState(false);
  async function handleRegenerateButtonClick(ip = regenerateInput) {
    setRegenerateSectionLoading(true);
    const sectionName = proposalTemplate
      ? proposalTemplate.sections[selectedSection].section_name
      : Object.keys(proposal)[selectedSection];

    const response = await fetch(
      `${API_BASE_URL}/regenerate_section/${sessionStorage.getItem(
        'proposal_id'
      )}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionStorage.getItem('session_id'),
          section: sectionName,
          concise_input: ip,
          form_data: Object.fromEntries(
            Object.entries(formData).map((item) => [item[0], item[1].value])
          ),
          project_description: userPrompt,
        }),
        credentials: 'include',
      }
    );

    if (response.ok) {
      const data = await response.json();
      setProposal((p) => ({
        ...p,
        [sectionName]: {
          open: p[sectionName].open,
          content: data.generated_text,
        },
      }));
    } else if (response.status === 401) {
      sessionStorage.setItem(
        'session_expired',
        'Session expired. Please login again.'
      );
      navigate('/login');
    } else console.log('Error: ', response);

    setRegenerateInput('');
    if (typeof dialogRef.current?.close === 'function') {
      dialogRef.current.close();
    }
    setRegenerateSectionLoading(false);

    if (isEdit) setIsEdit(false);
  }

  function handleExpanderToggle(section) {
    const sectionName = proposalTemplate
      ? proposalTemplate.sections[section].section_name
      : Object.keys(proposal)[section];
    setProposal((p) => {
      return {
        ...p,
        [sectionName]: {
          content: p[sectionName].content,
          open: !p[sectionName].open,
        },
      };
    });
  }

  const [isEdit, setIsEdit] = useState(false);
  const [editorContent, setEditorContent] = useState('');
  const [proposalTemplate, setProposalTemplate] = useState(null);
  async function handleEditClick(section) {
    if (!isEdit) {
      setSelectedSection(section);
      setIsEdit(true);
      setEditorContent(Object.values(proposal)[section].content);
    } else {
      const sectionName = proposalTemplate
        ? proposalTemplate.sections[selectedSection].section_name
        : Object.keys(proposal)[selectedSection];

      try {
        const response = await fetch(`${API_BASE_URL}/update-section-content`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            proposal_id: sessionStorage.getItem('proposal_id'),
            section: sectionName,
            content: editorContent,
          }),
          credentials: 'include',
        });

        if (!response.ok) {
          throw new Error('Failed to save the section content.');
        }

        setProposal((p) => ({
          ...p,
          [sectionName]: {
            ...p[sectionName],
            content: editorContent,
          },
        }));
      } catch (error) {
        console.error('Error saving section:', error);
      } finally {
        setIsEdit(false);
      }
    }
  }

  const [proposalStatus, setProposalStatus] = useState('draft');
  const [contributionId, setContributionId] = useState('');
  const [statusHistory, setStatusHistory] = useState([]);
  const [reviews, setReviews] = useState([]);

  async function handleSaveContributionId() {
    const response = await fetch(
      `${API_BASE_URL}/proposals/${sessionStorage.getItem(
        'proposal_id'
      )}/save-contribution-id`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ contribution_id: contributionId }),
        credentials: 'include',
      }
    );

    if (response.ok) {
      alert('Contribution ID saved!');
    } else {
      console.error('Failed to save Contribution ID');
      alert('Failed to save Contribution ID.');
    }
  }

  async function getPeerReviews() {
    if (sessionStorage.getItem('proposal_id')) {
      const response = await fetch(
        `${API_BASE_URL}/proposals/${sessionStorage.getItem(
          'proposal_id'
        )}/peer-reviews`,
        {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
        }
      );
      if (response.ok) {
        const data = await response.json();
        setReviews(data.reviews);
      } else if (response.status === 403) {
        setReviews([]);
      }
    }
  }

  async function getStatusHistory() {
  }

  async function getContent() {
    if (sessionStorage.getItem('proposal_id')) {
      const response = await fetch(
        `${API_BASE_URL}/load-draft/${sessionStorage.getItem('proposal_id')}`,
        {
          method: 'GET',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
        }
      );

      if (response.ok) {
        const data = await response.json();

        sessionStorage.setItem('proposal_id', data.proposal_id);
        sessionStorage.setItem('session_id', data.session_id);

        setUserPrompt(data.project_description);

        setFormData((p) =>
          Object.fromEntries(
            Object.entries(data.form_data).map((field) => [
              field[0],
              {
                value: field[1],
                mandatory: p[field[0]].mandatory,
              },
            ])
          )
        );

        const sectionState = {};
        Object.entries(data.generated_sections).forEach(([key, value]) => {
          sectionState[key] = {
            content: value,
            open: true,
          };
        });
        setProposal(sectionState);

        if (data.associated_knowledge_cards) {
          setAssociatedKnowledgeCards(data.associated_knowledge_cards);
        }

        setProposalStatus(data.status);
        setContributionId(data.contribution_id || '');
        setSidebarOpen(true);
        getStatusHistory();
        if (data.status === 'pre_submission' || data.status === 'in_review') {
          getPeerReviews();
        }

        const storedTemplate = sessionStorage.getItem('proposal_template');
        if (storedTemplate) {
          setProposalTemplate(JSON.parse(storedTemplate));
        }
      } else if (response.status === 401) {
        sessionStorage.setItem(
          'session_expired',
          'Session expired. Please login again.'
        );
        navigate('/login');
      }
    }
  }

  async function handleExport(format) {
    const proposalId = sessionStorage.getItem('proposal_id');

    if (!proposalId || proposalId === 'undefined') {
      setErrorMessage(
        'No draft available to export. Please create or load a draft first.'
      );
      return;
    }

    const response = await fetch(
      `${API_BASE_URL}/generate-document/${sessionStorage.getItem(
        'proposal_id'
      )}?format=${format}`,
      {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
      }
    );

    if (response.ok) {
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = 'proposal.docx';
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1];
        }
      }

      const blob = await response.blob();
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();

      setTimeout(() => URL.revokeObjectURL(link.href), 1000);
    } else if (response.status === 401) {
      sessionStorage.setItem(
        'session_expired',
        'Session expired. Please login again.'
      );
      navigate('/login');
    } else
      throw new Error(`Download failed: ${response.status} ${response.statusText}`);
  }

  async function handleExportTables() {
    const proposalId = sessionStorage.getItem('proposal_id');

    if (!proposalId || proposalId === 'undefined') {
      setErrorMessage(
        'No draft available to export. Please create or load a draft first.'
      );
      return;
    }

    const response = await fetch(
      `${API_BASE_URL}/generate-tables/${sessionStorage.getItem('proposal_id')}`,
      {
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
      }
    );

    if (response.ok) {
      const contentDisposition = response.headers.get('Content-Disposition');
      let filename = 'proposal-tables.xlsx';
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename="?([^"]+)"?/);
        if (filenameMatch && filenameMatch[1]) {
          filename = filenameMatch[1];
        }
      }

      const blob = await response.blob();
      const link = document.createElement('a');
      link.href = URL.createObjectURL(blob);
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();

      setTimeout(() => URL.revokeObjectURL(link.href), 1000);
    } else if (response.status === 401) {
      sessionStorage.setItem(
        'session_expired',
        'Session expired. Please login again.'
      );
      navigate('/login');
    } else
      throw new Error(`Download failed: ${response.status} ${response.statusText}`);
  }

  async function handleRevert(status) {
    const response = await fetch(
      `${API_BASE_URL}/proposals/${sessionStorage.getItem(
        'proposal_id'
      )}/revert-to-status/${status}`,
      {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
      }
    );

    if (response.ok) {
      await getContent();
    } else {
      console.error('Failed to revert status');
    }
  }

  async function handleSaveResponse(reviewId, responseText) {
    const response = await fetch(
      `${API_BASE_URL}/peer-reviews/${reviewId}/response`,
      {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ author_response: responseText }),
        credentials: 'include',
      }
    );

    if (response.ok) {
      getPeerReviews();
    } else {
      console.error('Failed to save response');
    }
  }

  async function handleSetStatus(status) {
    const response = await fetch(
      `${API_BASE_URL}/proposals/${sessionStorage.getItem('proposal_id')}/status`,
      {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: status }),
        credentials: 'include',
      }
    );

    if (response.ok) {
      await getContent();
    } else {
      console.error('Failed to update status');
    }
  }

  async function handleSubmit() {
    setIsPdfUploadModalOpen(true);
  }

  async function handlePdfUpload(file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(
      `${API_BASE_URL}/proposals/${sessionStorage.getItem(
        'proposal_id'
      )}/upload-submitted-pdf`,
      {
        method: 'POST',
        body: formData,
        credentials: 'include',
      }
    );

    if (response.ok) {
      await getContent();
    } else {
      console.error('Failed to upload PDF');
    }
    setIsPdfUploadModalOpen(false);
  }

  async function handleSubmitForPeerReview({ selectedUsers, deadline }) {
    const reviewers = selectedUsers.map((user_id) => ({ user_id, deadline }));
    const response = await fetch(
      `${API_BASE_URL}/proposals/${sessionStorage.getItem(
        'proposal_id'
      )}/submit-for-review`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ reviewers }),
        credentials: 'include',
      }
    );

    if (response.ok) {
      setProposalStatus('in_review');
      await getContent();
      setIsPeerReviewModalOpen(false);
    } else if (response.status === 401) {
      sessionStorage.setItem(
        'session_expired',
        'Session expired. Please login again.'
      );
      navigate('/login');
    }
  }

  function handleAssociateKnowledgeConfirm(selectedCards) {
    setAssociatedKnowledgeCards(selectedCards);
  }

  return (
    <Base>
      <div
        className={`Chat ${isMobile && isMobileMenuOpen ? 'mobile-menu-open' : ''}`}
        data-testid="chat-container"
      >
        <MultiSelectModal
          isOpen={isPeerReviewModalOpen}
          onClose={() => setIsPeerReviewModalOpen(false)}
          options={users}
          selectedOptions={selectedUsers}
          onSelectionChange={setSelectedUsers}
          onConfirm={handleSubmitForPeerReview}
          title="Select Users for Peer Review"
          showDeadline={true}
        />
        <AssociateKnowledgeModal
          isOpen={isAssociateKnowledgeModalOpen}
          onClose={() => setIsAssociateKnowledgeModalOpen(false)}
          onConfirm={handleAssociateKnowledgeConfirm}
          donorId={formData['Targeted Donor'].value}
          outcomeId={formData['Main Outcome'].value}
          fieldContextId={formData['Country / Location(s)'].value}
          initialSelection={associatedKnowledgeCards}
        />
        <PdfUploadModal
          isOpen={isPdfUploadModalOpen}
          onClose={() => setIsPdfUploadModalOpen(false)}
          onConfirm={handlePdfUpload}
        />
        {((!isMobile && sidebarOpen) || (isMobile && isMobileMenuOpen)) && (
          <ChatSidebar
            proposal={proposal}
            proposalTemplate={proposalTemplate}
            selectedSection={selectedSection}
            handleSidebarSectionClick={handleSidebarSectionClick}
          />
        )}

        <main className="Chat_right" ref={topRef} data-testid="chat-main">
          <button
            className="Chat_menuButton"
            onClick={() => setIsMobileMenuOpen((p) => !p)}
            data-testid="mobile-menu-button"
          >
            <i className="fa-solid fa-bars"></i>
          </button>
          {proposalStatus !== 'submitted' ? (
            <>
              <div className="Dashboard_top">
                <div className="Dashboard_label" data-testid="chat-title">
                  <img className="Dashboard_label_fileIcon" src={fileIcon} />
                  {titleName}
                </div>
              </div>

              <ProposalForm
                formData={formData}
                setFormData={setFormData}
                userPrompt={userPrompt}
                setUserPrompt={setUserPrompt}
                associatedKnowledgeCards={associatedKnowledgeCards}
                setAssociatedKnowledgeCards={setAssociatedKnowledgeCards}
                proposalStatus={proposalStatus}
                form_expanded={form_expanded}
                setFormExpanded={setFormExpanded}
                handleGenerateClick={handleGenerateClick}
                buttonEnable={buttonEnable}
                generateLoading={generateLoading}
                generateLabel={generateLabel}
              />
            </>
          ) : (
            ''
          )}

          {sidebarOpen ? (
            <>
              <div className="Dashboard_top">
                <div className="Dashboard_label">
                  <img className="Dashboard_label_fileIcon" src={resultsIcon} />
                  Results
                </div>

                {Object.keys(proposal).length > 0 ? (
                  <div className="Chat_exportButtons">
                    <button
                      type="button"
                      onClick={() => handleExport('docx')}
                      data-testid="export-word-button"
                    >
                      <img src={word_icon} />
                      Download Document
                    </button>
                    <button
                      type="button"
                      onClick={() => handleExportTables()}
                      data-testid="export-excel-button"
                    >
                      <img src={excel_icon} />
                      Download Tables
                    </button>
                    <div className="Chat_workflow_status_container">
                      <div className="workflow-stage-box">
                        <span className="workflow-stage-label">
                          Workflow Stage
                        </span>
                        <div className="workflow-badges">
                          {['draft', 'in_review', 'pre_submission', 'submitted'].map(
                            (status) => {
                              const statusDetails = {
                                draft: {
                                  text: 'Drafting',
                                  className: 'status-draft',
                                  message: 'Initial drafting stage - Author + AI',
                                },
                                in_review: {
                                  text: 'Peer Review',
                                  className: 'status-review',
                                  message:
                                    'Wait while proposal sent for quality review to other users',
                                },
                                pre_submission: {
                                  text: 'Pre-Submission',
                                  className: 'status-submission',
                                  message:
                                    'Edit to address the comments from all your reviewers',
                                },
                                submitted: {
                                  text: 'Submitted',
                                  className: 'status-submitted',
                                  message:
                                    'Non editable Record of Initial version as submitted to donor',
                                },
                              };
                              const isActive = proposalStatus === status;
                              const isClickable =
                                (proposalStatus === 'draft' &&
                                  (status === 'in_review' || status === 'submitted')) ||
                                (proposalStatus === 'in_review' &&
                                  (status === 'pre_submission' || status === 'draft')) ||
                                (proposalStatus === 'pre_submission' &&
                                  status === 'submitted');

                              return (
                                <div key={status} className="status-badge-container">
                                  <button
                                    type="button"
                                    title={statusDetails[status].message}
                                    className={`status-badge ${
                                      statusDetails[status].className
                                    } ${isActive ? 'active' : 'inactive'}`}
                                    onClick={() => {
                                      if (
                                        status === 'in_review' &&
                                        proposalStatus === 'draft'
                                      )
                                        setIsPeerReviewModalOpen(true);
                                      if (
                                        status === 'draft' &&
                                        proposalStatus === 'in_review'
                                      )
                                        handleSetStatus('draft');
                                      if (
                                        status === 'submitted' &&
                                        (proposalStatus === 'pre_submission' ||
                                          proposalStatus === 'draft')
                                      )
                                        handleSubmit();
                                    }}
                                    disabled={!isClickable && !isActive}
                                    data-testid={`workflow-status-badge-${status}`}
                                  >
                                    {statusDetails[status].text}
                                  </button>
                                  {statusHistory.includes(status) && !isActive && (
                                    <button
                                      className="revert-btn"
                                      onClick={() => handleRevert(status)}
                                      data-testid={`revert-button-${status}`}
                                    >
                                      Revert
                                    </button>
                                  )}
                                </div>
                              );
                            }
                          )}
                        </div>
                        {proposalStatus === 'pre_submission' && (
                          <button
                            className="revert-btn"
                            onClick={() => handleRevert('draft')}
                            data-testid="revert-to-draft-button"
                          >
                            Revert to Draft
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ) : (
                  ''
                )}
              </div>

              {proposalStatus === 'submitted' && (
                <div className="contribution-id-container">
                  <label htmlFor="contribution-id">Contribution ID:</label>
                  <p>
                    Only submitted proposal with a confirmed ContributionID are
                    counted as approved
                  </p>
                  <input
                    type="text"
                    id="contribution-id"
                    value={contributionId}
                    onChange={(e) => setContributionId(e.target.value)}
                    data-testid="contribution-id-input"
                  />
                  <CommonButton
                    onClick={handleSaveContributionId}
                    label="Save ID"
                    data-testid="save-contribution-id-button"
                  />
                </div>
              )}

              <ProposalDisplay
                proposal={proposal}
                proposalTemplate={proposalTemplate}
                generateLoading={generateLoading}
                isEdit={isEdit}
                selectedSection={selectedSection}
                isCopied={isCopied}
                editorContent={editorContent}
                setEditorContent={setEditorContent}
                handleEditClick={handleEditClick}
                setIsEdit={setIsEdit}
                handleCopyClick={handleCopyClick}
                handleRegenerateIconClick={handleRegenerateIconClick}
                handleExpanderToggle={handleExpanderToggle}
                proposalStatus={proposalStatus}
                reviews={reviews}
                handleSaveResponse={handleSaveResponse}
              />
            </>
          ) : (
            ''
          )}
        </main>

        <dialog
          ref={dialogRef}
          className="Chat_regenerate"
          data-testid="regenerate-dialog"
        >
          <header className="Chat_regenerate_header">
            Regenerate —{' '}
            {proposalTemplate
              ? proposalTemplate.sections[selectedSection]?.section_name
              : Object.keys(proposal)[selectedSection]}
            <img
              src={regenerateClose}
              onClick={() => {
                setRegenerateSectionLoading(false);
                setRegenerateInput('');
                dialogRef.current.close();
              }}
              data-testid="regenerate-dialog-close-button"
            />
          </header>

          <main className="Chat_right">
            <section className="Chat_inputArea">
              <textarea
                id="regenerate-prompt"
                name="regenerate-prompt"
                value={regenerateInput}
                onChange={(e) => setRegenerateInput(e.target.value)}
                className="Chat_inputArea_prompt"
                data-testid="regenerate-dialog-prompt-input"
              />

              <div
                className="Chat_inputArea_buttonContainer"
                style={{ marginTop: '20px' }}
              >
                <CommonButton
                  icon={generateIcon}
                  onClick={() => handleRegenerateButtonClick()}
                  label="Regenerate"
                  loading={regenerateSectionLoading}
                  loadingLabel="Regenerating"
                  disabled={!regenerateInput}
                  data-testid="regenerate-dialog-regenerate-button"
                />
              </div>
            </section>
          </main>
        </dialog>
      </div>
    </Base>
  );
}
