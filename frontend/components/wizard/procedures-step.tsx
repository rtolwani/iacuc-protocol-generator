"use client";

import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export interface ProceduresStepData {
  experimental_design: string;
  statistical_methods: string;
  procedures_description: string;
  anesthesia_protocol: string;
  analgesia_protocol: string;
  euthanasia_method: string;
}

interface ProceduresStepProps {
  data: ProceduresStepData;
  onChange: (data: Partial<ProceduresStepData>) => void;
}

export function ProceduresStep({ data, onChange }: ProceduresStepProps) {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Experimental Design</CardTitle>
          <CardDescription>
            Describe your experimental groups and study design
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="experimental_design">Study Design *</Label>
            <Textarea
              id="experimental_design"
              placeholder="Describe your experimental design including:
- Treatment groups and controls
- Number of animals per group
- Study timeline
- Endpoints measured"
              value={data.experimental_design}
              onChange={(e) => onChange({ experimental_design: e.target.value })}
              rows={6}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="statistical_methods">Statistical Methods *</Label>
            <Textarea
              id="statistical_methods"
              placeholder="Describe the statistical methods:
- Analysis methods (ANOVA, t-test, etc.)
- Power analysis if performed
- Significance level"
              value={data.statistical_methods}
              onChange={(e) => onChange({ statistical_methods: e.target.value })}
              rows={4}
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Procedures</CardTitle>
          <CardDescription>
            Describe all procedures performed on animals
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="procedures_description">Procedure Description *</Label>
            <Textarea
              id="procedures_description"
              placeholder="Describe each procedure in detail:
- What is done to the animals
- Frequency and duration
- Personnel performing procedures
- Any special techniques or equipment"
              value={data.procedures_description}
              onChange={(e) => onChange({ procedures_description: e.target.value })}
              rows={6}
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Anesthesia and Analgesia</CardTitle>
          <CardDescription>
            Specify pain management protocols
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="anesthesia_protocol">Anesthesia Protocol</Label>
            <Textarea
              id="anesthesia_protocol"
              placeholder="Describe anesthesia agents, doses, and routes:
- Drug name, dose, route of administration
- Monitoring during anesthesia
- Depth of anesthesia assessment"
              value={data.anesthesia_protocol}
              onChange={(e) => onChange({ anesthesia_protocol: e.target.value })}
              rows={4}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="analgesia_protocol">Analgesia Protocol</Label>
            <Textarea
              id="analgesia_protocol"
              placeholder="Describe pain management:
- Pre-emptive analgesia
- Post-operative pain management
- Duration of treatment"
              value={data.analgesia_protocol}
              onChange={(e) => onChange({ analgesia_protocol: e.target.value })}
              rows={4}
            />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Euthanasia</CardTitle>
          <CardDescription>
            Specify the method of euthanasia
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="euthanasia_method">Euthanasia Method *</Label>
            <Input
              id="euthanasia_method"
              placeholder="e.g., CO2 asphyxiation followed by cervical dislocation"
              value={data.euthanasia_method}
              onChange={(e) => onChange({ euthanasia_method: e.target.value })}
            />
            <p className="text-xs text-muted-foreground">
              Must be consistent with AVMA Guidelines on Euthanasia
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
