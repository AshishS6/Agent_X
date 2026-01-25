import { Routes, Route, Navigate } from 'react-router-dom';
import DashboardLayout from './components/Layout/DashboardLayout';
import DashboardHome from './pages/DashboardHome';
import FintechAssistantPage from './pages/FintechAssistantPage';
import CodeAssistantPage from './pages/CodeAssistantPage';
import GeneralAssistantPage from './pages/GeneralAssistantPage';
import SalesAgent from './pages/SalesAgent';
import SalesOverview from './pages/SalesOverview';
import SupportAgent from './pages/SupportAgent';
import HRAgent from './pages/HRAgent';
import MarketResearchAgent from './pages/MarketResearchAgent';
import SiteScanAgent from './pages/SiteScanAgent';
import MarketingOverview from './pages/MarketingOverview';
import BlogAgent from './pages/BlogAgent';
import IntelligenceAgent from './pages/IntelligenceAgent';
import LegalAgent from './pages/LegalAgent';
import FinanceAgent from './pages/FinanceAgent';
import OperationsOverview from './pages/OperationsOverview';
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
        {/* Sales Domain */}
        <Route path="sales/overview" element={<SalesOverview />} />
        <Route path="sales" element={<SalesAgent />} />
        
        {/* Marketing Domain */}
        <Route path="marketing/overview" element={<MarketingOverview />} />
        <Route path="marketing" element={<Navigate to="/marketing/overview" replace />} />
        <Route path="blog" element={<BlogAgent />} />
        <Route path="market-research" element={<MarketResearchAgent />} />
        
        {/* Operations Domain */}
        <Route path="operations/overview" element={<OperationsOverview />} />
        <Route path="operations/site-scan" element={<SiteScanAgent />} />
        
        {/* Other Agents */}
        <Route path="support" element={<SupportAgent />} />
        <Route path="hr" element={<HRAgent />} />
        <Route path="leads" element={<Navigate to="/sales" replace />} />
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
