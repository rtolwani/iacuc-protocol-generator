"use client";

import { Progress } from "@/components/ui/progress";

interface WizardStep {
  id: string;
  title: string;
  description: string;
}

interface WizardStepsProps {
  steps: WizardStep[];
  currentStep: number;
}

export function WizardSteps({ steps, currentStep }: WizardStepsProps) {
  const progress = ((currentStep + 1) / steps.length) * 100;

  return (
    <div className="space-y-4">
      <div className="flex justify-between text-sm">
        <span>
          Step {currentStep + 1} of {steps.length}
        </span>
        <span>{Math.round(progress)}% complete</span>
      </div>
      <Progress value={progress} />
      
      <div className="flex justify-between">
        {steps.map((step, index) => (
          <div
            key={step.id}
            className={`flex flex-col items-center ${
              index <= currentStep ? "text-primary" : "text-muted-foreground"
            }`}
          >
            <div
              className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                index < currentStep
                  ? "bg-primary text-primary-foreground"
                  : index === currentStep
                  ? "border-2 border-primary"
                  : "border-2 border-muted"
              }`}
            >
              {index < currentStep ? "✓" : index + 1}
            </div>
            <span className="text-xs mt-1 hidden md:block">{step.title}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export const PROTOCOL_WIZARD_STEPS: WizardStep[] = [
  {
    id: "basic",
    title: "Basic Info",
    description: "Protocol title and PI information",
  },
  {
    id: "animals",
    title: "Animals",
    description: "Species and animal numbers",
  },
  {
    id: "rationale",
    title: "Rationale",
    description: "Scientific justification",
  },
  {
    id: "procedures",
    title: "Procedures",
    description: "Experimental procedures",
  },
  {
    id: "welfare",
    title: "Animal Welfare",
    description: "3Rs and humane endpoints",
  },
  {
    id: "review",
    title: "Review",
    description: "Review and submit",
  },
];
