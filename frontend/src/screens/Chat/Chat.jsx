/**
 * Chat Component
 *
 * Thin wrapper that delegates to ChatContainer for better maintainability
 * and AI debugging. All logic is in ChatContainer.jsx.
 */

import ChatContainer from './components/ChatContainer';

export default function Chat(props) {
  return <ChatContainer {...props} />;
}
