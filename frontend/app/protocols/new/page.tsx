"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { WizardSteps, PROTOCOL_WIZARD_STEPS } from "@/components/wizard/wizard-steps";
import { BasicInfoStep, type BasicInfoData } from "@/components/wizard/basic-info-step";
import { AnimalsStep, type AnimalsStepData, type AnimalData } from "@/components/wizard/animals-step";
import { RationaleStep, type RationaleStepData } from "@/components/wizard/rationale-step";
import { ProceduresStep, type ProceduresStepData } from "@/components/wizard/procedures-step";
import { WelfareStep, type WelfareStepData } from "@/components/wizard/welfare-step";
import { ReviewStep } from "@/components/wizard/review-step";
import api from "@/lib/api";

interface WizardData {
  basicInfo: BasicInfoData;
  animals: AnimalsStepData;
  rationale: RationaleStepData;
  procedures: ProceduresStepData;
  welfare: WelfareStepData;
}

const initialData: WizardData = {
  basicInfo: {
    title: "",
    pi_name: "",
    pi_email: "",
    department: "",
    funding_sources: "",
    study_duration: "",
    lay_summary: "",
  },
  animals: {
    animals: [],
    usda_category: "",
    animal_number_justification: "",
  },
  rationale: {
    scientific_objectives: "",
    scientific_rationale: "",
    potential_benefits: "",
  },
  procedures: {
    experimental_design: "",
    statistical_methods: "",
    procedures_description: "",
    anesthesia_protocol: "",
    analgesia_protocol: "",
    euthanasia_method: "",
  },
  welfare: {
    replacement_statement: "",
    reduction_statement: "",
    refinement_statement: "",
    humane_endpoints: "",
    monitoring_schedule: "",
  },
};

export default function NewProtocolPage() {
  const router = useRouter();
  const [currentStep, setCurrentStep] = useState(0);
  const [data, setData] = useState<WizardData>(initialData);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const updateBasicInfo = (updates: Partial<BasicInfoData>) => {
    setData(prev => ({
      ...prev,
      basicInfo: { ...prev.basicInfo, ...updates },
    }));
  };

  const updateAnimals = (updates: Partial<AnimalsStepData>) => {
    setData(prev => ({
      ...prev,
      animals: { ...prev.animals, ...updates },
    }));
  };

  const updateRationale = (updates: Partial<RationaleStepData>) => {
    setData(prev => ({
      ...prev,
      rationale: { ...prev.rationale, ...updates },
    }));
  };

  const updateProcedures = (updates: Partial<ProceduresStepData>) => {
    setData(prev => ({
      ...prev,
      procedures: { ...prev.procedures, ...updates },
    }));
  };

  const updateWelfare = (updates: Partial<WelfareStepData>) => {
    setData(prev => ({
      ...prev,
      welfare: { ...prev.welfare, ...updates },
    }));
  };

  const canProceed = (): boolean => {
    switch (currentStep) {
      case 0: // Basic Info
        return (
          data.basicInfo.title.length >= 10 &&
          data.basicInfo.pi_name.length > 0 &&
          data.basicInfo.pi_email.length > 0 &&
          data.basicInfo.department.length > 0
        );
      case 1: // Animals
        return data.animals.animals.length > 0;
      case 2: // Rationale
        return (
          data.rationale.scientific_objectives.length > 0 &&
          data.rationale.scientific_rationale.length > 0
        );
      case 3: // Procedures
        return (
          data.procedures.experimental_design.length > 0 &&
          data.procedures.euthanasia_method.length > 0
        );
      case 4: // Welfare
        return (
          data.welfare.replacement_statement.length > 0 &&
          data.welfare.reduction_statement.length > 0 &&
          data.welfare.refinement_statement.length > 0 &&
          data.welfare.humane_endpoints.length > 0
        );
      default:
        return true;
    }
  };

  const handleNext = () => {
    if (currentStep < PROTOCOL_WIZARD_STEPS.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError(null);

    try {
      // First create the protocol with basic info
      const createResult = await api.createProtocol({
        title: data.basicInfo.title,
        pi_name: data.basicInfo.pi_name,
        pi_email: data.basicInfo.pi_email,
        department: data.basicInfo.department,
      });

      const protocolId = createResult.id;

      // Update with additional data
      await api.updateProtocol(protocolId, {
        lay_summary: data.basicInfo.lay_summary || "This section will describe the research project in plain language that can be understood by non-scientists. To be completed with project-specific details.",
        scientific_objectives: data.rationale.scientific_objectives,
        scientific_rationale: data.rationale.scientific_rationale,
        replacement_statement: data.welfare.replacement_statement,
        reduction_statement: data.welfare.reduction_statement,
        refinement_statement: data.welfare.refinement_statement,
        experimental_design: data.procedures.experimental_design,
        statistical_methods: data.procedures.statistical_methods,
        monitoring_schedule: data.welfare.monitoring_schedule,
        euthanasia_method: data.procedures.euthanasia_method,
      });

      // Add animals
      for (const animal of data.animals.animals) {
        await api.addAnimal(protocolId, animal);
      }

      router.push(`/protocols/${protocolId}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create protocol");
    } finally {
      setLoading(false);
    }
  };

  const renderStep = () => {
    switch (currentStep) {
      case 0:
        return <BasicInfoStep data={data.basicInfo} onChange={updateBasicInfo} />;
      case 1:
        return <AnimalsStep data={data.animals} onChange={updateAnimals} />;
      case 2:
        return <RationaleStep data={data.rationale} onChange={updateRationale} />;
      case 3:
        return <ProceduresStep data={data.procedures} onChange={updateProcedures} />;
      case 4:
        return <WelfareStep data={data.welfare} onChange={updateWelfare} />;
      case 5:
        return (
          <ReviewStep
            basicInfo={data.basicInfo}
            animals={data.animals}
            rationale={data.rationale}
            procedures={data.procedures}
            welfare={data.welfare}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Create New Protocol</h1>
        <p className="text-muted-foreground">
          Complete the following steps to create your IACUC protocol
        </p>
      </div>

      <WizardSteps steps={PROTOCOL_WIZARD_STEPS} currentStep={currentStep} />

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="min-h-[400px]">{renderStep()}</div>

      <div className="flex justify-between pt-4 border-t">
        <Button
          variant="outline"
          onClick={currentStep === 0 ? () => router.back() : handleBack}
        >
          {currentStep === 0 ? "Cancel" : "Back"}
        </Button>

        {currentStep < PROTOCOL_WIZARD_STEPS.length - 1 ? (
          <Button onClick={handleNext} disabled={!canProceed()}>
            Continue
          </Button>
        ) : (
          <Button onClick={handleSubmit} disabled={loading}>
            {loading ? "Submitting..." : "Submit Protocol"}
          </Button>
        )}
      </div>
    </div>
  );
}
