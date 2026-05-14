import { PieChart, Pie, Cell, Label } from 'recharts';
import {
    Card,
    CardContent,
    CardDescription,
    CardFooter,
    CardHeader,
    CardTitle,
} from '@/components/ui/card';
import {
    ChartContainer,
    ChartTooltip,
    ChartTooltipContent,
    type ChartConfig,
} from '@/components/ui/chart';
import type { SeverityDistribution } from '@/types';

interface SeverityDistributionChartProps {
    data: SeverityDistribution;
    isLoading?: boolean;
}

const chartConfig = {
    critical: { label: 'Critical', color: 'hsl(0 85% 60%)' },
    high: { label: 'High', color: 'hsl(25 95% 55%)' },
    medium: { label: 'Medium', color: 'hsl(45 95% 55%)' },
    low: { label: 'Low', color: 'hsl(142 70% 45%)' },
    info: { label: 'Info', color: 'hsl(262 80% 62%)' },
} satisfies ChartConfig;

export default function SeverityDistributionChart({
                                                      data,
                                                      isLoading,
                                                  }: SeverityDistributionChartProps) {
    const total = Object.values(data).reduce((sum, val) => sum + val, 0);

    const chartData = [
        { name: 'critical', count: data.critical, fill: 'var(--color-critical)' },
        { name: 'high', count: data.high, fill: 'var(--color-high)' },
        { name: 'medium', count: data.medium, fill: 'var(--color-medium)' },
        { name: 'low', count: data.low, fill: 'var(--color-low)' },
        { name: 'info', count: data.info, fill: 'var(--color-info)' },
    ].filter((item) => item.count > 0);

    if (isLoading) {
        return (
            <Card>
                <CardHeader>
                    <CardTitle>Severity Distribution</CardTitle>
                    <CardDescription>Breakdown by severity level</CardDescription>
                </CardHeader>
                <CardContent className="flex items-center justify-center">
                    <div className="h-48 w-48 animate-pulse rounded-full bg-muted" />
                </CardContent>
            </Card>
        );
    }

    return (
        <Card className="flex flex-col h-full">
            <CardHeader className="items-center pb-0">
                <CardTitle>Severity Distribution</CardTitle>
                <CardDescription>Breakdown by severity level</CardDescription>
            </CardHeader>
            <CardContent className="flex-1 pb-0">
                <ChartContainer
                    config={chartConfig}
                    className="mx-auto aspect-square max-h-[280px]"
                >
                    <PieChart>
                        <ChartTooltip
                            cursor={false}
                            content={<ChartTooltipContent hideLabel />}
                        />
                        <Pie
                            data={chartData}
                            dataKey="count"
                            nameKey="name"
                            innerRadius={60}
                            outerRadius={90}
                            paddingAngle={2}
                            strokeWidth={0}
                        >
                            {chartData.map((entry) => (
                                <Cell key={entry.name} fill={entry.fill} />
                            ))}
                            <Label
                                content={({ viewBox }) => {
                                    if (viewBox && 'cx' in viewBox && 'cy' in viewBox) {
                                        return (
                                            <text
                                                x={viewBox.cx}
                                                y={viewBox.cy}
                                                textAnchor="middle"
                                                dominantBaseline="middle"
                                            >
                                                <tspan
                                                    x={viewBox.cx}
                                                    y={viewBox.cy}
                                                    className="fill-foreground text-3xl font-bold"
                                                >
                                                    {total}
                                                </tspan>
                                                <tspan
                                                    x={viewBox.cx}
                                                    y={(viewBox.cy || 0) + 24}
                                                    className="fill-muted-foreground text-sm"
                                                >
                                                    Total
                                                </tspan>
                                            </text>
                                        );
                                    }
                                }}
                            />
                        </Pie>
                    </PieChart>
                </ChartContainer>
            </CardContent>
            <CardFooter className="flex-col gap-2 text-sm">
                <div className="flex flex-wrap items-center justify-center gap-x-4 gap-y-1">
                    {chartData.map((item) => (
                        <div key={item.name} className="flex items-center gap-1.5">
              <span
                  className="inline-block h-2.5 w-2.5 rounded-full"
                  style={{ backgroundColor: chartConfig[item.name as keyof typeof chartConfig].color }}
              />
                            <span className="text-muted-foreground capitalize">{item.name}</span>
                            <span className="font-medium">{item.count}</span>
                        </div>
                    ))}
                </div>
            </CardFooter>
        </Card>
    );
}