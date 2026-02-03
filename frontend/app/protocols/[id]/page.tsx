"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Separator } from "@/components/ui/separator";
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

export default function ProtocolDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [protocol, setProtocol] = useState<Protocol | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchProtocol = async () => {
      try {
        const data = await api.getProtocol(params.id as string);
        setProtocol(data);
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
                setLoading(true);
                setError(null);
                const result = await api.runAICrew(protocol.id, false);
                if (result.success) {
                  setProtocol({ ...protocol, status: "under_review" });
                  alert("AI Review completed! Check the Review page for results.");
                } else {
                  setError(result.message || "AI review failed");
                }
              } catch (err) {
                setError(err instanceof Error ? err.message : "Failed to run AI review");
              } finally {
                setLoading(false);
              }
            }}
            disabled={loading}
          >
            {loading ? "Running AI Review..." : "Run AI Review"}
          </Button>
        )}
      </div>

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
