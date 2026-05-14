import { useState, useEffect, useCallback, useRef } from 'react';
import { reviewApi } from '@/services/api';
import type { ReviewResponse, ReviewSubmitRequest } from '@/types';

interface UseReviewOptions {
  jobId: string;
  jobStatus: string;
  pollIntervalMs?: number;
}

interface UseReviewReturn {
  review: ReviewResponse | null;
  isReviewPending: boolean;
  isSubmitting: boolean;
  submitReview: (payload: ReviewSubmitRequest) => Promise<void>;
}

export function useReview({
  jobId,
  jobStatus,
  pollIntervalMs = 5000,
}: UseReviewOptions): UseReviewReturn {
  const [review, setReview] = useState<ReviewResponse | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const isAwaitingReview = jobStatus === 'awaiting_review';

  // Poll for pending review when job is awaiting_review
  useEffect(() => {
    if (!isAwaitingReview || !jobId) {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      return;
    }

    const fetchReview = async () => {
      try {
        const data = await reviewApi.getPendingReview(jobId);
        setReview(data);
        // Stop polling if review was resolved
        if (data.status !== 'pending' && intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
      } catch {
        // 404 = no pending review, ignore
      }
    };

    // Fetch immediately
    fetchReview();

    // Then poll
    intervalRef.current = setInterval(fetchReview, pollIntervalMs);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, [isAwaitingReview, jobId, pollIntervalMs]);

  // Clear review when job status changes away from awaiting_review
  useEffect(() => {
    if (!isAwaitingReview) {
      setReview(null);
    }
  }, [isAwaitingReview]);

  const submitReview = useCallback(
    async (payload: ReviewSubmitRequest) => {
      if (!jobId) return;
      setIsSubmitting(true);
      try {
        const result = await reviewApi.submitReview(jobId, payload);
        setReview(result);
      } finally {
        setIsSubmitting(false);
      }
    },
    [jobId],
  );

  return {
    review,
    isReviewPending: review?.status === 'pending',
    isSubmitting,
    submitReview,
  };
}
