export interface AskRequest {
  question: string;
}

export interface AskResponse {
  answer: string;
  generated_sql: string | null;
  execution_time_ms: number | null;
  provider: string;
  model: string;
  conversation_id: string;
  created_at: string;
}

export interface HistoryItem {
  id: string;
  question: string;
  answer: string;
  generated_sql: string | null;
  execution_time_ms: number | null;
  provider: string;
  created_at: string;
}
