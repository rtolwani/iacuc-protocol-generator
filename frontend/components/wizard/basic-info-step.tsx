"use client";

import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export interface BasicInfoData {
  title: string;
  pi_name: string;
  pi_email: string;
  department: string;
  funding_sources: string;
  study_duration: string;
  lay_summary: string;
}

interface BasicInfoStepProps {
  data: BasicInfoData;
  onChange: (data: Partial<BasicInfoData>) => void;
}

export function BasicInfoStep({ data, onChange }: BasicInfoStepProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Basic Information</CardTitle>
        <CardDescription>
          Enter the fundamental details about your research protocol
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="title">Protocol Title *</Label>
          <Input
            id="title"
            placeholder="Effects of Novel Treatment on Disease Model"
            value={data.title}
            onChange={(e) => onChange({ title: e.target.value })}
          />
          <p className="text-xs text-muted-foreground">
            Be specific and descriptive. Minimum 10 characters.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="pi_name">Principal Investigator *</Label>
            <Input
              id="pi_name"
              placeholder="Dr. Jane Smith"
              value={data.pi_name}
              onChange={(e) => onChange({ pi_name: e.target.value })}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="pi_email">PI Email *</Label>
            <Input
              id="pi_email"
              type="email"
              placeholder="jsmith@university.edu"
              value={data.pi_email}
              onChange={(e) => onChange({ pi_email: e.target.value })}
            />
          </div>
        </div>

        <div className="grid md:grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="department">Department *</Label>
            <Input
              id="department"
              placeholder="Department of Neuroscience"
              value={data.department}
              onChange={(e) => onChange({ department: e.target.value })}
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="study_duration">Study Duration</Label>
            <Input
              id="study_duration"
              placeholder="12 months"
              value={data.study_duration}
              onChange={(e) => onChange({ study_duration: e.target.value })}
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="funding_sources">Funding Sources</Label>
          <Input
            id="funding_sources"
            placeholder="NIH R01, Internal Grant"
            value={data.funding_sources}
            onChange={(e) => onChange({ funding_sources: e.target.value })}
          />
        </div>

        <div className="space-y-2">
          <Label htmlFor="lay_summary">Lay Summary *</Label>
          <Textarea
            id="lay_summary"
            placeholder="Describe your research in plain language that can be understood by non-scientists. This summary should explain the purpose, methods, and potential benefits of the research."
            value={data.lay_summary}
            onChange={(e) => onChange({ lay_summary: e.target.value })}
            rows={5}
          />
          <p className="text-xs text-muted-foreground">
            Minimum 100 characters. Write at a level understandable by the general public.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
