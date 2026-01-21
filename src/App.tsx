import { Routes, Route } from 'react-router-dom';
import DashboardLayout from './components/Layout/DashboardLayout';
import DashboardHome from './pages/DashboardHome';
import FintechAssistantPage from './pages/FintechAssistantPage';
import CodeAssistantPage from './pages/CodeAssistantPage';
import GeneralAssistantPage from './pages/GeneralAssistantPage';
import SalesAgent from './pages/SalesAgent';
import SupportAgent from './pages/SupportAgent';
import HRAgent from './pages/HRAgent';
import MarketResearchAgent from './pages/MarketResearchAgent';
import MarketingAgent from './pages/MarketingAgent';
import BlogAgent from './pages/BlogAgent';
import LeadSourcingAgent from './pages/LeadSourcingAgent';
import IntelligenceAgent from './pages/IntelligenceAgent';
import LegalAgent from './pages/LegalAgent';
import FinanceAgent from './pages/FinanceAgent';
import Workflows from './pages/Workflows';
import ActivityLogs from './pages/ActivityLogs';
import Integrations from './pages/Integrations';
import Settings from './pages/Settings';

function App() {
  return (
    <Routes>
      <Route path="/" element={<DashboardLayout />}>
        <Route index element={<DashboardHome />} />
        <Route path="assistants/fintech" element={<FintechAssistantPage />} />
        <Route path="assistants/code" element={<CodeAssistantPage />} />
        <Route path="assistants/general" element={<GeneralAssistantPage />} />
        <Route path="sales" element={<SalesAgent />} />
        <Route path="support" element={<SupportAgent />} />
        <Route path="hr" element={<HRAgent />} />
        <Route path="market-research" element={<MarketResearchAgent />} />
        <Route path="marketing" element={<MarketingAgent />} />
        <Route path="blog" element={<BlogAgent />} />
        <Route path="leads" element={<LeadSourcingAgent />} />
        <Route path="intelligence" element={<IntelligenceAgent />} />
        <Route path="legal" element={<LegalAgent />} />
        <Route path="finance" element={<FinanceAgent />} />

        {/* System Routes */}
        <Route path="workflows" element={<Workflows />} />
        <Route path="activity" element={<ActivityLogs />} />
        <Route path="data" element={<Integrations />} />
        <Route path="settings" element={<Settings />} />
      </Route>
    </Routes>
  );
}

export default App;
