import { useMemo } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { ChevronDown, Code, DollarSign, Sparkles } from 'lucide-react';
import clsx from 'clsx';
import AssistantChat from '../components/Assistants/AssistantChat';

type AssistantType = 'fintech' | 'code' | 'general';

const ASSISTANTS: Record<AssistantType, { label: string; description: string; icon: any }> = {
  fintech: {
    label: 'Fintech Assistant',
    description:
      'Get answers about payment gateways, financial APIs, and fintech integrations with context from our knowledge base.',
    icon: DollarSign,
  },
  code: {
    label: 'Code Assistant',
    description: 'Get help with programming, code examples, and technical questions.',
    icon: Code,
  },
  general: {
    label: 'General Assistant',
    description: 'Ask general questions and get helpful answers.',
    icon: Sparkles,
  },
};

const DEFAULT_ASSISTANT: AssistantType = 'general';

const AssistantsPage = () => {
  const navigate = useNavigate();
  const params = useParams();

  const assistantType = useMemo<AssistantType>(() => {
    const raw = (params as any)?.assistantType as string | undefined;
    if (raw === 'fintech' || raw === 'code' || raw === 'general') return raw;
    return DEFAULT_ASSISTANT;
  }, [params]);

  const config = ASSISTANTS[assistantType];
  const Icon = config.icon;

  const headerSlot = (
    <div className="flex items-center gap-3 min-w-0">
      <div className="flex items-center gap-3 min-w-0">
        <div className="w-9 h-9 rounded-lg bg-gray-800 border border-gray-700 flex items-center justify-center shrink-0">
          <Icon className="w-4 h-4 text-gray-200" />
        </div>
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-500">Assistant</span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-green-500/10 text-green-400 border border-green-500/20">
              Ready
            </span>
          </div>
          <div className="text-sm font-medium text-white truncate">{config.label}</div>
        </div>
      </div>
    </div>
  );

  const composerLeftSlot = (
    <div className="relative">
      <select
        value={assistantType}
        onChange={(e) => navigate(`/assistants/${e.target.value}`)}
        className={clsx(
          'appearance-none bg-gray-800/50 border border-gray-700 hover:border-gray-600 text-gray-200 text-sm rounded-lg px-3 py-3 pr-9',
          'focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500'
        )}
        aria-label="Select assistant"
      >
        <option value="general">General</option>
        <option value="fintech">Fintech</option>
        <option value="code">Code</option>
      </select>
      <ChevronDown className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-gray-400" size={14} />
    </div>
  );

  const { introTitle, introDescription, samplePrompts } = useMemo(() => {
    if (assistantType === 'fintech') {
      return {
        introTitle: 'Ask about OPEN and Zwitch—products, onboarding, or integrations.',
        introDescription:
          'I can help you understand payment flows, API onboarding, common integration patterns, and practical troubleshooting for launches.',
        samplePrompts: [
          'How do I onboard to Zwitch as a business? What documents are needed?',
          'Help me design a payment gateway integration using Zwitch APIs (webhooks, retries, idempotency).',
          'What’s the best way to set up reconciliation for payouts and refunds?',
          'Explain OPEN’s connected banking approach for payouts and vendor payments—where does it fit?',
          'What should my UAT checklist look like before going live with payments?',
        ],
      };
    }
    if (assistantType === 'code') {
      return {
        introTitle: 'Ask for code help—debugging, architecture, or examples.',
        introDescription:
          'Share your goal or error and I’ll help you fix it, improve the implementation, or draft clean code snippets.',
        samplePrompts: [
          'Debug this React state bug: my component re-renders endlessly—what’s the likely cause?',
          'Write a TypeScript function to validate a webhook payload with a signature.',
          'Help me design a REST API for blog documents (CRUD + versioning).',
          'How should I structure a Go service with handlers, repos, and models?',
          'Suggest a clean pagination pattern for React lists with caching.',
        ],
      };
    }
    return {
      introTitle: 'Ask anything—writing, planning, analysis, or quick answers.',
      introDescription:
        'Tell me what you’re trying to achieve and I’ll help you get there quickly—step-by-step or as a draft you can copy.',
      samplePrompts: [
        'Summarize this meeting transcript into action items.',
        'Rewrite this paragraph to be clearer and more professional.',
        'Create a test plan for a new feature I’m shipping.',
        'Help me decide between two approaches and explain trade-offs.',
        'Draft a short product announcement email.',
      ],
    };
  }, [assistantType]);

  return (
    <AssistantChat
      assistantName={assistantType}
      knowledgeBase={assistantType}
      title={config.label}
      description={config.description}
      headerSlot={headerSlot}
      composerLeftSlot={composerLeftSlot}
      introTitle={introTitle}
      introDescription={introDescription}
      samplePrompts={samplePrompts}
      showHeader={false}
    />
  );
};

export default AssistantsPage;

