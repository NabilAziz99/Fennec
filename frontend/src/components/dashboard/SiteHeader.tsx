import { useLocation } from 'react-router-dom';
import { Separator } from '@/components/ui/separator';
import { SidebarTrigger } from '@/components/ui/sidebar';
import { Button } from '@/components/ui/button';
import { RefreshCw } from 'lucide-react';
import { cn } from '@/lib/utils';

interface SiteHeaderProps {
    onRefresh?: () => void;
    isRefreshing?: boolean;
}

const pageTitles: Record<string, string> = {
    '/dashboard': 'Security Dashboard',
    '/dashboard/tests': 'Penetration Tests',
    '/dashboard/issues': 'Issues',
    '/dashboard/chats': 'Chats',
    '/dashboard/monitor': 'Event Monitor',
    '/dashboard/settings': 'Settings',
};

export function SiteHeader({ onRefresh, isRefreshing }: SiteHeaderProps) {
    const location = useLocation();

    // Match the most specific path first
    const title =
        Object.entries(pageTitles).find(([path]) =>
            location.pathname === path || location.pathname.startsWith(path + '/')
        )?.[1] ?? 'Dashboard';

    return (
        <header className="flex h-[calc(var(--spacing)*12)] shrink-0 items-center gap-2 border-b transition-[width,height] ease-linear group-has-data-[collapsible=icon]/sidebar-wrapper:h-[calc(var(--spacing)*12)]">
            <div className="flex w-full items-center gap-1 px-4 lg:gap-2 lg:px-6">
                <SidebarTrigger className="-ml-1" />
                <Separator
                    orientation="vertical"
                    className="mx-2 data-[orientation=vertical]:h-4"
                />
                <h1 className="text-base font-medium">{title}</h1>

                {onRefresh && (
                    <div className="ml-auto flex items-center gap-2">
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={onRefresh}
                            disabled={isRefreshing}
                        >
                            <RefreshCw
                                className={cn('h-4 w-4', isRefreshing && 'animate-spin')}
                            />
                            <span className="hidden sm:inline">Refresh</span>
                        </Button>
                    </div>
                )}
            </div>
        </header>
    );
}