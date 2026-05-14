import { useEffect, useState } from 'react';
import { AlertTriangle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import type { ReviewResponse } from '@/types';

interface ReviewBannerProps {
  review: ReviewResponse;
  onOpenDialog: () => void;
}

export function ReviewBanner({ review, onOpenDialog }: ReviewBannerProps) {
  const [secondsLeft, setSecondsLeft] = useState(
    review.seconds_remaining ?? review.timeout_seconds,
  );

  useEffect(() => {
    setSecondsLeft(review.seconds_remaining ?? review.timeout_seconds);
  }, [review.seconds_remaining, review.timeout_seconds]);

  useEffect(() => {
    if (secondsLeft <= 0) return;
    const timer = setInterval(() => {
      setSecondsLeft((prev) => Math.max(0, prev - 1));
    }, 1000);
    return () => clearInterval(timer);
  }, [secondsLeft]);

  const minutes = Math.floor(secondsLeft / 60);
  const seconds = secondsLeft % 60;
  const progressPercent =
    ((review.timeout_seconds - secondsLeft) / review.timeout_seconds) * 100;

  return (
    <div className="rounded-lg border border-amber-500/40 bg-amber-500/10 p-4">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <AlertTriangle className="h-5 w-5 text-amber-400 shrink-0" />
          <div>
            <div className="flex items-center gap-2">
              <span className="font-semibold text-amber-200">
                Human Review Required
              </span>
              <Badge variant="outline" className="border-amber-500/40 text-amber-300 text-xs">
                Cycle {review.review_cycle}
              </Badge>
            </div>
            <p className="text-sm text-amber-300/80 mt-0.5">
              {secondsLeft > 0
                ? `Auto-approve in ${minutes}:${seconds.toString().padStart(2, '0')}`
                : 'Auto-approving...'}
            </p>
          </div>
        </div>
        <Button
          onClick={onOpenDialog}
          variant="outline"
          className="border-amber-500/40 text-amber-200 hover:bg-amber-500/20"
        >
          Review Hypotheses
        </Button>
      </div>
      <Progress value={progressPercent} className="mt-3 h-1.5 bg-amber-900/30" />
    </div>
  );
}
