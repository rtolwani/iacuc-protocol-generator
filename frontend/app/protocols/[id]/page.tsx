"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Separator } from "@/components/ui/separator";
import { ChevronDown, ChevronUp, Brain, CheckCircle, AlertTriangle, ArrowRight, Check, Eye } from "lucide-react";
import api from "@/lib/api";

interface HumaneEndpoint {
  criterion: string;
  measurement: string;
  threshold: string;
  action: string;
}

interface Protocol {
  id: string;
  title: string;
  pi_name: string;
  pi_email: string;
  department: string;
  funding_sources: string;
  study_duration: string;
  lay_summary: string;
  status: string;
  created_at: string;
  animals?: Array<{
    species: string;
    strain: string;
    sex: string;
    total_number: number;
    source: string;
    genetic_modification: string;
  }>;
  scientific_objectives?: string;
  scientific_rationale?: string;
  potential_benefits?: string;
  experimental_design?: string;
  statistical_methods?: string;
  euthanasia_method?: string;
  replacement_statement?: string;
  reduction_statement?: string;
  refinement_statement?: string;
  humane_endpoints?: HumaneEndpoint[] | string;
  monitoring_schedule?: string;
}

const statusColors: Record<string, string> = {
  draft: "bg-gray-500",
  submitted: "bg-yellow-500",
  under_review: "bg-blue-500",
  approved: "bg-green-500",
  rejected: "bg-red-500",
  revision_requested: "bg-orange-500",
  expired: "bg-gray-400",
  suspended: "bg-red-400",
  terminated: "bg-red-600",
};

interface AIReviewResults {
  status?: string;
  success?: boolean;
  protocol_id?: string;
  agent_outputs: Record<string, string>;
  errors: string[];
  reviewed_at?: string;
  message?: string;
}

const agentLabels: Record<string, { name: string; description: string }> = {
  intake: { name: "Protocol Intake", description: "Extracts key parameters from submission" },
  lay_summary: { name: "Lay Summary", description: "Generates plain-language summary" },
  statistics: { name: "Statistical Review", description: "Evaluates sample size justification" },
  regulatory: { name: "Regulatory Compliance", description: "Checks USDA/PHS requirements" },
  veterinary: { name: "Veterinary Review", description: "Assesses animal health considerations" },
  alternatives: { name: "3Rs Assessment", description: "Reviews replacement, reduction, refinement" },
  procedures: { name: "Procedures Review", description: "Evaluates experimental procedures" },
  assembly: { name: "Protocol Assembly", description: "Generates complete IACUC protocol" },
};

