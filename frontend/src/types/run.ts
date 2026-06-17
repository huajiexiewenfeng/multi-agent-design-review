export type RunProjection = {
  run_id: string;
  stage: string;
  status: string;
  missing_inputs: string[];
  current_versions: Record<string, string>;
};
