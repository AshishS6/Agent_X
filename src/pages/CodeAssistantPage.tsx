import AssistantChat from '../components/Assistants/AssistantChat';

const CodeAssistantPage = () => {
  return (
    <AssistantChat
      assistantName="code"
      knowledgeBase="code"
      title="Code Assistant"
      description="Get help with programming, code examples, and technical questions."
    />
  );
};

export default CodeAssistantPage;
