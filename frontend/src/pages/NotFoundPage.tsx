import { Link, useNavigate } from "react-router-dom";

export default function NotFoundPage() {
    const navigate = useNavigate();

    const handleBack = () => {
        if (window.history.length > 1) {
            navigate(-1);
            return;
        }
        navigate("/");
    };

    return (
        <main className="min-h-screen bg-[color:var(--color-dark-bg)] text-[color:var(--color-text-primary)]">
            <div className="mx-auto flex min-h-screen max-w-3xl flex-col items-center justify-center px-6 py-16 text-center">
                <p className="text-sm font-medium uppercase tracking-[0.35em] text-[color:var(--color-text-secondary)]">
                    Fennec Security
                </p>
                <h1 className="mt-6 text-7xl font-semibold tracking-tight sm:text-8xl">
                    404
                </h1>
                <p className="mt-4 text-xl font-medium text-[color:var(--color-text-primary)] sm:text-2xl">
                    Page not found
                </p>
                <p className="mt-3 text-base text-[color:var(--color-text-secondary)] sm:text-lg">
                    The link you followed may be broken, or the page may have moved.
                </p>
                <div className="mt-8 flex flex-col items-center gap-3 sm:flex-row">
                    <Link
                        to="/"
                        className="rounded-lg bg-[color:var(--color-fennec-lime)] px-5 py-2 text-sm font-semibold text-black transition hover:bg-[color:var(--color-fennec-lime-dim)]"
                    >
                        Back to home
                    </Link>
                    <button
                        type="button"
                        onClick={handleBack}
                        className="rounded-lg border border-[color:var(--color-dark-border)] px-5 py-2 text-sm font-semibold text-[color:var(--color-text-primary)] transition hover:border-[color:var(--color-fennec-lime)]"
                    >
                        Go back
                    </button>
                </div>
            </div>
        </main>
    );
}
