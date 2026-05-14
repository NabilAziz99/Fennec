// layouts/PrivateLayout.tsx
import { useEffect } from "react";
import { Outlet, useLocation } from "react-router-dom";

/**
 * Detect stuck `body.style.pointer-events: none` and clear it when no Radix
 * primitive is actually open.
 *
 * Known Radix UI bug (radix-ui/primitives#1241 and related): when a Dialog /
 * DropdownMenu / Sheet closes under certain timing conditions — rapid
 * unmount during navigation, SSE state updates that re-render during a
 * close animation, etc. — the cleanup callback that restores
 * `body.style.pointerEvents = ''` never fires.
 */
function useRadixPointerEventsFix(): void {
    useEffect(() => {
        const clearIfStale = () => {
            if (document.body.style.pointerEvents !== "none") return;
            if (document.querySelector('[data-state="open"][role="dialog"], [data-state="open"][role="menu"], [data-state="open"][role="alertdialog"], [data-radix-focus-guard]')) {
                return;
            }
            document.body.style.pointerEvents = "";
        };

        let timer: ReturnType<typeof setTimeout> | null = null;
        const observer = new MutationObserver(() => {
            if (document.body.style.pointerEvents === "none") {
                if (timer) clearTimeout(timer);
                timer = setTimeout(clearIfStale, 600);
            }
        });
        observer.observe(document.body, {
            attributes: true,
            attributeFilter: ["style"],
        });

        clearIfStale();

        return () => {
            observer.disconnect();
            if (timer) clearTimeout(timer);
        };
    }, []);
}

export default function PrivateLayout() {
    const location = useLocation();
    useRadixPointerEventsFix();

    useEffect(() => {
        if (document.body.style.pointerEvents === "none") {
            document.body.style.pointerEvents = "";
        }
    }, [location.pathname]);

    return (
        <main>
            <Outlet />
        </main>
    );
}
