import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Terminal,
    AlertTriangle,
    CheckCircle,
    Loader2,
} from 'lucide-react';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { usePentestContext } from '@/contexts/PentestContext';
import { targetApi, credentialApi } from '@/services/api';
import type { Target, Credential } from '@/types';

interface TestDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
}

export function TestDialog({ open, onOpenChange }: TestDialogProps) {
    const navigate = useNavigate();

    // Form state
    const [selectedTargetId, setSelectedTargetId] = useState('');
    const [selectedCredentialId, setSelectedCredentialId] = useState('');
    const [method, setMethod] = useState<'turbo' | 'balanced' | 'deep'>('balanced');
    const [frequency, setFrequency] = useState<string>('none');
    const [localError, setLocalError] = useState('');

    // Data state
    const [targets, setTargets] = useState<Target[]>([]);
    const [credentials, setCredentials] = useState<Credential[]>([]);
    const [targetsLoading, setTargetsLoading] = useState(false);
    const [credentialsLoading, setCredentialsLoading] = useState(false);

    const {
        startStream,
        sessionId,
        connectionStatus,
        testStatus,
        error: streamError,
        reset,
    } = usePentestContext();

    const isLoading =
        connectionStatus === 'connecting' ||
        (connectionStatus === 'connected' && testStatus === 'running');

    // Navigate when sessionId is set and we're connected (not on error)
    // Only fires while the dialog is open — prevents yanking the user back to
    // the status page when they navigate elsewhere with an active session.
    useEffect(() => {
        if (!open) return;
        if (sessionId && connectionStatus === 'connected' && testStatus === 'running') {
            const timer = setTimeout(() => {
                onOpenChange(false);
                navigate(`/dashboard/status/${sessionId}`);
            }, 500);
            return () => clearTimeout(timer);
        }
    }, [open, sessionId, connectionStatus, testStatus, navigate, onOpenChange]);

    // Reset state when dialog opens
    useEffect(() => {
        if (open) {
            setSelectedTargetId('');
            setSelectedCredentialId('');
            setMethod('balanced');
            setFrequency('none');
            setLocalError('');
            setCredentials([]);
            reset();
        }
    }, [open, reset]);

    // Load targets when dialog opens
    useEffect(() => {
        if (!open) return;
        setTargetsLoading(true);
        targetApi
            .list()
            .then(setTargets)
            .catch((err) => console.error('Failed to load targets:', err))
            .finally(() => setTargetsLoading(false));
    }, [open]);

    // Load credentials when target changes
    useEffect(() => {
        if (!selectedTargetId) {
            setCredentials([]);
            setSelectedCredentialId('');
            return;
        }
        setCredentialsLoading(true);
        setSelectedCredentialId('');
        credentialApi
            .list(selectedTargetId)
            .then(setCredentials)
            .catch((err) => {
                console.error('Failed to load credentials:', err);
                setCredentials([]);
            })
            .finally(() => setCredentialsLoading(false));
    }, [selectedTargetId]);

    const handleStartTest = async () => {
        if (!selectedTargetId) {
            setLocalError('Please select a target domain');
            return;
        }

        const target = targets.find((t) => t.id === selectedTargetId);
        if (!target) {
            setLocalError('Selected target not found');
            return;
        }

        let targetUrl = target.domain;
        if (!targetUrl.startsWith('http://') && !targetUrl.startsWith('https://')) {
            targetUrl = `https://${targetUrl}`;
        }

        setLocalError('');
        // Pass the user's dialog selections through to the job creation request.
        // Without these, selected credentials / method / frequency were silently
        // dropped and the job ended up with credential_id=null every time.
        const freq = frequency && frequency !== 'none'
            ? (frequency as 'daily' | 'weekly' | 'monthly')
            : null;
        await startStream(
            targetUrl,
            `Assessment - ${target.name}`,
            undefined,
            undefined,
            {
                target_id: target.id,
                credential_id: selectedCredentialId || undefined,
                method,
                frequency: freq,
            },
        );
    };

    const error = localError || streamError;
    const status =
        connectionStatus === 'connecting'
            ? 'Initializing...'
            : connectionStatus === 'connected' && sessionId
                ? 'Test started! Redirecting...'
                : '';
    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-lg">
                <DialogHeader>
                    <DialogTitle>Configure Continuous Testing</DialogTitle>
                    <DialogDescription>
                        Set up the parameters of your penetration test which will be used to guide the AI agents.
                    </DialogDescription>
                </DialogHeader>

                <div className="flex flex-col gap-4 pt-2">
                    {/* Target Domain */}
                    <div>
                        <label className="text-sm font-medium mb-1.5 block">
                            Target Domain
                        </label>
                        <Select
                            value={selectedTargetId}
                            onValueChange={(val) => {
                                setSelectedTargetId(val);
                                setLocalError('');
                            }}
                            disabled={isLoading}
                        >
                            <SelectTrigger>
                                <SelectValue
                                    placeholder={
                                        targetsLoading
                                            ? 'Loading targets...'
                                            : 'Select a target'
                                    }
                                />
                            </SelectTrigger>
                            <SelectContent>
                                {targets.map((t) => (
                                    <SelectItem key={t.id} value={t.id}>
                                        {t.name}
                                        <span className="ml-2 text-xs text-muted-foreground">
                                            ({t.domain})
                                        </span>
                                    </SelectItem>
                                ))}
                                {targets.length === 0 && !targetsLoading && (
                                    <div className="px-2 py-3 text-center text-sm text-muted-foreground">
                                        No targets found. Add one first.
                                    </div>
                                )}
                            </SelectContent>
                        </Select>
                    </div>

                    {/* Authentication Credentials */}
                    <div>
                        <label className="text-sm font-medium mb-1.5 block">
                            Authentication Credentials{' '}
                            <span className="text-muted-foreground font-normal">(Optional)</span>
                        </label>
                        <Select
                            value={selectedCredentialId}
                            onValueChange={setSelectedCredentialId}
                            disabled={isLoading || !selectedTargetId}
                        >
                            <SelectTrigger>
                                <SelectValue
                                    placeholder={
                                        !selectedTargetId
                                            ? 'Select a target first'
                                            : credentialsLoading
                                                ? 'Loading credentials...'
                                                : 'None'
                                    }
                                />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="none">None</SelectItem>
                                {credentials.map((c) => (
                                    <SelectItem key={c.id} value={c.id}>
                                        {c.name}
                                        <span className="ml-2 text-xs text-muted-foreground">
                                            ({c.username})
                                        </span>
                                    </SelectItem>
                                ))}
                            </SelectContent>
                        </Select>
                    </div>

                    {/* Method */}
                    <div>
                        <label className="text-sm font-medium mb-1.5 block">Method</label>
                        <div className="grid grid-cols-3 gap-2">
                            {(['turbo', 'balanced', 'deep'] as const).map((m) => (
                                <button
                                    key={m}
                                    type="button"
                                    onClick={() => setMethod(m)}
                                    disabled={isLoading}
                                    className={`flex flex-col items-center gap-1 rounded-md border p-3 text-sm transition-colors ${
                                        method === m
                                            ? 'border-primary bg-primary/10 text-primary'
                                            : 'border-border hover:bg-muted/50 text-muted-foreground'
                                    } disabled:opacity-50 disabled:cursor-not-allowed`}
                                >
                                    <span className="font-medium capitalize">{m}</span>
                                    <span className="text-[10px] text-muted-foreground">
                                        {m === 'turbo'
                                            ? 'Fast scan'
                                            : m === 'balanced'
                                                ? 'Recommended'
                                                : 'Thorough'}
                                    </span>
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Frequency */}
                    <div>
                        <label className="text-sm font-medium mb-1.5 block">
                            Frequency{' '}
                            <span className="text-muted-foreground font-normal">(Optional)</span>
                        </label>
                        <Select
                            value={frequency}
                            onValueChange={setFrequency}
                            disabled={isLoading}
                        >
                            <SelectTrigger>
                                <SelectValue placeholder="None" />
                            </SelectTrigger>
                            <SelectContent>
                                <SelectItem value="none">None</SelectItem>
                                <SelectItem value="daily">Daily</SelectItem>
                                <SelectItem value="weekly">Weekly</SelectItem>
                                <SelectItem value="monthly">Monthly</SelectItem>
                            </SelectContent>
                        </Select>
                    </div>

                    {/* Start Button */}
                    <Button
                        onClick={handleStartTest}
                        disabled={isLoading || !selectedTargetId}
                        className="w-full"
                    >
                        {isLoading ? (
                            <>
                                <Loader2 className="h-4 w-4 animate-spin mr-1" />
                                Starting...
                            </>
                        ) : (
                            <>
                                <Terminal className="h-4 w-4 mr-1" />
                                Start Assessment
                            </>
                        )}
                    </Button>

                    {/* Error */}
                    {error  && (
                        <div className="flex items-center gap-2 rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
                            <AlertTriangle className="h-4 w-4 shrink-0" />
                            <span>{error}</span>
                        </div>
                    )}

                    {/* Status */}
                    {status && !error  && (
                        <div className="flex items-center gap-2 rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-3 py-2 text-sm text-emerald-400">
                            <CheckCircle className="h-4 w-4 shrink-0" />
                            <span>{status}</span>
                            {sessionId && (
                                <Badge variant="outline" className="ml-auto text-xs">
                                    {sessionId.slice(0, 8)}...
                                </Badge>
                            )}
                        </div>
                    )}

                    <p className="text-xs text-muted-foreground">
                        Only test systems you have permission to assess.
                    </p>
                </div>
            </DialogContent>
        </Dialog>
    );
}
