"use client";

import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export interface WelfareStepData {
  replacement_statement: string;
  reduction_statement: string;
  refinement_statement: string;
  humane_endpoints: string;
  monitoring_schedule: string;
}

interface WelfareStepProps {
  data: WelfareStepData;
  onChange: (data: Partial<WelfareStepData>) => void;
}

export function WelfareStep({ data, onChange }: WelfareStepProps) {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>3Rs - Replacement</CardTitle>
          <CardDescription>
            Explain why alternatives to animal use cannot achieve your research objectives
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="replacement_statement">Replacement Statement *</Label>
            <Textarea
              id="replacement_statement"
              placeholder="Describe the alternatives considered and why they cannot replace animal use:
- In vitro methods (cell culture, organoids)
- Computational models
- Human studies
- Lower organisms
Explain what literature searches were conducted to identify alternatives."
              value={data.replacement_statement}
              onChange={(e) => onChange({ replacement_statement: e.target.value })}
              rows={5}
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>3Rs - Reduction</CardTitle>
          <CardDescription>
            Describe how you minimized the number of animals used
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="reduction_statement">Reduction Statement *</Label>
            <Textarea
              id="reduction_statement"
              placeholder="Explain how the number of animals has been minimized:
- Power analysis to determine minimum sample size
- Use of pilot studies
- Sharing of animals between studies
- Statistical methods to maximize data extraction"
              value={data.reduction_statement}
              onChange={(e) => onChange({ reduction_statement: e.target.value })}
              rows={5}
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>3Rs - Refinement</CardTitle>
          <CardDescription>
            Describe how you minimize pain, suffering, and distress
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="refinement_statement">Refinement Statement *</Label>
            <Textarea
              id="refinement_statement"
              placeholder="Describe refinements to minimize pain and distress:
- Anesthesia and analgesia protocols
- Environmental enrichment
- Low-stress handling techniques
- Humane endpoints"
              value={data.refinement_statement}
              onChange={(e) => onChange({ refinement_statement: e.target.value })}
              rows={5}
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Humane Endpoints</CardTitle>
          <CardDescription>
            Define criteria for early endpoint determination
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="humane_endpoints">Humane Endpoint Criteria *</Label>
            <Textarea
              id="humane_endpoints"
              placeholder="Define specific, measurable criteria for humane endpoints:
- Weight loss threshold (e.g., >20% body weight)
- Clinical signs requiring intervention
- Behavioral indicators
- Tumor size limits (if applicable)
- Actions to be taken when endpoints are reached"
              value={data.humane_endpoints}
              onChange={(e) => onChange({ humane_endpoints: e.target.value })}
              rows={6}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="monitoring_schedule">Monitoring Schedule *</Label>
            <Input
              id="monitoring_schedule"
              placeholder="e.g., Daily observation, weekly weighing, detailed health assessment every 48 hours post-procedure"
              value={data.monitoring_schedule}
              onChange={(e) => onChange({ monitoring_schedule: e.target.value })}
            />
            <p className="text-xs text-muted-foreground">
              Describe how often animals will be monitored and what will be assessed.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
