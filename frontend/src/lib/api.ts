// Base API client for backend communication
const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api/v1";

interface ApiOptions extends RequestInit {
  token?: string;
}

/** Custom error class for API responses with non-ok status codes */
class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/**
 * Generic fetch wrapper that handles auth headers, JSON parsing,
 * and error extraction from the backend response body.
 */
async function apiFetch<T>(
  endpoint: string,
  options: ApiOptions = {},
): Promise<T> {
  const { token, ...fetchOptions } = options;

  // When sending FormData let the browser set Content-Type (with boundary)
  const isFormData = typeof FormData !== "undefined" && fetchOptions.body instanceof FormData;

  const headers: Record<string, string> = {
    ...(isFormData ? {} : { "Content-Type": "application/json" }),
    ...((fetchOptions.headers as Record<string, string>) || {}),
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...fetchOptions,
    headers,
  });

  if (!response.ok) {
    const error = await response
      .json()
      .catch(() => ({ detail: response.statusText }));
    throw new ApiError(response.status, error.detail || "Unknown error");
  }

  // 204 No Content – nothing to parse
  if (response.status === 204) return undefined as T;

  return response.json();
}

// Exported convenience methods
export const api = {
  get: <T>(endpoint: string, options?: ApiOptions) =>
    apiFetch<T>(endpoint, { method: "GET", ...options }),

  post: <T>(endpoint: string, body: unknown, options?: ApiOptions) =>
    apiFetch<T>(endpoint, {
      method: "POST",
      body: JSON.stringify(body),
      ...options,
    }),

  put: <T>(endpoint: string, body: unknown, options?: ApiOptions) =>
    apiFetch<T>(endpoint, {
      method: "PUT",
      body: JSON.stringify(body),
      ...options,
    }),

  del: <T>(endpoint: string, options?: ApiOptions) =>
    apiFetch<T>(endpoint, { method: "DELETE", ...options }),

  /** Upload a file via multipart/form-data. */
  upload: <T>(endpoint: string, formData: FormData, options?: ApiOptions) =>
    apiFetch<T>(endpoint, {
      method: "POST",
      body: formData,
      ...options,
    }),
};

export { ApiError };
