"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import toast from "react-hot-toast";
import { createJob, deleteJobs, getJob, getJobs } from "../lib/apiClient";
import {
  DEFAULT_CONTENT_TYPE,
  DEFAULT_LANGUAGE,
  DEFAULT_MAX_DURATION,
  DEFAULT_MIN_DURATION,
  DEFAULT_MODEL,
  JOB_POLL_INTERVAL_MS,
  RECENT_LOG_LIMIT,
} from "../lib/constants";
import { isActiveJob } from "../lib/utils";
import type { ClipJob, ContentType, CropMode } from "../types/clip.type";
import { ControlPanel } from "./_components/ControlPanel";
import { DeleteAllToast } from "./_components/DeleteAllToast";
import { HistorySection } from "./_components/HistorySection";
import { ResultsSection } from "./_components/ResultsSection";
import { SiteFooter } from "./_components/SiteFooter";
import { StatusPanel } from "./_components/StatusPanel";
import { Topbar } from "./_components/Topbar";

export default function HomePage() {
  const [url, setUrl] = useState("");
  const [minDuration, setMinDuration] = useState(DEFAULT_MIN_DURATION);
  const [maxDuration, setMaxDuration] = useState(DEFAULT_MAX_DURATION);
  const [cropMode, setCropMode] = useState<CropMode>("person");
  const [contentType, setContentType] = useState<ContentType>(DEFAULT_CONTENT_TYPE);
  const [useLlm, setUseLlm] = useState(false);
  const [job, setJob] = useState<ClipJob | null>(null);
  const [jobs, setJobs] = useState<ClipJob[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState("");

  const activeJobId = job?.id;
  const isBusy = isActiveJob(job);
  const latestLogs = useMemo(() => job?.logs.slice(-RECENT_LOG_LIMIT) ?? [], [job]);

  const loadJobs = useCallback(async () => {
    setJobs(await getJobs());
  }, []);

  useEffect(() => {
    loadJobs().catch(() => undefined);
  }, [loadJobs]);

  useEffect(() => {
    if (!activeJobId) return;

    const interval = window.setInterval(async () => {
      const nextJob = await getJob(activeJobId);
      setJob(nextJob);

      if (nextJob.status === "completed" || nextJob.status === "failed") {
        loadJobs().catch(() => undefined);
      }
    }, JOB_POLL_INTERVAL_MS);

    return () => window.clearInterval(interval);
  }, [activeJobId, loadJobs]);

  const handleStartJob = useCallback(async () => {
    const trimmedUrl = url.trim();
    setError("");

    if (!trimmedUrl) {
      setError("YouTube URL is required.");
      return;
    }

    setIsSubmitting(true);

    try {
      const nextJob = await toast.promise(
        createJob({
          url: trimmedUrl,
          min_duration: minDuration,
          max_duration: maxDuration,
          model: DEFAULT_MODEL,
          language: DEFAULT_LANGUAGE,
          burn_subtitles: true,
          crop_mode: cropMode,
          content_type: contentType,
          use_llm: useLlm,
        }),
        {
          loading: "Preparing clip job...",
          success: "Clipping started!",
          error: "Failed to start clipping",
        },
      );

      setJob(nextJob);
      await loadJobs();
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Failed to start job.");
    } finally {
      setIsSubmitting(false);
    }
  }, [contentType, cropMode, loadJobs, maxDuration, minDuration, url, useLlm]);

  const handleDeleteAllConfirmed = useCallback(async () => {
    await toast.promise(deleteJobs(), {
      loading: "Deleting history...",
      success: "All history deleted!",
      error: "Failed to delete history",
    });

    setJob(null);
    await loadJobs();
  }, [loadJobs]);

  const handleDeleteAll = useCallback(() => {
    toast((item) => <DeleteAllToast toastId={item.id} onConfirm={handleDeleteAllConfirmed} />, {
      duration: Infinity,
    });
  }, [handleDeleteAllConfirmed]);

  return (
    <main className="shell">
      <Topbar onRefresh={loadJobs} />

      <section className="workspace">
        <ControlPanel
          contentType={contentType}
          cropMode={cropMode}
          error={error}
          isBusy={isBusy}
          isSubmitting={isSubmitting}
          maxDuration={maxDuration}
          minDuration={minDuration}
          onContentTypeChange={setContentType}
          onCropModeChange={setCropMode}
          onMaxDurationChange={setMaxDuration}
          onMinDurationChange={setMinDuration}
          onStartJob={handleStartJob}
          onUrlChange={setUrl}
          onUseLlmChange={setUseLlm}
          url={url}
          useLlm={useLlm}
        />
        <StatusPanel job={job} latestLogs={latestLogs} />
      </section>

      <ResultsSection clips={job?.clips ?? []} />
      <HistorySection jobs={jobs} onDeleteAll={handleDeleteAll} onSelectJob={setJob} />
      <SiteFooter />
    </main>
  );
}
