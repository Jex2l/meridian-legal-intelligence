const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

export type AuthSession = {
  access_token: string;
  user_id: string;
  workspace_id: string;
  name: string;
  email: string;
};

export type DocumentOut = {
  id: string;
  filename: string;
  title: string | null;
  jurisdiction: string | null;
  doc_date: string | null;
  status: string;
  source_type: string;
  created_at: string;
};

export type ChunkOut = {
  id: string;
  section_heading: string | null;
  page_number: number | null;
  chunk_index: number;
  text: string;
};

export type DocumentDetail = DocumentOut & { chunks: ChunkOut[] };

export type Citation = {
  index: number;
  chunk_id: string;
  document_id: string;
  document_filename: string;
  section_heading: string | null;
  page_number: number | null;
  text: string;
};

export type AskResponse = {
  question: string;
  answer_text: string;
  low_confidence: boolean;
  ungrounded_response_rejected: boolean;
  rejection_reason: string | null;
  citations: Citation[];
};

export type DraftResponse = {
  task: string;
  draft_text: string;
  low_confidence: boolean;
  ungrounded_response_rejected: boolean;
  rejection_reason: string | null;
  citations: Citation[];
};

class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(
  path: string,
  options: RequestInit & { token?: string } = {}
): Promise<T> {
  const { token, headers, ...rest } = options;
  const resp = await fetch(`${API_BASE_URL}${path}`, {
    ...rest,
    headers: {
      ...(rest.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...headers,
    },
  });
  if (!resp.ok) {
    let detail = resp.statusText;
    try {
      const body = await resp.json();
      detail = body.detail || detail;
    } catch {
      // ignore
    }
    throw new ApiError(resp.status, detail);
  }
  return resp.json() as Promise<T>;
}

export const api = {
  signup: (workspace_name: string, email: string, name: string, accepted_terms: boolean) =>
    request<AuthSession>("/auth/signup", {
      method: "POST",
      body: JSON.stringify({ workspace_name, email, name, accepted_terms }),
    }),

  login: (email: string) =>
    request<AuthSession>("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email }),
    }),

  listDocuments: (token: string) =>
    request<DocumentOut[]>("/documents", { token }),

  getDocument: (token: string, id: string) =>
    request<DocumentDetail>(`/documents/${id}`, { token }),

  uploadDocument: async (token: string, file: File, jurisdiction?: string) => {
    const form = new FormData();
    form.append("file", file);
    const qs = jurisdiction ? `?jurisdiction=${encodeURIComponent(jurisdiction)}` : "";
    return request<DocumentOut>(`/documents/upload${qs}`, {
      method: "POST",
      token,
      body: form,
    });
  },

  ask: (token: string, question: string, k = 5) =>
    request<AskResponse>("/ask", {
      method: "POST",
      token,
      body: JSON.stringify({ question, k }),
    }),

  draft: (token: string, task: string, k = 6) =>
    request<DraftResponse>("/draft", {
      method: "POST",
      token,
      body: JSON.stringify({ task, k }),
    }),
};

export { ApiError };
