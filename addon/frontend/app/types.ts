// Based on addon/app/models/trace.py
export interface Span {
  id: string;
  trace_id: string;
  parent_id?: string;
  started_at: string;
  ended_at: string;
  span_type: string;
  span_data: { [key: string]: any };
  error?: any;
} 