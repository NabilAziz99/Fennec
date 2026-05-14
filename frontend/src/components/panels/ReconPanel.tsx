import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import {
  Globe,
  Server,
  Lock,
  Key,
  CheckCircle,
  XCircle,
  Code,
  Database,
} from 'lucide-react';
import type { ReconState } from '@/hooks/usePentestStream';

interface ReconPanelProps {
  recon: ReconState | null;
  isStreaming?: boolean;
}

export function ReconPanel({ recon, isStreaming }: ReconPanelProps) {
  if (!recon) {
    return (
      <Card>
        <CardHeader className="py-3">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Reconnaissance Data
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">
            {isStreaming
              ? 'Waiting for reconnaissance data...'
              : 'No reconnaissance data available'}
          </p>
        </CardContent>
      </Card>
    );
  }

  // Default potentially undefined arrays to empty (SSE can deliver partial data)
  const technologies: ReconState['technologies'] = recon.technologies || [];
  const endpoints: ReconState['endpoints'] = recon.endpoints || [];
  const entryPoints: ReconState['entryPoints'] = recon.entryPoints || [];
  const portsOpen: number[] = recon.portsOpen || [];
  const defaultCredentialsFound: boolean = recon.defaultCredentialsFound || false;
  const headersOfInterest: string[] = recon.headersOfInterest || [];
  const notes: string[] = recon.notes || [];

  return (
    <Card>
      <CardHeader className="py-3">
        <CardTitle className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
          <Globe className="h-4 w-4" />
          Reconnaissance Data
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Target Info */}
        <div>
          <h4 className="mb-2 flex items-center gap-2 text-xs font-semibold">
            <Server className="h-3.5 w-3.5" />
            Target Information
          </h4>
          <div className="space-y-1 rounded-lg bg-muted/50 p-3 text-xs">
            {recon.summary && (
              <div className="flex justify-start text-left">
                <span className="text-muted-foreground">Summary:</span>
                <span className="pl-5">{recon.summary}</span>
              </div>
            )}
            {recon.ipAddress && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">IP Address:</span>
                <span className="font-mono">{recon.ipAddress}</span>
              </div>
            )}
            {portsOpen.length > 0 && (
              <div className="flex justify-between">
                <span className="text-muted-foreground">Open Ports:</span>
                <span className="font-mono">{portsOpen.join(', ')}</span>
              </div>
            )}
          </div>
        </div>

        {/* Technologies */}
        {technologies.length > 0 && (
          <div>
            <h4 className="mb-2 flex items-center gap-2 text-xs font-semibold">
              <Code className="h-3.5 w-3.5" />
              Technologies ({technologies.length})
            </h4>
            <div className="flex flex-wrap gap-2">
              {technologies.map((tech, idx) => (
                <Badge key={idx} variant="outline" className="gap-1">
                  {tech.name}
                  {tech.version && ` ${tech.version}`}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Authentication */}
        {(recon.authType || recon.loginEndpoint) && (
          <div>
            <h4 className="mb-2 flex items-center gap-2 text-xs font-semibold">
              <Lock className="h-3.5 w-3.5" />
              Authentication
            </h4>
            <div className="space-y-1 rounded-lg bg-muted/50 p-3 text-xs">
              {recon.authType && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Type:</span>
                  <Badge variant="secondary">{recon.authType}</Badge>
                </div>
              )}
              {recon.loginEndpoint && (
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Login Endpoint:</span>
                  <span className="font-mono text-xs">{recon.loginEndpoint}</span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-muted-foreground">Registration Available:</span>
                {recon.registrationAvailable ? (
                  <CheckCircle className="h-4 w-4 text-emerald-400" />
                ) : (
                  <XCircle className="h-4 w-4 text-muted-foreground" />
                )}
              </div>
            </div>
          </div>
        )}

        {/* Endpoints */}
        {endpoints.length > 0 && (
          <div>
            <h4 className="mb-2 flex items-center gap-2 text-xs font-semibold">
              <Database className="h-3.5 w-3.5" />
              Endpoints ({endpoints.length})
            </h4>
            <div className="max-h-32 space-y-1 overflow-y-auto text-xs">
              {endpoints.slice(0, 10).map((endpoint, idx) => (
                <div key={idx} className="flex items-center gap-2 rounded bg-muted/50 p-2">
                  <Badge variant="outline" className="text-xs">
                    {endpoint.method}
                  </Badge>
                  <span className="flex-1 truncate font-mono text-xs">{endpoint.path}</span>
                  {endpoint.auth_required && (
                    <Lock className="h-3 w-3 text-yellow-400" />
                  )}
                </div>
              ))}
              {endpoints.length > 10 && (
                <p className="text-center text-muted-foreground">
                  +{endpoints.length - 10} more endpoints
                </p>
              )}
            </div>
          </div>
        )}

        {/* Entry Points */}
        {entryPoints.length > 0 && (
          <div>
            <h4 className="mb-2 flex items-center gap-2 text-xs font-semibold">
              Entry Points ({entryPoints.length})
            </h4>
            <div className="max-h-24 space-y-1 overflow-y-auto text-xs">
              {entryPoints.map((ep, idx) => (
                <div key={idx} className="rounded bg-muted/50 p-2">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs">{ep.location}</span>
                    <Badge variant="secondary" className="text-xs">
                      {ep.type}
                    </Badge>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Default Credentials */}
        {defaultCredentialsFound && (
          <div>
            <h4 className="mb-2 flex items-center gap-2 text-xs font-semibold text-yellow-400">
              <Key className="h-3.5 w-3.5" />
              Default Credentials Found
            </h4>
            <div className="rounded-lg border border-yellow-500/40 bg-yellow-500/10 p-2 text-xs">
              <span className="text-yellow-400">Default credentials were detected on this target.</span>
            </div>
          </div>
        )}

        {/* Headers of Interest */}
        {headersOfInterest.length > 0 && (
          <div>
            <h4 className="mb-2 text-xs font-semibold">Headers of Interest</h4>
            <div className="space-y-1 text-xs">
              {headersOfInterest.map((header, idx) => (
                <div key={idx} className="rounded bg-muted/50 p-2">
                  <span className="font-mono">{header}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Notes */}
        {notes.length > 0 && (
          <div>
            <h4 className="mb-2 text-xs font-semibold">Notes</h4>
            <ul className="list-inside list-disc space-y-1 text-xs text-muted-foreground">
              {notes.map((note, idx) => (
                <li key={idx}>{note}</li>
              ))}
            </ul>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
