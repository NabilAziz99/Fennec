import {
    AlertTriangle,
    Shield,
    CheckCircle,
    FlaskConical,
    Bot,
    TrendingUp,
    TrendingDown,
} from 'lucide-react';
import {
    Card,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { formatNumber, formatCurrency } from '@/lib/utils';
import type {DashboardStats} from "@/types";

interface StatsCardsProps {
    stats: DashboardStats;
    isLoading?: boolean;
}

export default function StatsCards({ stats, isLoading }: StatsCardsProps) {
    const cards = [
        {
            title: 'Vulnerabilities',
            value: formatNumber(stats.total_vulnerabilities),
            badge: { label: `${stats.critical_count} critical`, variant: 'destructive' as const },
            footer: 'Across all completed scans',
            icon: AlertTriangle,
            trend: null,
        },
        {
            title: 'Risk Mitigation',
            value: formatCurrency(stats.risk_mitigation_value),
            badge: null,
            footer: 'Estimated savings from remediation',
            icon: Shield,
            trend: { direction: 'up' as const, value: '+12%' },
        },
        {
            title: 'Issues Fixed',
            value: formatNumber(stats.issues_fixed),
            badge: null,
            footer: 'Resolved across all projects',
            icon: CheckCircle,
            trend: { direction: 'up' as const, value: '+8%' },
        },
        {
            title: 'Penetration Tests',
            value: formatNumber(stats.total_tests),
            badge: stats.running_tests > 0
                ? { label: `${stats.running_tests} running`, variant: 'secondary' as const }
                : null,
            footer: 'Total tests executed',
            icon: FlaskConical,
            trend: null,
        },
        {
            title: 'AI Agents',
            value: String(stats.total_agents),
            badge: { label: `${stats.active_agents} active`, variant: 'outline' as const },
            footer: 'Autonomous testing agents',
            icon: Bot,
            trend: null,
        },
    ];

    return (
        <div className="grid grid-cols-1 gap-4 px-4 lg:px-6 @xl/main:grid-cols-2 @5xl/main:grid-cols-5">
            {cards.map((card) => (
                <Card key={card.title} className="@container/card">
                    <CardHeader>
                        <CardDescription className="flex items-center gap-2">
                            <card.icon className="h-4 w-4" />
                            {card.title}
                        </CardDescription>
                        {isLoading ? (
                            <div className="h-8 w-24 animate-pulse rounded bg-muted" />
                        ) : (
                            <CardTitle className="text-2xl font-semibold tabular-nums @[250px]/card:text-3xl">
                                {card.value}
                            </CardTitle>
                        )}
                        {card.trend && (
                            <div className="ml-auto">
                                <Badge variant="outline">
                                    {card.trend.direction === 'up' ? (
                                        <TrendingUp className="h-3 w-3" />
                                    ) : (
                                        <TrendingDown className="h-3 w-3" />
                                    )}
                                    {card.trend.value}
                                </Badge>
                            </div>
                        )}
                    </CardHeader>
                    <CardFooter className="flex-col items-start gap-1.5 text-sm">
                        {card.badge && (
                            <Badge variant={card.badge.variant}>{card.badge.label}</Badge>
                        )}
                        <div className="text-muted-foreground">{card.footer}</div>
                    </CardFooter>
                </Card>
            ))}
        </div>
    );
}