export default function ProtocolDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [protocol, setProtocol] = useState<Protocol | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [aiResults, setAIResults] = useState<AIReviewResults | null>(null);
  const [expandedAgents, setExpandedAgents] = useState<Set<string>>(new Set());
  const [loadingAI, setLoadingAI] = useState(false);
  const [comparisonData, setComparisonData] = useState<Array<{
    agent: string;
    field: string;
    description: string;
    original_value: string;
    ai_suggestion: string;
    secondary_fields: string[];
  }>>([]);
  const [appliedAgents, setAppliedAgents] = useState<Set<string>>(new Set());
  const [applyingAgent, setApplyingAgent] = useState<string | null>(null);
  const [showComparison, setShowComparison] = useState<string | null>(null);

  const toggleAgent = (agent: string) => {
    const newExpanded = new Set(expandedAgents);
    if (newExpanded.has(agent)) {
      newExpanded.delete(agent);
    } else {
      newExpanded.add(agent);
    }
    setExpandedAgents(newExpanded);
  };

  const expandAll = () => {
    if (aiResults) {
      setExpandedAgents(new Set(Object.keys(aiResults.agent_outputs)));
    }
  };

  const collapseAll = () => {
    setExpandedAgents(new Set());
  };

  const handleApplySuggestion = async (agent: string) => {
    if (!protocol) return;
    setApplyingAgent(agent);
    try {
      const result = await api.applySuggestion(protocol.id, agent);
      if (result.success) {
        setAppliedAgents(new Set([...appliedAgents, agent]));
        // Refresh protocol data
        const updatedProtocol = await api.getProtocol(protocol.id);
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const data = updatedProtocol as any;
        const mappedProtocol: Protocol = {
          id: data.id,
          title: data.title,
          status: data.status,
          pi_name: data.principal_investigator?.name || data.pi_name || "",
          pi_email: data.principal_investigator?.email || data.pi_email || "",
          department: data.principal_investigator?.department || data.department || "",
          funding_sources: data.funding_sources || "",
          study_duration: data.study_duration || "",
          lay_summary: data.lay_summary || "",
          created_at: data.created_at || new Date().toISOString(),
          animals: data.animals?.map((a: Record<string, unknown>) => ({
            species: a.species || "",
            strain: a.strain || "",
            sex: a.sex || "",
            total_number: a.total_number || 0,
            source: a.source || "",
            genetic_modification: a.genetic_modification || "",
          })),
          scientific_objectives: data.scientific_objectives,
          scientific_rationale: data.scientific_rationale,
          potential_benefits: data.potential_benefits,
          experimental_design: data.experimental_design,
          statistical_methods: data.statistical_methods,
          euthanasia_method: data.euthanasia_method,
          replacement_statement: data.replacement_statement,
          reduction_statement: data.reduction_statement,
          refinement_statement: data.refinement_statement,
          humane_endpoints: data.humane_endpoints,
          monitoring_schedule: data.monitoring_schedule,
        };
        setProtocol(mappedProtocol);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to apply suggestion");
    } finally {
      setApplyingAgent(null);
    }
  };

  const getComparisonForAgent = (agent: string) => {
    return comparisonData.find(c => c.agent === agent);
  };

  useEffect(() => {
    const fetchProtocol = async () => {
      try {
        const rawData = await api.getProtocol(params.id as string);
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const data = rawData as any;
        // Map API response to component's Protocol interface
        const mappedProtocol: Protocol = {
          id: data.id,
          title: data.title,
          status: data.status,
          pi_name: data.principal_investigator?.name || data.pi_name || "",
          pi_email: data.principal_investigator?.email || data.pi_email || "",
          department: data.principal_investigator?.department || data.department || "",
          funding_sources: data.funding_sources || "",
          study_duration: data.study_duration || "",
          lay_summary: data.lay_summary || "",
          created_at: data.created_at || new Date().toISOString(),
          animals: data.animals?.map((a: Record<string, unknown>) => ({
            species: a.species || "",
            strain: a.strain || "",
            sex: a.sex || "",
            total_number: a.total_number || 0,
            source: a.source || "",
            genetic_modification: a.genetic_modification || "",
          })),
          scientific_objectives: data.scientific_objectives,
          scientific_rationale: data.scientific_rationale,
          potential_benefits: data.potential_benefits,
          experimental_design: data.experimental_design,
          statistical_methods: data.statistical_methods,
          euthanasia_method: data.euthanasia_method,
          replacement_statement: data.replacement_statement,
          reduction_statement: data.reduction_statement,
          refinement_statement: data.refinement_statement,
          humane_endpoints: data.humane_endpoints,
          monitoring_schedule: data.monitoring_schedule,
        };
        setProtocol(mappedProtocol);
        
        // Fetch AI results if protocol is under review or later
        if (["under_review", "approved", "rejected", "revision_requested"].includes(data.status)) {
          const results = await api.getAIResults(params.id as string);
          if (results) {
            setAIResults(results);
          }
          // Also fetch comparison data
          try {
            const comparison = await api.getComparisonData(params.id as string);
            if (comparison.comparisons) {
              setComparisonData(comparison.comparisons);
            }
          } catch {
            // Comparison data is optional
          }
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to load protocol");
      } finally {
        setLoading(false);
      }
    };

    if (params.id) {
      fetchProtocol();
    }
  }, [params.id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading protocol...</p>
        </div>
      </div>
    );
  }

  if (error || !protocol) {
    return (
      <div className="max-w-3xl mx-auto">
        <Alert variant="destructive">
          <AlertDescription>{error || "Protocol not found"}</AlertDescription>
        </Alert>
        <div className="mt-4">
          <Link href="/protocols">
            <Button variant="outline">Back to Protocols</Button>
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">{protocol.title}</h1>
          <p className="text-muted-foreground mt-1">
            Protocol ID: {protocol.id}
          </p>
        </div>
        <Badge className={statusColors[protocol.status] || "bg-gray-500"}>
          {protocol.status.replace("_", " ").toUpperCase()}
        </Badge>
      </div>

      <div className="flex gap-2">
        <Link href="/protocols">
          <Button variant="outline">Back to List</Button>
        </Link>
        <Button variant="outline" onClick={() => window.print()}>
          Print / Export
        </Button>
        {protocol.status === "draft" && (
          <Button 
            onClick={async () => {
              try {
                await api.updateStatus(protocol.id, "submitted");
                setProtocol({ ...protocol, status: "submitted" });
              } catch (err) {
                setError(err instanceof Error ? err.message : "Failed to submit");
              }
            }}
          >
            Submit for Review
          </Button>
        )}
        {protocol.status === "submitted" && (
          <Button 
            onClick={async () => {
              try {
                setLoadingAI(true);
                setError(null);
                const result = await api.runAICrew(protocol.id, false);
                if (result.success) {
                  setProtocol({ ...protocol, status: "under_review" });
                  setAIResults(result);
                } else {
                  setError(result.message || "AI review failed");
                }
              } catch (err) {
                setError(err instanceof Error ? err.message : "Failed to run AI review");
              } finally {
                setLoadingAI(false);
              }
            }}
            disabled={loadingAI}
          >
            {loadingAI ? "Running AI Review..." : "Run AI Review"}
          </Button>
        )}
      </div>

      {/* AI Review Results */}
      {aiResults && (aiResults.success || aiResults.status === "complete") && (
        <Card className="border-blue-200 bg-blue-50/50">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Brain className="h-5 w-5 text-blue-600" />
                <CardTitle className="text-blue-900">AI Review Results</CardTitle>
              </div>
              <div className="flex gap-2">
                <Button variant="ghost" size="sm" onClick={expandAll}>
                  Expand All
                </Button>
                <Button variant="ghost" size="sm" onClick={collapseAll}>
                  Collapse All
                </Button>
              </div>
            </div>
            <CardDescription>
              Analysis from {Object.keys(aiResults.agent_outputs).length} AI agents
              {aiResults.reviewed_at && ` • Reviewed ${new Date(aiResults.reviewed_at).toLocaleString()}`}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {Object.entries(aiResults.agent_outputs).map(([agent, output]) => {
              const info = agentLabels[agent] || { name: agent, description: "" };
              const isExpanded = expandedAgents.has(agent);
              const comparison = getComparisonForAgent(agent);
              const isApplied = appliedAgents.has(agent);
              const isApplying = applyingAgent === agent;
              const isShowingComparison = showComparison === agent;
              
              return (
                <div key={agent} className="bg-white rounded-lg border">
                  <div className="p-4 flex items-center justify-between">
                    <button
                      onClick={() => toggleAgent(agent)}
                      className="flex items-center gap-3 flex-1 text-left hover:opacity-80"
                    >
                      {isApplied ? (
                        <Check className="h-4 w-4 text-green-600" />
                      ) : (
                        <CheckCircle className="h-4 w-4 text-blue-600" />
                      )}
                      <div>
                        <p className="font-medium">{info.name}</p>
                        <p className="text-sm text-muted-foreground">{info.description}</p>
                      </div>
                    </button>
                    <div className="flex items-center gap-2">
                      {comparison && !isApplied && (
                        <>
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => setShowComparison(isShowingComparison ? null : agent)}
                          >
                            <Eye className="h-4 w-4 mr-1" />
                            Compare
                          </Button>
                          <Button
                            size="sm"
                            onClick={() => handleApplySuggestion(agent)}
                            disabled={isApplying}
                            className="bg-green-600 hover:bg-green-700"
                          >
                            {isApplying ? (
                              <>Applying...</>
                            ) : (
                              <>
                                <ArrowRight className="h-4 w-4 mr-1" />
                                Apply
                              </>
                            )}
                          </Button>
                        </>
                      )}
                      {isApplied && (
                        <Badge className="bg-green-100 text-green-800">Applied</Badge>
                      )}
                      <button onClick={() => toggleAgent(agent)}>
                        {isExpanded ? (
                          <ChevronUp className="h-5 w-5 text-gray-400" />
                        ) : (
                          <ChevronDown className="h-5 w-5 text-gray-400" />
                        )}
                      </button>
                    </div>
                  </div>
                  
                  {/* Comparison View */}
                  {isShowingComparison && comparison && (
                    <div className="px-4 pb-4 border-t bg-amber-50">
                      <div className="mt-3 grid md:grid-cols-2 gap-4">
                        <div>
                          <p className="text-sm font-medium text-gray-700 mb-2">Original Value</p>
                          <div className="bg-white border rounded p-3 text-sm max-h-48 overflow-y-auto">
                            {comparison.original_value || "(not set)"}
                          </div>
                        </div>
                        <div>
                          <p className="text-sm font-medium text-green-700 mb-2">AI Suggestion</p>
                          <div className="bg-green-50 border border-green-200 rounded p-3 text-sm max-h-48 overflow-y-auto whitespace-pre-wrap">
                            {comparison.ai_suggestion.substring(0, 500)}
                            {comparison.ai_suggestion.length > 500 && "..."}
                          </div>
                        </div>
                      </div>
                      <div className="mt-3 flex justify-end gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setShowComparison(null)}
                        >
                          Close
                        </Button>
                        <Button
                          size="sm"
                          onClick={() => {
                            handleApplySuggestion(agent);
                            setShowComparison(null);
                          }}
                          disabled={isApplying}
                          className="bg-green-600 hover:bg-green-700"
                        >
                          Apply This Suggestion
                        </Button>
                      </div>
                    </div>
                  )}
                  
                  {/* Full Output View */}
                  {isExpanded && !isShowingComparison && (
                    <div className="px-4 pb-4 border-t">
                      <div className="mt-3 bg-gray-50 rounded p-4 text-sm whitespace-pre-wrap font-mono max-h-96 overflow-y-auto">
                        {output || "No output available"}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
            
            {aiResults.errors && aiResults.errors.length > 0 && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <AlertTriangle className="h-4 w-4 text-red-600" />
                  <p className="font-medium text-red-900">Errors during review</p>
                </div>
                <ul className="list-disc list-inside text-sm text-red-700">
                  {aiResults.errors.map((err, i) => (
                    <li key={i}>{err}</li>
                  ))}
                </ul>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Loading AI indicator */}
      {loadingAI && (
        <Card className="border-yellow-200 bg-yellow-50/50">
          <CardContent className="py-8">
            <div className="flex items-center justify-center gap-4">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-yellow-600"></div>
              <div>
                <p className="font-medium text-yellow-900">AI Review in Progress</p>
                <p className="text-sm text-yellow-700">This typically takes 60-90 seconds...</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Basic Information */}
      <Card>
        <CardHeader>
          <CardTitle>Basic Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <p className="text-sm text-muted-foreground">Principal Investigator</p>
              <p className="font-medium">{protocol.pi_name}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Email</p>
              <p className="font-medium">{protocol.pi_email}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Department</p>
              <p className="font-medium">{protocol.department}</p>
            </div>
            <div>
              <p className="text-sm text-muted-foreground">Study Duration</p>
              <p className="font-medium">{protocol.study_duration || "Not specified"}</p>
            </div>
            <div className="md:col-span-2">
              <p className="text-sm text-muted-foreground">Funding Sources</p>
              <p className="font-medium">{protocol.funding_sources || "Not specified"}</p>
            </div>
          </div>
          <Separator />
          <div>
            <p className="text-sm text-muted-foreground mb-2">Lay Summary</p>
            <p>{protocol.lay_summary}</p>
          </div>
        </CardContent>
      </Card>

      {/* Animals */}
      {protocol.animals && protocol.animals.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Animals</CardTitle>
            <CardDescription>
              Species and strains used in this study
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {protocol.animals.map((animal, index) => (
                <div key={index} className="p-3 bg-muted rounded-md">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="font-medium">
                        {animal.species}
                        {animal.strain && ` (${animal.strain})`}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {animal.sex} | n={animal.total_number} | Source: {animal.source}
                      </p>
                      {animal.genetic_modification && (
                        <p className="text-sm text-muted-foreground">
                          Genetic Modification: {animal.genetic_modification}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Scientific Rationale */}
      {(protocol.scientific_objectives || protocol.scientific_rationale || protocol.potential_benefits) && (
        <Card>
          <CardHeader>
            <CardTitle>Scientific Rationale</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {protocol.scientific_objectives && (
              <div>
                <p className="text-sm text-muted-foreground mb-1">Scientific Objectives</p>
                <p>{protocol.scientific_objectives}</p>
              </div>
            )}
            {protocol.scientific_rationale && (
              <div>
                <p className="text-sm text-muted-foreground mb-1">Rationale for Animal Use</p>
                <p>{protocol.scientific_rationale}</p>
              </div>
            )}
            {protocol.potential_benefits && (
              <div>
                <p className="text-sm text-muted-foreground mb-1">Potential Benefits</p>
                <p>{protocol.potential_benefits}</p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Procedures */}
      {(protocol.experimental_design || protocol.euthanasia_method) && (
        <Card>
          <CardHeader>
            <CardTitle>Procedures</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {protocol.experimental_design && (
              <div>
                <p className="text-sm text-muted-foreground mb-1">Experimental Design</p>
                <p>{protocol.experimental_design}</p>
              </div>
            )}
            {protocol.statistical_methods && (
              <div>
                <p className="text-sm text-muted-foreground mb-1">Statistical Methods</p>
                <p>{protocol.statistical_methods}</p>
              </div>
            )}
            {protocol.euthanasia_method && (
              <div>
                <p className="text-sm text-muted-foreground mb-1">Euthanasia Method</p>
                <p>{protocol.euthanasia_method}</p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Animal Welfare (3Rs) */}
      {(protocol.replacement_statement || protocol.reduction_statement || protocol.refinement_statement) && (
        <Card>
          <CardHeader>
            <CardTitle>Animal Welfare (3Rs)</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {protocol.replacement_statement && (
              <div>
                <p className="text-sm text-muted-foreground mb-1">Replacement</p>
                <p>{protocol.replacement_statement}</p>
              </div>
            )}
            {protocol.reduction_statement && (
              <div>
                <p className="text-sm text-muted-foreground mb-1">Reduction</p>
                <p>{protocol.reduction_statement}</p>
              </div>
            )}
            {protocol.refinement_statement && (
              <div>
                <p className="text-sm text-muted-foreground mb-1">Refinement</p>
                <p>{protocol.refinement_statement}</p>
              </div>
            )}
            {protocol.humane_endpoints && (
              <div>
                <p className="text-sm text-muted-foreground mb-1">Humane Endpoints</p>
                {typeof protocol.humane_endpoints === "string" ? (
                  <p>{protocol.humane_endpoints}</p>
                ) : Array.isArray(protocol.humane_endpoints) ? (
                  <div className="space-y-2 mt-2">
                    {protocol.humane_endpoints.map((endpoint, index) => (
                      <div key={index} className="p-3 bg-muted rounded-md text-sm">
                        <p><span className="font-medium">Criterion:</span> {endpoint.criterion}</p>
                        <p><span className="font-medium">Measurement:</span> {endpoint.measurement}</p>
                        <p><span className="font-medium">Threshold:</span> {endpoint.threshold}</p>
                        <p><span className="font-medium">Action:</span> {endpoint.action}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-muted-foreground">No endpoints defined</p>
                )}
              </div>
            )}
            {protocol.monitoring_schedule && (
              <div>
                <p className="text-sm text-muted-foreground mb-1">Monitoring Schedule</p>
                <p>{protocol.monitoring_schedule}</p>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Metadata */}
      <Card>
        <CardHeader>
          <CardTitle>Protocol Metadata</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid md:grid-cols-2 gap-4 text-sm">
            <div>
              <p className="text-muted-foreground">Created</p>
              <p>{new Date(protocol.created_at).toLocaleString()}</p>
            </div>
            <div>
              <p className="text-muted-foreground">Status</p>
              <p className="capitalize">{protocol.status.replace("_", " ")}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
