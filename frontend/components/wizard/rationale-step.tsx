"use client";

import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export interface RationaleStepData {
  scientific_objectives: string;
  scientific_rationale: string;
  potential_benefits: string;
}

interface RationaleStepProps {
  data: RationaleStepData;
  onChange: (data: Partial<RationaleStepData>) => void;
}

export function RationaleStep({ data, onChange }: RationaleStepProps) {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Scientific Objectives</CardTitle>
          <CardDescription>
            Clearly state the goals and hypotheses of your research
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="scientific_objectives">Research Objectives *</Label>
            <Textarea
              id="scientific_objectives"
              placeholder="List the specific aims and hypotheses of your research. For example:
1. Determine the effect of compound X on tumor growth
2. Evaluate the mechanism of action through biomarker analysis
3. Assess safety and tolerability in the animal model"
              value={data.scientific_objectives}
              onChange={(e) => onChange({ scientific_objectives: e.target.value })}
              rows={6}
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Scientific Rationale</CardTitle>
          <CardDescription>
            Justify why animals are necessary for this research
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="scientific_rationale">Rationale for Animal Use *</Label>
            <Textarea
              id="scientific_rationale"
              placeholder="Explain why animals are necessary for this research. Address:
- Why alternative methods (cell culture, computer models) cannot achieve the research objectives
- Why this particular species is appropriate
- The relevance of this animal model to human disease or condition being studied"
              value={data.scientific_rationale}
              onChange={(e) => onChange({ scientific_rationale: e.target.value })}
              rows={6}
            />
            <p className="text-xs text-muted-foreground">
              Provide a strong scientific justification for the use of animals in this research.
            </p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Potential Benefits</CardTitle>
          <CardDescription>
            Describe the expected outcomes and significance of the research
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="potential_benefits">Expected Benefits *</Label>
            <Textarea
              id="potential_benefits"
              placeholder="Describe the potential benefits of this research:
- Scientific knowledge that will be gained
- Potential medical or therapeutic applications
- Impact on human or animal health
- Contribution to the field"
              value={data.potential_benefits}
              onChange={(e) => onChange({ potential_benefits: e.target.value })}
              rows={6}
            />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
