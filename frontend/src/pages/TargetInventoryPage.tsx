import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Plus,
  Search,
  Globe,
  Shield,
  ShieldCheck,
  Loader2,
  AlertTriangle,
  Trash2,
  Pencil,
  Save,
  KeyRound,
} from 'lucide-react';
import DashboardLayout from '@/components/dashboard/DashboardLayout';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { targetApi, credentialApi } from '@/services/api';
import type { Target, Credential } from '@/types';

function relativeTime(dateStr: string | null): string {
  if (!dateStr) return 'Never';
  const now = Date.now();
  const then = new Date(dateStr).getTime();
  const diffMs = now - then;
  const diffMins = Math.floor(diffMs / 60000);
  if (diffMins < 1) return 'Just now';
  if (diffMins < 60) return `${diffMins}m ago`;
  const diffHours = Math.floor(diffMins / 60);
  if (diffHours < 24) return `${diffHours}h ago`;
  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 30) return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
  const diffMonths = Math.floor(diffDays / 30);
  return `${diffMonths} month${diffMonths > 1 ? 's' : ''} ago`;
}

export default function TargetInventoryPage() {
  const navigate = useNavigate();
  const [targets, setTargets] = useState<Target[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [isRefreshing, setIsRefreshing] = useState(false);

  // Add Target Dialog state
  const [addDialogOpen, setAddDialogOpen] = useState(false);
  const [newDomain, setNewDomain] = useState('');
  const [newName, setNewName] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [createError, setCreateError] = useState('');

  // Credential fields (optional)
  const [credentials, setCredentials] = useState<Credential[]>([]);
  const [selectedCredentialId, setSelectedCredentialId] = useState<string>('none');
  const [newCredUsername, setNewCredUsername] = useState('');
  const [newCredPassword, setNewCredPassword] = useState('');
  const [newCredAuthType, setNewCredAuthType] = useState('form');
  const [showNewCredFields, setShowNewCredFields] = useState(false);

  // Edit Target Dialog state
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editTarget, setEditTarget] = useState<Target | null>(null);
  const [editName, setEditName] = useState('');
  const [editDomain, setEditDomain] = useState('');
  const [editError, setEditError] = useState('');
  const [isSaving, setIsSaving] = useState(false);
  const [editCredentials, setEditCredentials] = useState<Credential[]>([]);
  const [editingCredId, setEditingCredId] = useState<string | null>(null);
  const [editCredName, setEditCredName] = useState('');
  const [editCredUsername, setEditCredUsername] = useState('');
  const [editCredPassword, setEditCredPassword] = useState('');
  const [editCredAuthType, setEditCredAuthType] = useState('form');
  const [showAddCred, setShowAddCred] = useState(false);
  const [addCredName, setAddCredName] = useState('');
  const [addCredUsername, setAddCredUsername] = useState('');
  const [addCredPassword, setAddCredPassword] = useState('');
  const [addCredAuthType, setAddCredAuthType] = useState('form');

  const fetchTargets = useCallback(async () => {
    try {
      const data = await targetApi.list();
      setTargets(data);
    } catch {
      // silently handle
    } finally {
      setIsLoading(false);
    }
  }, []);

  const fetchCredentials = useCallback(async () => {
    try {
      const data = await credentialApi.list();
      setCredentials(data);
    } catch {
      // silently handle
    }
  }, []);

  const handleDeleteTarget = async (targetId: string) => {
    try {
      await targetApi.delete(targetId);
      await fetchTargets();
    } catch {
      // silently handle
    }
  };

  const openEditDialog = async (target: Target) => {
    setEditTarget(target);
    setEditName(target.name);
    setEditDomain(target.domain);
    setEditError('');
    setEditingCredId(null);
    setShowAddCred(false);
    setEditDialogOpen(true);
    try {
      const creds = await credentialApi.list(target.id);
      setEditCredentials(creds);
    } catch {
      setEditCredentials([]);
    }
  };

  const handleSaveTarget = async () => {
    if (!editTarget) return;
    setIsSaving(true);
    setEditError('');
    try {
      await targetApi.update(editTarget.id, {
        name: editName.trim(),
        domain: editDomain.trim(),
      });
      setEditDialogOpen(false);
      await fetchTargets();
    } catch (err) {
      setEditError(err instanceof Error ? err.message : 'Failed to update target');
    } finally {
      setIsSaving(false);
    }
  };

  const handleSaveCredential = async (credId: string) => {
    setIsSaving(true);
    try {
      const updates: Record<string, string> = {};
      if (editCredName.trim()) updates.name = editCredName.trim();
      if (editCredUsername.trim()) updates.username = editCredUsername.trim();
      if (editCredPassword.trim()) updates.password = editCredPassword.trim();
      if (editCredAuthType) updates.auth_type = editCredAuthType;
      await credentialApi.update(credId, updates);
      setEditingCredId(null);
      if (editTarget) {
        const creds = await credentialApi.list(editTarget.id);
        setEditCredentials(creds);
      }
    } catch {
      setEditError('Failed to update credential');
    } finally {
      setIsSaving(false);
    }
  };

  const handleAddCredToTarget = async () => {
    if (!editTarget || !addCredUsername.trim() || !addCredPassword.trim()) return;
    setIsSaving(true);
    try {
      await credentialApi.create({
        target_id: editTarget.id,
        name: addCredName.trim() || `${editTarget.name} credentials`,
        username: addCredUsername.trim(),
        password: addCredPassword.trim(),
        auth_type: addCredAuthType,
      });
      setShowAddCred(false);
      setAddCredName('');
      setAddCredUsername('');
      setAddCredPassword('');
      setAddCredAuthType('form');
      const creds = await credentialApi.list(editTarget.id);
      setEditCredentials(creds);
    } catch {
      setEditError('Failed to add credential');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteCredential = async (credId: string) => {
    try {
      await credentialApi.delete(credId);
      setEditCredentials((prev) => prev.filter((c) => c.id !== credId));
    } catch {
      setEditError('Failed to delete credential');
    }
  };

  useEffect(() => {
    fetchTargets();
  }, [fetchTargets]);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await fetchTargets();
    setTimeout(() => setIsRefreshing(false), 500);
  };

  const handleAddTarget = async () => {
    if (!newDomain.trim()) {
      setCreateError('Domain is required');
      return;
    }
    if (!newName.trim()) {
      setCreateError('Name is required');
      return;
    }

    setIsCreating(true);
    setCreateError('');
    try {
      const target = await targetApi.create({ domain: newDomain.trim(), name: newName.trim() });

      // Create credential if new credential fields are filled
      if (showNewCredFields && newCredUsername.trim() && newCredPassword.trim()) {
        await credentialApi.create({
          target_id: target.id,
          name: `${newName.trim()} credentials`,
          username: newCredUsername.trim(),
          password: newCredPassword.trim(),
          auth_type: newCredAuthType,
        });
      }

      setAddDialogOpen(false);
      setNewDomain('');
      setNewName('');
      setSelectedCredentialId('none');
      setNewCredUsername('');
      setNewCredPassword('');
      setNewCredAuthType('form');
      setShowNewCredFields(false);
      await fetchTargets();
    } catch (err) {
      setCreateError(
        err instanceof Error ? err.message : 'Failed to create target'
      );
    } finally {
      setIsCreating(false);
    }
  };

  const filteredTargets = targets.filter((t) => {
    const q = searchQuery.toLowerCase();
    return (
      t.name.toLowerCase().includes(q) || t.domain.toLowerCase().includes(q)
    );
  });

  return (
    <DashboardLayout onRefresh={handleRefresh} isRefreshing={isRefreshing}>
      <div className="flex flex-col gap-6 p-4 lg:p-6">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-semibold tracking-tight">
              Targets ({targets.length})
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              Select a target to view its security findings
            </p>
          </div>
          <Button onClick={() => { setAddDialogOpen(true); fetchCredentials(); }}>
            <Plus className="h-4 w-4 mr-1" />
            Add Target
          </Button>
        </div>

        {/* Stats Bar */}
        <div className="flex items-center gap-3">
          <Badge variant="secondary" className="text-xs">
            <Globe className="h-3 w-3 mr-1" />
            {targets.length} Target{targets.length !== 1 ? 's' : ''}
          </Badge>
          <Badge variant="outline" className="text-xs text-muted-foreground">
            0 targets remaining
          </Badge>
        </div>

        {/* Search */}
        <div className="relative max-w-md">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search targets..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
          />
        </div>

        {/* Target Grid */}
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
          </div>
        ) : filteredTargets.length === 0 ? (
          <div className="rounded-lg border border-dashed border-border/60 bg-muted/30 p-12 text-center">
            {targets.length === 0 ? (
              <>
                <Shield className="mx-auto h-10 w-10 text-muted-foreground/50 mb-3" />
                <p className="text-sm text-muted-foreground mb-4">
                  No targets added yet. Add your first target to start testing.
                </p>
                <Button
                  variant="outline"
                  onClick={() => setAddDialogOpen(true)}
                >
                  <Plus className="h-4 w-4 mr-1" />
                  Add Target
                </Button>
              </>
            ) : (
              <p className="text-sm text-muted-foreground">
                No targets match your search.
              </p>
            )}
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredTargets.map((target) => {
              const sev = target.severity_counts || {};
              const critical = sev.critical ?? 0;
              const high = sev.high ?? 0;
              const medium = sev.medium ?? 0;
              const low = sev.low ?? 0;

              return (
                <div
                  key={target.id}
                  onClick={() =>
                    navigate(
                      `/dashboard/findings?target_id=${target.id}`
                    )
                  }
                  className="rounded-lg border border-border/50 bg-card p-4 cursor-pointer hover:bg-muted/50 transition-colors"
                >
                  {/* Top row: icon + name + delete */}
                  <div className="flex items-start gap-3 mb-3">
                    <div className="flex h-9 w-9 items-center justify-center rounded-md bg-muted">
                      <Globe className="h-4 w-4 text-muted-foreground" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">
                        {target.name}
                      </p>
                      <p className="text-xs text-muted-foreground truncate">
                        {target.domain}
                      </p>
                    </div>
                    <div className="flex items-center gap-1">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          openEditDialog(target);
                        }}
                        className="p-1.5 rounded-md text-muted-foreground hover:text-fennec-orange-400 hover:bg-fennec-orange-500/10 transition-colors"
                        title="Edit target"
                      >
                        <Pencil className="h-4 w-4" />
                      </button>
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          if (confirm(`Delete target "${target.name}"?`)) {
                            handleDeleteTarget(target.id);
                          }
                        }}
                        className="p-1.5 rounded-md text-muted-foreground hover:text-red-400 hover:bg-red-500/10 transition-colors"
                        title="Delete target"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  </div>

                  {/* Severity badges */}
                  <div className="flex items-center gap-2 mb-3">
                    {critical > 0 && (
                      <span className="inline-flex items-center gap-1 text-xs">
                        <span className="h-2 w-2 rounded-full bg-red-500" />
                        {critical}
                      </span>
                    )}
                    {high > 0 && (
                      <span className="inline-flex items-center gap-1 text-xs">
                        <span className="h-2 w-2 rounded-full bg-orange-500" />
                        {high}
                      </span>
                    )}
                    {medium > 0 && (
                      <span className="inline-flex items-center gap-1 text-xs">
                        <span className="h-2 w-2 rounded-full bg-yellow-500" />
                        {medium}
                      </span>
                    )}
                    {low > 0 && (
                      <span className="inline-flex items-center gap-1 text-xs">
                        <span className="h-2 w-2 rounded-full bg-emerald-500" />
                        {low}
                      </span>
                    )}
                    {critical === 0 &&
                      high === 0 &&
                      medium === 0 &&
                      low === 0 && (
                        <span className="text-xs text-muted-foreground">
                          No findings
                        </span>
                      )}
                  </div>

                  {/* Bottom row: verified + last scanned — verification UX disabled per request, always show Verified */}
                  <div className="flex items-center justify-between">
                    <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/20 text-xs">
                      <ShieldCheck className="h-3 w-3 mr-1" />
                      Verified
                    </Badge>
                    {/* {target.verified ? (
                      <Badge className="bg-emerald-500/20 text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/20 text-xs">
                        <ShieldCheck className="h-3 w-3 mr-1" />
                        Verified
                      </Badge>
                    ) : (
                      <Badge
                        variant="outline"
                        className="text-muted-foreground text-xs"
                      >
                        <ShieldAlert className="h-3 w-3 mr-1" />
                        Unverified
                      </Badge>
                    )} */}
                    <span className="text-xs text-muted-foreground">
                      {relativeTime(target.last_scanned)}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Add Target Dialog */}
      <Dialog open={addDialogOpen} onOpenChange={setAddDialogOpen}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Add Target</DialogTitle>
            <DialogDescription>
              Add a new target domain for security testing.
            </DialogDescription>
          </DialogHeader>

          <div className="flex flex-col gap-4 pt-2">
            <div>
              <label className="text-sm font-medium mb-1.5 block">Domain</label>
              <Input
                placeholder="https://example.com"
                value={newDomain}
                onChange={(e) => {
                  setNewDomain(e.target.value);
                  setCreateError('');
                }}
                disabled={isCreating}
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-1.5 block">Name</label>
              <Input
                placeholder="My Application"
                value={newName}
                onChange={(e) => {
                  setNewName(e.target.value);
                  setCreateError('');
                }}
                disabled={isCreating}
              />
            </div>

            {/* Credential section */}
            <div>
              <label className="text-sm font-medium mb-1.5 block">
                Authentication Credentials <span className="text-muted-foreground font-normal">(optional)</span>
              </label>
              <Select
                value={selectedCredentialId}
                onValueChange={(val) => {
                  setSelectedCredentialId(val);
                  setShowNewCredFields(val === 'new');
                }}
              >
                <SelectTrigger>
                  <SelectValue placeholder="No credentials" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="none">No credentials</SelectItem>
                  {credentials.map((cred) => (
                    <SelectItem key={cred.id} value={cred.id}>
                      {cred.name} ({cred.username})
                    </SelectItem>
                  ))}
                  <SelectItem value="new">+ Add new credentials</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* New credential fields */}
            {showNewCredFields && (
              <div className="flex flex-col gap-3 rounded-lg border border-border/50 bg-muted/20 p-3">
                <div>
                  <label className="text-xs font-medium mb-1 block text-muted-foreground">Username</label>
                  <Input
                    placeholder="admin@example.com"
                    value={newCredUsername}
                    onChange={(e) => setNewCredUsername(e.target.value)}
                    disabled={isCreating}
                  />
                </div>
                <div>
                  <label className="text-xs font-medium mb-1 block text-muted-foreground">Password</label>
                  <Input
                    type="password"
                    placeholder="••••••••"
                    value={newCredPassword}
                    onChange={(e) => setNewCredPassword(e.target.value)}
                    disabled={isCreating}
                  />
                </div>
                <div>
                  <label className="text-xs font-medium mb-1 block text-muted-foreground">Auth Type</label>
                  <Select value={newCredAuthType} onValueChange={setNewCredAuthType}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="form">Form Login</SelectItem>
                      <SelectItem value="basic">Basic Auth</SelectItem>
                      <SelectItem value="bearer">Bearer Token</SelectItem>
                      <SelectItem value="api_key">API Key</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            )}

            {createError && (
              <div className="flex items-center gap-2 rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
                <AlertTriangle className="h-4 w-4 shrink-0" />
                <span>{createError}</span>
              </div>
            )}
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setAddDialogOpen(false)}
              disabled={isCreating}
            >
              Cancel
            </Button>
            <Button onClick={handleAddTarget} disabled={isCreating}>
              {isCreating ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin mr-1" />
                  Adding...
                </>
              ) : (
                <>
                  <Plus className="h-4 w-4 mr-1" />
                  Add Target
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
      {/* Edit Target Dialog */}
      <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
        <DialogContent className="sm:max-w-lg max-h-[85vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Edit Target</DialogTitle>
            <DialogDescription>
              Update target details and manage credentials.
            </DialogDescription>
          </DialogHeader>

          <div className="flex flex-col gap-4 pt-2">
            <div>
              <label className="text-sm font-medium mb-1.5 block">Name</label>
              <Input
                value={editName}
                onChange={(e) => { setEditName(e.target.value); setEditError(''); }}
                disabled={isSaving}
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-1.5 block">Domain</label>
              <Input
                value={editDomain}
                onChange={(e) => { setEditDomain(e.target.value); setEditError(''); }}
                disabled={isSaving}
              />
            </div>

            {/* Credentials Section */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium flex items-center gap-1.5">
                  <KeyRound className="h-4 w-4" />
                  Credentials ({editCredentials.length})
                </label>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowAddCred(!showAddCred)}
                  disabled={isSaving}
                >
                  <Plus className="h-3 w-3 mr-1" />
                  Add
                </Button>
              </div>

              {editCredentials.length === 0 && !showAddCred && (
                <p className="text-xs text-muted-foreground py-2">No credentials configured.</p>
              )}

              {editCredentials.map((cred) => (
                <div key={cred.id} className="rounded-lg border border-border/50 bg-muted/20 p-3 mb-2">
                  {editingCredId === cred.id ? (
                    <div className="flex flex-col gap-2">
                      <Input
                        placeholder="Name"
                        value={editCredName}
                        onChange={(e) => setEditCredName(e.target.value)}
                        className="text-sm"
                      />
                      <Input
                        placeholder="Username"
                        value={editCredUsername}
                        onChange={(e) => setEditCredUsername(e.target.value)}
                        className="text-sm"
                      />
                      <Input
                        type="password"
                        placeholder="New password (leave empty to keep)"
                        value={editCredPassword}
                        onChange={(e) => setEditCredPassword(e.target.value)}
                        className="text-sm"
                      />
                      <Select value={editCredAuthType} onValueChange={setEditCredAuthType}>
                        <SelectTrigger className="text-sm">
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="form">Form Login</SelectItem>
                          <SelectItem value="basic">Basic Auth</SelectItem>
                          <SelectItem value="bearer">Bearer Token</SelectItem>
                          <SelectItem value="cookie">Cookie</SelectItem>
                          <SelectItem value="custom">Custom</SelectItem>
                        </SelectContent>
                      </Select>
                      <div className="flex gap-2 mt-1">
                        <Button size="sm" onClick={() => handleSaveCredential(cred.id)} disabled={isSaving}>
                          <Save className="h-3 w-3 mr-1" /> Save
                        </Button>
                        <Button size="sm" variant="outline" onClick={() => setEditingCredId(null)}>
                          Cancel
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <div className="flex items-center justify-between">
                      <div className="min-w-0">
                        <p className="text-sm font-medium truncate">{cred.name}</p>
                        <p className="text-xs text-muted-foreground">{cred.username} · {cred.auth_type}</p>
                      </div>
                      <div className="flex items-center gap-1 shrink-0">
                        <button
                          onClick={() => {
                            setEditingCredId(cred.id);
                            setEditCredName(cred.name);
                            setEditCredUsername(cred.username);
                            setEditCredPassword('');
                            setEditCredAuthType(cred.auth_type);
                          }}
                          className="p-1.5 rounded-md text-muted-foreground hover:text-fennec-orange-400 hover:bg-fennec-orange-500/10 transition-colors"
                        >
                          <Pencil className="h-3.5 w-3.5" />
                        </button>
                        <button
                          onClick={() => {
                            if (confirm(`Delete credential "${cred.name}"?`)) {
                              handleDeleteCredential(cred.id);
                            }
                          }}
                          className="p-1.5 rounded-md text-muted-foreground hover:text-red-400 hover:bg-red-500/10 transition-colors"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              ))}

              {/* Add new credential form */}
              {showAddCred && (
                <div className="rounded-lg border border-border/50 bg-muted/20 p-3 mb-2">
                  <div className="flex flex-col gap-2">
                    <Input
                      placeholder="Credential name"
                      value={addCredName}
                      onChange={(e) => setAddCredName(e.target.value)}
                      className="text-sm"
                    />
                    <Input
                      placeholder="Username"
                      value={addCredUsername}
                      onChange={(e) => setAddCredUsername(e.target.value)}
                      className="text-sm"
                    />
                    <Input
                      type="password"
                      placeholder="Password"
                      value={addCredPassword}
                      onChange={(e) => setAddCredPassword(e.target.value)}
                      className="text-sm"
                    />
                    <Select value={addCredAuthType} onValueChange={setAddCredAuthType}>
                      <SelectTrigger className="text-sm">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="form">Form Login</SelectItem>
                        <SelectItem value="basic">Basic Auth</SelectItem>
                        <SelectItem value="bearer">Bearer Token</SelectItem>
                        <SelectItem value="cookie">Cookie</SelectItem>
                        <SelectItem value="custom">Custom</SelectItem>
                      </SelectContent>
                    </Select>
                    <div className="flex gap-2 mt-1">
                      <Button size="sm" onClick={handleAddCredToTarget} disabled={isSaving || !addCredUsername.trim() || !addCredPassword.trim()}>
                        <Plus className="h-3 w-3 mr-1" /> Add
                      </Button>
                      <Button size="sm" variant="outline" onClick={() => setShowAddCred(false)}>
                        Cancel
                      </Button>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {editError && (
              <div className="flex items-center gap-2 rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
                <AlertTriangle className="h-4 w-4 shrink-0" />
                <span>{editError}</span>
              </div>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setEditDialogOpen(false)} disabled={isSaving}>
              Cancel
            </Button>
            <Button onClick={handleSaveTarget} disabled={isSaving}>
              {isSaving ? (
                <><Loader2 className="h-4 w-4 animate-spin mr-1" /> Saving...</>
              ) : (
                <><Save className="h-4 w-4 mr-1" /> Save Target</>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </DashboardLayout>
  );
}
