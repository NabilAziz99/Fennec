import { useState, useMemo } from 'react';
import { Check, X, Plus, Trash2 } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { Card, CardContent } from '@/components/ui/card';
import type {
  ReviewResponse,
  ReviewSubmitRequest,
  HypothesisEditItem,
  NewHypothesisItem,
} from '@/types';

interface HypothesisReviewDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  review: ReviewResponse;
  onSubmit: (payload: ReviewSubmitRequest) => Promise<void>;
  isSubmitting: boolean;
}

interface EditState {
  action: 'approve' | 'reject';
  title?: string;
  description?: string;
  priority?: number;
}

export function HypothesisReviewDialog({
  open,
  onOpenChange,
  review,
  onSubmit,
  isSubmitting,
}: HypothesisReviewDialogProps) {
  const hypotheses = review.hypotheses_snapshot;

  const pendingHypotheses = useMemo(
    () => hypotheses.filter((h) => h.status === 'pending'),
    [hypotheses],
  );
  const otherHypotheses = useMemo(
    () => hypotheses.filter((h) => h.status !== 'pending'),
    [hypotheses],
  );

  // Initialize edits: all pending hypotheses default to "approve"
  const [edits, setEdits] = useState<Record<string, EditState>>(() => {
    const initial: Record<string, EditState> = {};
    for (const h of pendingHypotheses) {
      initial[h.id as string] = { action: 'approve' };
    }
    return initial;
  });

  const [newHypotheses, setNewHypotheses] = useState<NewHypothesisItem[]>([]);
  const [guidanceNotes, setGuidanceNotes] = useState('');
  const [showAddForm, setShowAddForm] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newDescription, setNewDescription] = useState('');
  const [newPriority, setNewPriority] = useState(0.5);

  const approvedCount = Object.values(edits).filter(
    (e) => e.action === 'approve',
  ).length;
  const rejectedCount = Object.values(edits).filter(
    (e) => e.action === 'reject',
  ).length;

  const toggleAction = (hypId: string) => {
    setEdits((prev) => ({
      ...prev,
      [hypId]: {
        ...prev[hypId],
        action: prev[hypId]?.action === 'approve' ? 'reject' : 'approve',
      },
    }));
  };

  const updateEdit = (
    hypId: string,
    field: 'title' | 'description' | 'priority',
    value: string | number,
  ) => {
    setEdits((prev) => ({
      ...prev,
      [hypId]: { ...prev[hypId], [field]: value },
    }));
  };

  const addNewHypothesis = () => {
    if (!newTitle.trim()) return;
    setNewHypotheses((prev) => [
      ...prev,
      {
        title: newTitle.trim(),
        description: newDescription.trim(),
        priority: newPriority,
        skills: [],
        required_agent: 'pentester',
      },
    ]);
    setNewTitle('');
    setNewDescription('');
    setNewPriority(0.5);
    setShowAddForm(false);
  };

  const removeNewHypothesis = (idx: number) => {
    setNewHypotheses((prev) => prev.filter((_, i) => i !== idx));
  };

  const handleSubmit = async () => {
    const editItems: HypothesisEditItem[] = Object.entries(edits).map(
      ([hypothesis_id, edit]) => ({
        hypothesis_id,
        action: edit.action,
        ...(edit.title !== undefined && { title: edit.title }),
        ...(edit.description !== undefined && { description: edit.description }),
        ...(edit.priority !== undefined && { priority: edit.priority }),
      }),
    );

    await onSubmit({
      edits: editItems,
      new_hypotheses: newHypotheses,
      guidance_notes: guidanceNotes,
    });

    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-3">
            Hypothesis Review
            <Badge variant="outline" className="text-xs">
              Cycle {review.review_cycle}
            </Badge>
          </DialogTitle>
        </DialogHeader>

        {/* Summary badges */}
        <div className="flex gap-2 flex-wrap">
          <Badge className="bg-emerald-500/20 text-emerald-300 border-emerald-500/30">
            {approvedCount} Approved
          </Badge>
          <Badge className="bg-red-500/20 text-red-300 border-red-500/30">
            {rejectedCount} Rejected
          </Badge>
          {newHypotheses.length > 0 && (
            <Badge className="bg-blue-500/20 text-blue-300 border-blue-500/30">
              {newHypotheses.length} New
            </Badge>
          )}
        </div>

        <Separator />

        {/* Pending hypotheses - editable */}
        {pendingHypotheses.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-muted-foreground mb-3">
              Pending Hypotheses ({pendingHypotheses.length})
            </h3>
            <div className="space-y-3">
              {pendingHypotheses.map((h) => {
                const hypId = h.id as string;
                const edit = edits[hypId];
                const isRejected = edit?.action === 'reject';

                return (
                  <Card
                    key={hypId}
                    className={`transition-all ${
                      isRejected
                        ? 'opacity-50 border-red-500/40'
                        : 'border-emerald-500/20'
                    }`}
                  >
                    <CardContent className="p-4 space-y-3">
                      <div className="flex items-start justify-between gap-3">
                        <div className="flex-1 space-y-2">
                          <div>
                            <Label className="text-xs text-muted-foreground">
                              Title
                            </Label>
                            <Input
                              defaultValue={h.title as string}
                              onChange={(e) =>
                                updateEdit(hypId, 'title', e.target.value)
                              }
                              disabled={isRejected}
                              className="mt-1"
                            />
                          </div>
                          <div>
                            <Label className="text-xs text-muted-foreground">
                              Description
                            </Label>
                            <Input
                              defaultValue={(h.description as string) || ''}
                              onChange={(e) =>
                                updateEdit(hypId, 'description', e.target.value)
                              }
                              disabled={isRejected}
                              className="mt-1"
                            />
                          </div>
                          <div className="flex items-center gap-4">
                            <div className="w-24">
                              <Label className="text-xs text-muted-foreground">
                                Priority
                              </Label>
                              <Input
                                type="number"
                                step="0.1"
                                min="0"
                                max="1"
                                defaultValue={h.priority as number}
                                onChange={(e) =>
                                  updateEdit(
                                    hypId,
                                    'priority',
                                    parseFloat(e.target.value),
                                  )
                                }
                                disabled={isRejected}
                                className="mt-1"
                              />
                            </div>
                            {Array.isArray(h.skills) && h.skills.length > 0 && (
                              <div className="flex gap-1 flex-wrap mt-4">
                                {(h.skills as string[]).map((s) => (
                                  <Badge
                                    key={s}
                                    variant="outline"
                                    className="text-xs"
                                  >
                                    {s}
                                  </Badge>
                                ))}
                              </div>
                            )}
                          </div>
                        </div>
                        <Button
                          variant={isRejected ? 'destructive' : 'outline'}
                          size="icon"
                          onClick={() => toggleAction(hypId)}
                          className="shrink-0 mt-5"
                          title={isRejected ? 'Click to approve' : 'Click to reject'}
                        >
                          {isRejected ? (
                            <X className="h-4 w-4" />
                          ) : (
                            <Check className="h-4 w-4" />
                          )}
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </div>
        )}

        {/* Completed/blocked hypotheses - read-only */}
        {otherHypotheses.length > 0 && (
          <div>
            <h3 className="text-sm font-medium text-muted-foreground mb-2">
              Other Hypotheses ({otherHypotheses.length})
            </h3>
            <div className="space-y-1">
              {otherHypotheses.map((h) => (
                <div
                  key={h.id as string}
                  className="flex items-center gap-2 text-sm text-muted-foreground px-2 py-1"
                >
                  <Badge variant="outline" className="text-xs capitalize">
                    {h.status as string}
                  </Badge>
                  <span className="truncate">{h.title as string}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        <Separator />

        {/* New hypotheses */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <h3 className="text-sm font-medium text-muted-foreground">
              Add New Hypotheses
            </h3>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowAddForm(!showAddForm)}
            >
              <Plus className="h-4 w-4 mr-1" />
              Add
            </Button>
          </div>

          {newHypotheses.map((nh, idx) => (
            <div
              key={idx}
              className="flex items-center gap-2 px-3 py-2 rounded border border-blue-500/20 mb-2"
            >
              <span className="flex-1 text-sm truncate">{nh.title}</span>
              <Badge variant="outline" className="text-xs">
                p={nh.priority}
              </Badge>
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6"
                onClick={() => removeNewHypothesis(idx)}
              >
                <Trash2 className="h-3 w-3" />
              </Button>
            </div>
          ))}

          {showAddForm && (
            <Card className="border-dashed border-blue-500/30">
              <CardContent className="p-3 space-y-2">
                <Input
                  placeholder="Hypothesis title"
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                />
                <Input
                  placeholder="Description (optional)"
                  value={newDescription}
                  onChange={(e) => setNewDescription(e.target.value)}
                />
                <div className="flex items-center gap-2">
                  <Label className="text-xs shrink-0">Priority</Label>
                  <Input
                    type="number"
                    step="0.1"
                    min="0"
                    max="1"
                    value={newPriority}
                    onChange={(e) => setNewPriority(parseFloat(e.target.value))}
                    className="w-20"
                  />
                  <Button size="sm" onClick={addNewHypothesis} className="ml-auto">
                    Add
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        <Separator />

        {/* Guidance notes */}
        <div>
          <Label className="text-sm text-muted-foreground">
            Guidance Notes (optional)
          </Label>
          <textarea
            value={guidanceNotes}
            onChange={(e) => setGuidanceNotes(e.target.value)}
            placeholder="Additional instructions for the agent..."
            className="mt-1 w-full rounded-md border bg-transparent px-3 py-2 text-sm min-h-[60px] resize-y"
          />
        </div>

        <DialogFooter>
          <Button variant="ghost" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={isSubmitting}>
            {isSubmitting ? 'Submitting...' : 'Submit Review'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
