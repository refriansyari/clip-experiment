import { CheckCircle2, Clock3, Loader2, XCircle, type LucideIcon } from "lucide-react";
import type { JobStatus } from "../types/clip.type";

export const DEFAULT_MIN_DURATION = 35;
export const DEFAULT_MAX_DURATION = 180;
export const DEFAULT_MODEL = "Systran/faster-whisper-small";
export const DEFAULT_LANGUAGE = "en";
export const DEFAULT_CONTENT_TYPE = "podcast" as const;
export const JOB_POLL_INTERVAL_MS = 2200;
export const RECENT_LOG_LIMIT = 10;

export const statusCopy: Record<JobStatus, string> = {
  queued: "Queued",
  running: "Processing",
  completed: "Completed",
  failed: "Failed",
};

export const statusIcon: Record<JobStatus, LucideIcon> = {
  queued: Clock3,
  running: Loader2,
  completed: CheckCircle2,
  failed: XCircle,
};
