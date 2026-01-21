import AssistantChat from '../components/Assistants/AssistantChat';

const FintechAssistantPage = () => {
  return (
    <AssistantChat
      assistantName="fintech"
      knowledgeBase="fintech"
      title="Fintech Assistant"
      description="Get answers about payment gateways, financial APIs, and fintech integrations with context from our knowledge base."
    />
  );
};

export default FintechAssistantPage;
