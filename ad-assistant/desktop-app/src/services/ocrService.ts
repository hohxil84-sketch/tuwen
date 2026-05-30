/**
 * OCR Service Layer — Sprint-01 Task-04.
 *
 * Encapsulates all HTTP calls to the local FastAPI OCR service
 * running on ``http://127.0.0.1:9100``.
 */

const BASE_URL = "http://127.0.0.1:9100";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface OCRTextBlock {
  text: string;
  confidence: number;
  bbox: number[]; // [x1, y1, x2, y2]
}

export interface OCRResult {
  text: string;
  blocks: OCRTextBlock[];
  engine: string;
  duration_ms: number;
  image_hash?: string;
  history_id?: string;
}

export interface OCRErrorDetail {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

export interface APIResponse<T = unknown> {
  success: boolean;
  data: T;
  error: OCRErrorDetail | null;
  request_id: string;
}

export interface HealthStatus {
  status: string;
  engine: string;
  error_code?: string;
  message?: string;
}

export interface HistoryRecord {
  id: string;
  image_filename: string;
  image_hash: string;
  local_copy_path: string | null;
  text: string;
  blocks: OCRTextBlock[];
  engine: string;
  duration_ms: number;
  created_at: string;
}

export interface HistoryListData {
  items: HistoryRecord[];
  limit: number;
  offset: number;
}

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

async function request<T>(url: string, options?: RequestInit): Promise<APIResponse<T>> {
  const response = await fetch(url, {
    ...options,
    headers: {
      ...(options?.headers || {}),
    },
  });

  const body = await response.json();

  if (!response.ok || !body.success) {
    const err: OCRErrorDetail = body.error || {
      code: "NETWORK_ERROR",
      message: `Request failed with status ${response.status}`,
    };
    throw err;
  }

  return body as APIResponse<T>;
}

/**
 * Upload an image file to the local OCR service and return recognized text.
 */
export async function uploadAndOCR(imageFile: File): Promise<OCRResult> {
  const formData = new FormData();
  formData.append("image", imageFile);

  const response = await request<OCRResult>(`${BASE_URL}/local/ocr`, {
    method: "POST",
    body: formData,
  });

  return response.data;
}

/**
 * Check whether the local OCR engine is ready.
 */
export async function checkHealth(): Promise<HealthStatus> {
  const response = await request<HealthStatus>(`${BASE_URL}/local/ocr/health`);
  return response.data;
}

/**
 * Fetch paginated OCR history list (most recent first).
 */
export async function getHistory(
  limit: number = 50,
  offset: number = 0,
): Promise<HistoryListData> {
  const response = await request<HistoryListData>(
    `${BASE_URL}/local/ocr/history?limit=${limit}&offset=${offset}`,
  );
  return response.data;
}

/**
 * Fetch a single OCR history record by ID.
 */
export async function getHistoryDetail(id: string): Promise<HistoryRecord> {
  const response = await request<HistoryRecord>(
    `${BASE_URL}/local/ocr/history/${encodeURIComponent(id)}`,
  );
  return response.data;
}
