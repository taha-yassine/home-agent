import { useLocation, useMatches } from "react-router";

// In Home Assistant ingress, the app is mounted under `/api/hassio_ingress/<token>`.
// This hook derives the ingress base path. In dev, returns an empty string.
export function useIngressBasePath(): string {
  const location = useLocation();
  const matches = useMatches();

  // Derive the matched base from the `routes/ingress` route.
  const ingressBaseMatch = (matches as any[]).find((m) => m?.id === "routes/ingress");
  const fromMatch: string | undefined = (ingressBaseMatch as any)?.pathname;
  if (fromMatch) {
    return fromMatch;
  }

  return "";
}


