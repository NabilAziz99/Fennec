import { Link, useLocation, useNavigate } from 'react-router-dom';
import {
    LayoutDashboard,
    Activity,
    ShieldAlert,
    Globe,
    Plus,
} from 'lucide-react';
import {
    Sidebar,
    SidebarContent,
    SidebarGroup,
    SidebarGroupContent,
    SidebarGroupLabel,
    SidebarHeader,
    SidebarMenu,
    SidebarMenuButton,
    SidebarMenuItem,
} from '@/components/ui/sidebar';
import { useState } from "react";
import { TestDialog } from "@/components/dashboard/TestDialogBox.tsx";

/* ------------------------------------------------------------------ */
/*  Navigation data                                                    */
/* ------------------------------------------------------------------ */

const navMain = [
    { title: 'Overview', href: '/dashboard', icon: LayoutDashboard },
    { title: 'Status', href: '/dashboard/status', icon: Activity },
    { title: 'Findings', href: '/dashboard/findings', icon: ShieldAlert },
    { title: 'Target Inventory', href: '/dashboard/targets', icon: Globe },
];

/* ------------------------------------------------------------------ */
/*  Component                                                          */
/* ------------------------------------------------------------------ */

export function AppSidebar(props: React.ComponentProps<typeof Sidebar>) {
    const location = useLocation();
    const navigate = useNavigate();
    const [TestOpen, setTestOpen] = useState(false);

    const isActive = (href: string) => {
        if (href === '/dashboard') return location.pathname === '/dashboard';
        return location.pathname.startsWith(href);
    };

    return (
        <>
        <Sidebar collapsible="icon" {...props}>
            {/* ---- Header / Logo ---- */}
            <SidebarHeader>
                <SidebarMenu>
                    <SidebarMenuItem>
                        <SidebarMenuButton
                            asChild
                            className="data-[slot=sidebar-menu-button]:!p-1.5"
                        >
                            <Link to="/dashboard">
                                <img
                                    src="/fennec.png"
                                    alt="Fennec"
                                    className="h-6 w-6 rounded-md object-contain"
                                />
                                <span className="text-base font-semibold">Fennec</span>
                            </Link>
                        </SidebarMenuButton>
                    </SidebarMenuItem>
                </SidebarMenu>
            </SidebarHeader>

            {/* ---- Main content ---- */}
            <SidebarContent>
                {/* Quick action */}
                <SidebarGroup>
                    <SidebarGroupContent className="flex flex-col gap-2">
                        <SidebarMenu>
                            <SidebarMenuItem>
                                <SidebarMenuButton
                                    tooltip="Create"
                                    onClick={() => setTestOpen(true)}
                                    className="bg-primary text-primary-foreground hover:bg-primary/90 hover:text-primary-foreground active:bg-primary/90 active:text-primary-foreground min-w-8 duration-200 ease-linear"
                                >
                                    <Plus className="h-4 w-4" />
                                    <span>Create</span>
                                </SidebarMenuButton>
                            </SidebarMenuItem>
                        </SidebarMenu>
                    </SidebarGroupContent>
                </SidebarGroup>

                {/* Platform nav */}
                <SidebarGroup>
                    <SidebarGroupLabel>Platform</SidebarGroupLabel>
                    <SidebarGroupContent>
                        <SidebarMenu>
                            {navMain.map((item) => (
                                <SidebarMenuItem key={item.title}>
                                    <SidebarMenuButton
                                        tooltip={item.title}
                                        isActive={isActive(item.href)}
                                        onClick={() => navigate(item.href)}
                                        className="cursor-pointer"
                                    >
                                        <item.icon className="h-4 w-4" />
                                        <span>{item.title}</span>
                                    </SidebarMenuButton>
                                </SidebarMenuItem>
                            ))}
                        </SidebarMenu>
                    </SidebarGroupContent>
                </SidebarGroup>
            </SidebarContent>
        </Sidebar>
        <TestDialog open={TestOpen} onOpenChange={setTestOpen} />
        </>
    );
}
