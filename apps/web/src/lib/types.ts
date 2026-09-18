export type JobStatus = "queued" | "running" | "succeeded" | "failed";

export interface JobError {
  code: string;
  message: string;
}

export interface AnalysisResult {
  face_count: number;
  emotions: Record<string, number>;
  action_units: Record<string, number>;
  landmarks: number[][];
  overlay_image_base64: string;
}

export interface JobResponse {
  job_id: string;
  status: JobStatus;
  error: JobError | null;
  result: AnalysisResult | null;
}
