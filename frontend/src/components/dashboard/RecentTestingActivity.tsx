import { Link } from 'react-router-dom';
import {
    CheckCircle,
    Clock,
    AlertCircle,
    XCircle,
    ExternalLink,
    MoreHorizontal,
} from 'lucide-react';
import {
    Card,
    CardContent,
    CardDescription,
    CardHeader,
    CardTitle,
} from '@/components/ui/card';
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { formatRelativeTime } from '@/lib/utils';
import type { TestActivity } from '@/types';

interface RecentTestingActivityProps {
    tests: TestActivity[];
    isLoading?: boolean;
}

/* ---- Status rendering ---- */

const statusConfig: Record<
    TestActivity['status'],
    { icon: React.ComponentType<{ className?: string }>; label: string; variant: 'default' | 'secondary' | 'outline' | 'destructive' }
> = {
    completed: { icon: CheckCircle, label: 'Completed', variant: 'outline' },
    running: { icon: Clock, label: 'Running', variant: 'secondary' },
    pending: { icon: AlertCircle, label: 'Pending', variant: 'outline' },
    failed: { icon: XCircle, label: 'Failed', variant: 'destructive' },
    awaiting_review: { icon: AlertCircle, label: 'Awaiting Review', variant: 'secondary' },
};

function StatusBadge({ status }: { status: TestActivity['status'] }) {
    const config = statusConfig[status] ?? statusConfig.pending;
    const Icon = config.icon;

    return (
        <Badge variant={config.variant} className="gap-1">
            <Icon className={`h-3 w-3 ${status === 'running' ? 'animate-pulse' : ''}`} />
            {config.label}
        </Badge>
    );
}

/* ---- Severity mini-badges ---- */

function SeverityBadges({ issues }: { issues: TestActivity['issues'] }) {
    const badges = [
        { key: 'critical', count: issues.critical, className: 'border-red-500/40 text-red-400' },
        { key: 'high', count: issues.high, className: 'border-orange-500/40 text-orange-400' },
        { key: 'medium', count: issues.medium, className: 'border-amber-500/40 text-amber-400' },
        { key: 'low', count: issues.low, className: 'border-emerald-500/40 text-emerald-400' },
    ].filter((b) => b.count > 0);

    if (badges.length === 0) {
        return <span className="text-muted-foreground">—</span>;
    }

    return (
        <div className="flex items-center gap-1">
            {badges.map((b) => (
                <Badge key={b.key} variant="outline" className={b.className}>
                    {b.count}
                </Badge>
            ))}
        </div>
    );
}

/* ---- Loading skeleton ---- */

function SkeletonRow() {
    return (
        <TableRow>
            <TableCell>
                <div className="space-y-2">
                    <div className="h-4 w-40 animate-pulse rounded bg-muted" />
                    <div className="h-3 w-28 animate-pulse rounded bg-muted" />
                </div>
            </TableCell>
            <TableCell><div className="h-5 w-20 animate-pulse rounded-full bg-muted" /></TableCell>
            <TableCell><div className="h-5 w-24 animate-pulse rounded bg-muted" /></TableCell>
            <TableCell><div className="h-4 w-14 animate-pulse rounded bg-muted" /></TableCell>
            <TableCell><div className="h-4 w-20 animate-pulse rounded bg-muted" /></TableCell>
            <TableCell><div className="h-6 w-16 animate-pulse rounded bg-muted" /></TableCell>
        </TableRow>
    );
}

/* ---- Main component ---- */

export default function RecentTestingActivity({
                                                  tests,
                                                  isLoading,
                                              }: RecentTestingActivityProps) {
    return (
        <Card className="mx-5">
            <CardHeader className="flex-row items-center justify-between">
                <div>
                    <CardTitle>Recent Testing Activity</CardTitle>
                    <CardDescription>Latest penetration test runs and results</CardDescription>
                </div>
                <Button variant="outline" size="sm" asChild>
                    <Link to="/dashboard/tests">View all</Link>
                </Button>
            </CardHeader>
            <CardContent className="p-0 m-2">
                <div className="overflow-hidden rounded-lg border">
                    <Table>
                        <TableHeader className="bg-muted/50">
                            <TableRow>
                                <TableHead>Test</TableHead>
                                <TableHead>Status</TableHead>
                                <TableHead>Issues</TableHead>
                                <TableHead>Duration</TableHead>
                                <TableHead>Started</TableHead>
                                <TableHead className="w-12" />
                            </TableRow>
                        </TableHeader>
                        <TableBody>
                            {isLoading ? (
                                Array.from({ length: 5 }).map((_, i) => <SkeletonRow key={i} />)
                            ) : tests.length > 0 ? (
                                tests.map((test) => (
                                    <TableRow key={test.id}>
                                        <TableCell>
                                            <div className="flex flex-col">
                                                <Link
                                                    to={`/dashboard/tests/${test.id}`}
                                                    className="font-medium hover:underline"
                                                >
                                                    {test.title}
                                                </Link>
                                                <span className="text-muted-foreground max-w-[220px] truncate text-xs">
                          {test.target_url}
                        </span>
                                            </div>
                                        </TableCell>
                                        <TableCell>
                                            <StatusBadge status={test.status} />
                                        </TableCell>
                                        <TableCell>
                                            <SeverityBadges issues={test.issues} />
                                        </TableCell>
                                        <TableCell className="text-muted-foreground">
                                            {test.duration}
                                        </TableCell>
                                        <TableCell className="text-muted-foreground">
                                            {formatRelativeTime(test.started_at)}
                                        </TableCell>
                                        <TableCell>
                                            <DropdownMenu>
                                                <DropdownMenuTrigger asChild>
                                                    <Button variant="ghost" size="icon" className="h-8 w-8">
                                                        <MoreHorizontal className="h-4 w-4" />
                                                        <span className="sr-only">Actions</span>
                                                    </Button>
                                                </DropdownMenuTrigger>
                                                <DropdownMenuContent align="end" className="w-40">
                                                    <DropdownMenuItem asChild>
                                                        <Link to={`/dashboard/tests/${test.id}`}>
                                                            <ExternalLink className="mr-2 h-4 w-4" />
                                                            View details
                                                        </Link>
                                                    </DropdownMenuItem>
                                                    <DropdownMenuItem>Re-run test</DropdownMenuItem>
                                                    <DropdownMenuSeparator />
                                                    <DropdownMenuItem>
                                                        Delete
                                                    </DropdownMenuItem>
                                                </DropdownMenuContent>
                                            </DropdownMenu>
                                        </TableCell>
                                    </TableRow>
                                ))
                            ) : (
                                <TableRow>
                                    <TableCell colSpan={6} className="h-32 text-center">
                                        <div className="text-muted-foreground">
                                            <AlertCircle className="mx-auto mb-2 h-8 w-8 opacity-50" />
                                            <p>No tests yet</p>
                                            <p className="mt-1 text-sm">
                                                Start a penetration test to see results here
                                            </p>
                                        </div>
                                    </TableCell>
                                </TableRow>
                            )}
                        </TableBody>
                    </Table>
                </div>
            </CardContent>
        </Card>
    );
}