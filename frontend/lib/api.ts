/**
 * API Client for IACUC Protocol Generator Backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export interface ProtocolSummary {
  id: string;
  protocol_number: string | null;
  title: string;
  status: string;
  pi_name: string;
  species: string[];
  total_animals: number;
  usda_category: string;
  completeness: number;
  created_at: string;
  updated_at: string;
}

export interface Protocol {
  id: string;
  title: string;
  status: string;
  principal_investigator: {
    name: string;
    email: string;
    department?: string;
  };
  department: string;
  lay_summary: string;
  animals: Array<{
    species: string;
    strain?: string;
    sex: string;
    total_number: number;
    source: string;
  }>;
  [key: string]: unknown;
}

export interface CreateProtocolRequest {
  title: string;
  pi_name: string;
  pi_email: string;
  department: string;
}

export interface UpdateProtocolRequest {
  title?: string;
  lay_summary?: string;
  scientific_objectives?: string;
  scientific_rationale?: string;
  replacement_statement?: string;
  reduction_statement?: string;
  refinement_statement?: string;
  experimental_design?: string;
  statistical_methods?: string;
  monitoring_schedule?: string;
  euthanasia_method?: string;
}

export interface AddAnimalRequest {
  species: string;
  strain?: string;
  sex: string;
  total_number: number;
  source: string;
  genetic_modification?: string;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl;
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: "Unknown error" }));
      throw new Error(error.detail || `HTTP ${response.status}`);
    }

    return response.json();
  }

  // Protocol endpoints
  async listProtocols(status?: string, piName?: string): Promise<{ protocols: ProtocolSummary[]; total: number }> {
    const params = new URLSearchParams();
    if (status) params.append("status", status);
    if (piName) params.append("pi_name", piName);
    const query = params.toString();
    return this.request(`/protocols${query ? `?${query}` : ""}`);
  }

  async getProtocol(id: string): Promise<Protocol> {
    return this.request(`/protocols/${id}`);
  }

  async getProtocolSummary(id: string): Promise<ProtocolSummary> {
    return this.request(`/protocols/${id}/summary`);
  }

  async createProtocol(data: CreateProtocolRequest): Promise<{ id: string; message: string; completeness: number }> {
    return this.request("/protocols", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async updateProtocol(id: string, data: UpdateProtocolRequest): Promise<{ id: string; message: string; completeness: number }> {
    return this.request(`/protocols/${id}`, {
      method: "PUT",
      body: JSON.stringify(data),
    });
  }

  async deleteProtocol(id: string): Promise<{ message: string }> {
    return this.request(`/protocols/${id}`, {
      method: "DELETE",
    });
  }

  async addAnimal(protocolId: string, data: AddAnimalRequest): Promise<{ message: string; total_animals: number }> {
    return this.request(`/protocols/${protocolId}/animals`, {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async updateStatus(protocolId: string, status: string): Promise<{ id: string; status: string; message: string }> {
    return this.request(`/protocols/${protocolId}/status?status=${status}`, {
      method: "PUT",
    });
  }

  async getMissingSections(protocolId: string): Promise<{ protocol_id: string; missing_sections: string[]; completeness: number; is_complete: boolean }> {
    return this.request(`/protocols/${protocolId}/missing-sections`);
  }

  // Review endpoints
  async listPendingReviews(): Promise<{ pending_reviews: unknown[] }> {
    return this.request("/review/pending");
  }

  async getWorkflow(workflowId: string): Promise<unknown> {
    return this.request(`/review/workflows/${workflowId}`);
  }

  async approveCheckpoint(
    workflowId: string,
    checkpointType: string,
    reviewerId: string,
    comments?: string
  ): Promise<unknown> {
    return this.request(`/review/workflows/${workflowId}/checkpoints/${checkpointType}/approve`, {
      method: "POST",
      body: JSON.stringify({ reviewer_id: reviewerId, comments }),
    });
  }

  async rejectCheckpoint(
    workflowId: string,
    checkpointType: string,
    reviewerId: string,
    comments: string,
    specificIssues?: string[]
  ): Promise<unknown> {
    return this.request(`/review/workflows/${workflowId}/checkpoints/${checkpointType}/reject`, {
      method: "POST",
      body: JSON.stringify({ reviewer_id: reviewerId, comments, specific_issues: specificIssues }),
    });
  }

  // Run AI Crew
  async runAICrew(protocolId: string, verbose: boolean = false): Promise<{
    success: boolean;
    protocol_id: string;
    agent_outputs: Record<string, string>;
    errors: string[];
    message: string;
  }> {
    return this.request(`/review/protocols/${protocolId}/run-crew`, {
      method: "POST",
      body: JSON.stringify({ verbose }),
    });
  }

  // Get AI Review Results
  async getAIResults(protocolId: string): Promise<{
    success: boolean;
    protocol_id: string;
    agent_outputs: Record<string, string>;
    errors: string[];
    reviewed_at?: string;
  } | null> {
    try {
      return await this.request(`/review/protocols/${protocolId}/ai-results`);
    } catch {
      return null;
    }
  }

  // Get Comparison Data
  async getComparisonData(protocolId: string): Promise<{
    protocol_id: string;
    comparisons: Array<{
      agent: string;
      field: string;
      description: string;
      original_value: string;
      ai_suggestion: string;
      secondary_fields: string[];
    }>;
  }> {
    return this.request(`/review/protocols/${protocolId}/comparison`);
  }

  // Apply AI Suggestion
  async applySuggestion(protocolId: string, agent: string, field?: string): Promise<{
    success: boolean;
    protocol_id: string;
    field_updated: string;
    old_value: string | null;
    new_value: string;
    message: string;
  }> {
    return this.request(`/review/protocols/${protocolId}/apply-suggestion`, {
      method: "POST",
      body: JSON.stringify({ agent, field }),
    });
  }

  // Health check
  async healthCheck(): Promise<{ status: string; version: string }> {
    const response = await fetch(`${this.baseUrl.replace("/api/v1", "")}/health`);
    if (!response.ok) throw new Error("Health check failed");
    return response.json();
  }
}

export const api = new ApiClient();
export default api;
