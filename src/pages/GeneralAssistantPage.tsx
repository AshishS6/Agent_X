import AssistantChat from '../components/Assistants/AssistantChat';

const GeneralAssistantPage = () => {
  return (
    <AssistantChat
      assistantName="general"
      knowledgeBase="general"
      title="General Assistant"
      description="Ask general questions and get helpful answers."
    />
  );
};

export default GeneralAssistantPage;
