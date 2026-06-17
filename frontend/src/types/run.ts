export type RunProjection = {
  run_id: string;
  stage: string;
  status: string;
  missing_inputs: string[];
  current_versions?: Record<string, string>;
};

export type TimelineEvent = {
  id: string;
  actor: string;
  event_type: string;
  message: string;
};
