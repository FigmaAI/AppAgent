// types.ts

export interface ServerResponse {
  status: string;
  message: string;
}

export interface ExploreMessage {
  type: 'explore';
  taskDesc: string;
  personaDesc: string;
}

export interface InitMessage {
  type: 'init';
  url: string;
  password?: string;
}

export interface ReportUpdateMessage {
  type: 'report-update';
  content: string;
}

export type PluginMessage =
  | ExploreMessage
  | InitMessage
  | ReportUpdateMessage
  | { type: 'stop-exploration' }
  | { type: 'exploration-status' };

export interface ParsedReport {
  title: string;
  taskName: string;
  taskDesc: string;
  personaDesc: string;
  rounds: Promise<ParsedRound>[];
}
  
export interface ParsedRound {
  images: string[];
  observation: string;
  thoughts: string[];
  action: string;
  summary: string;
  decision: string;
}
