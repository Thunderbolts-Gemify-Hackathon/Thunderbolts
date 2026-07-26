import { api } from "./http";

export type AgentAction = {
  id: string;
  profil_id: string;
  type_action: string;
  payload_json: string;
  statut: string;
  message?: string | null;
  created_at: string;
};

export type AgentDigest = {
  alertes_stock: Array<Record<string, unknown>>;
  budget: Record<string, unknown>;
  ce_soir: Record<string, unknown> | null;
  actions: AgentAction[];
  memories: Array<Record<string, unknown>>;
  resume: string;
};

export function getAgentDigest(profilId: string, token: string) {
  return api<AgentDigest>(`/ia/${profilId}/agent/digest`, { token });
}

export function respondAgentAction(
  profilId: string,
  token: string,
  actionId: string,
  decision: "accepte" | "refuse"
) {
  return api<AgentAction>(
    `/ia/${profilId}/agent/actions/${actionId}/respond`,
    { method: "POST", token, body: { decision } }
  );
}
