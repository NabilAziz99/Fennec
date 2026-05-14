import { useState, useCallback } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import DashboardPageV2 from "./pages/DashboardPageV2";
import AssessmentDetailPage from "./pages/AssessmentDetailPage";
import StatusPage from "./pages/StatusPage";
import FindingsPage from "./pages/FindingsPage";
import TargetInventoryPage from "./pages/TargetInventoryPage";
import PlaceholderPage from "./pages/PlaceholderPage";
import PrivateLayout from "@/layouts/PrivateLayout";
import { PentestProvider } from "@/contexts/PentestContext";
import type { RawEventCallback } from "@/hooks/usePentestStream";
import NotFoundPage from "@/pages/NotFoundPage";

function App() {
    // Central event handler that can be accessed by components
    const [, setEventTrigger] = useState(0);
    const rawEventHandlers = useState<Set<RawEventCallback>>(() => new Set())[0];

    const handleRawEvent: RawEventCallback = useCallback((eventType, payload, sessionId) => {
        // Enhanced logging for debugging SSE events
        if (eventType === 'hypothesis_tree') {
            console.group(`[SSE] ${eventType} - Session: ${sessionId}`);
            console.log('Payload:', payload);
            const hypotheses = (payload as Record<string, unknown>)?.hypotheses;
            console.log('Hypotheses count:', hypotheses ? Object.keys(hypotheses).length : 0);
            if (hypotheses && typeof hypotheses === 'object') {
                console.log('Hypothesis IDs:', Object.keys(hypotheses));
                console.log('First hypothesis:', Object.values(hypotheses)[0]);
            }
            console.groupEnd();
        } else if (eventType === 'findings_update') {
            console.log(`[SSE] ${eventType} - Session: ${sessionId}`, payload);
        } else if (eventType === 'recon_update') {
            console.log(`[SSE] ${eventType} - Session: ${sessionId}`, payload);
        } else if (eventType.includes('error')) {
            console.error(`[SSE] ${eventType} - Session: ${sessionId}`, payload);
        } else {
            console.log(`[SSE] ${eventType} - Session: ${sessionId}`, payload);
        }

        // Trigger re-render for any subscribed components
        setEventTrigger(prev => prev + 1);

        // Call all registered handlers
        rawEventHandlers.forEach(handler => {
            try {
                handler(eventType, payload, sessionId);
            } catch (error) {
                console.error('[App] Error in raw event handler:', error);
            }
        });
    }, [rawEventHandlers]);

    return (
        <PentestProvider onRawEvent={handleRawEvent}>
            <Routes>
                {/* Root redirects to dashboard */}
                <Route path="/" element={<Navigate to="/dashboard" replace />} />

                {/* Dashboard pages */}
                <Route path="/dashboard" element={<PrivateLayout />}>
                    <Route index element={<DashboardPageV2 />} />
                    <Route path="status" element={<StatusPage />} />
                    <Route path="status/:testId" element={<AssessmentDetailPage />} />
                    <Route path="findings" element={<FindingsPage />} />
                    <Route path="targets" element={<TargetInventoryPage />} />
                    <Route path="tasks" element={<PlaceholderPage title="Tasks" />} />
                    <Route path="*" element={<NotFoundPage />} />
                </Route>

                <Route path="*" element={<NotFoundPage />} />
            </Routes>
        </PentestProvider>
    );
}

export default App;
