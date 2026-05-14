interface PlaceholderPageProps {
    title: string;
}

export default function PlaceholderPage({ title }: PlaceholderPageProps) {
    return (
        <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
            <h1 className="text-2xl font-semibold mb-2">{title}</h1>
            <p>Coming Soon</p>
        </div>
    );
}
