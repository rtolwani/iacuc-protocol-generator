"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import type { BasicInfoData } from "./basic-info-step";
import type { AnimalsStepData } from "./animals-step";
import type { RationaleStepData } from "./rationale-step";
import type { ProceduresStepData } from "./procedures-step";
import type { WelfareStepData } from "./welfare-step";

interface ReviewStepProps {
  basicInfo: BasicInfoData;
  animals: AnimalsStepData;
  rationale: RationaleStepData;
  procedures: ProceduresStepData;
  welfare: WelfareStepData;
}

export function ReviewStep({
  basicInfo,
  animals,
  rationale,
  procedures,
  welfare,
}: ReviewStepProps) {
  const missingFields: string[] = [];

  // Check required fields
  if (!basicInfo.title || basicInfo.title.length < 10) missingFields.push("Protocol title (min 10 characters)");
  if (!basicInfo.pi_name) missingFields.push("Principal investigator");
  if (!basicInfo.pi_email) missingFields.push("PI email");
  if (!basicInfo.department) missingFields.push("Department");
  if (!basicInfo.lay_summary || basicInfo.lay_summary.length < 100) missingFields.push("Lay summary (min 100 characters)");
  if (animals.animals.length === 0) missingFields.push("Animal information");
  if (!animals.usda_category) missingFields.push("USDA pain category");
  if (!animals.animal_number_justification) missingFields.push("Animal number justification");
  if (!rationale.scientific_objectives) missingFields.push("Scientific objectives");
  if (!rationale.scientific_rationale) missingFields.push("Scientific rationale");
  if (!procedures.experimental_design) missingFields.push("Experimental design");
  if (!procedures.euthanasia_method) missingFields.push("Euthanasia method");
  if (!welfare.replacement_statement) missingFields.push("Replacement statement");
  if (!welfare.reduction_statement) missingFields.push("Reduction statement");
  if (!welfare.refinement_statement) missingFields.push("Refinement statement");
  if (!welfare.humane_endpoints) missingFields.push("Humane endpoints");
  if (!welfare.monitoring_schedule) missingFields.push("Monitoring schedule");

  const totalAnimals = animals.animals.reduce((sum, a) => sum + a.total_number, 0);

  return (
    <div className="space-y-6">
      {missingFields.length > 0 && (
        <Alert variant="destructive">
          <AlertTitle>Missing Required Information</AlertTitle>
          <AlertDescription>
            <ul className="list-disc list-inside mt-2">
              {missingFields.map((field, i) => (
                <li key={i}>{field}</li>
              ))}
            </ul>
          </AlertDescription>
        </Alert>
      )}

      {missingFields.length === 0 && (
        <Alert>
          <AlertTitle>Ready for Submission</AlertTitle>
          <AlertDescription>
            All required fields are complete. Review the information below and submit when ready.
          </AlertDescription>
        </Alert>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Basic Information</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          <div>
            <span className="font-medium">Title: </span>
            <span>{basicInfo.title || "Not provided"}</span>
          </div>
          <div>
            <span className="font-medium">Principal Investigator: </span>
            <span>{basicInfo.pi_name || "Not provided"}</span>
          </div>
          <div>
            <span className="font-medium">Email: </span>
            <span>{basicInfo.pi_email || "Not provided"}</span>
          </div>
          <div>
            <span className="font-medium">Department: </span>
            <span>{basicInfo.department || "Not provided"}</span>
          </div>
          <div>
            <span className="font-medium">Funding: </span>
            <span>{basicInfo.funding_sources || "Not specified"}</span>
          </div>
          <div>
            <span className="font-medium">Duration: </span>
            <span>{basicInfo.study_duration || "Not specified"}</span>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            Animals
            {animals.usda_category && (
              <Badge variant="outline">Category {animals.usda_category}</Badge>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {animals.animals.length > 0 ? (
            <>
              <div className="space-y-1">
                {animals.animals.map((animal, i) => (
                  <div key={i}>
                    <span className="font-medium">{animal.species}</span>
                    {animal.strain && <span> ({animal.strain})</span>}
                    <span className="text-muted-foreground">
                      {" "}- {animal.sex}, n={animal.total_number}, source: {animal.source}
                    </span>
                  </div>
                ))}
              </div>
              <div className="font-medium pt-2">Total animals: {totalAnimals}</div>
            </>
          ) : (
            <span className="text-muted-foreground">No animals specified</span>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Scientific Rationale</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <span className="font-medium">Objectives:</span>
            <p className="text-sm mt-1 whitespace-pre-wrap">
              {rationale.scientific_objectives || "Not provided"}
            </p>
          </div>
          <div>
            <span className="font-medium">Rationale:</span>
            <p className="text-sm mt-1 whitespace-pre-wrap">
              {rationale.scientific_rationale || "Not provided"}
            </p>
          </div>
          <div>
            <span className="font-medium">Potential Benefits:</span>
            <p className="text-sm mt-1 whitespace-pre-wrap">
              {rationale.potential_benefits || "Not provided"}
            </p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Procedures</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <span className="font-medium">Experimental Design:</span>
            <p className="text-sm mt-1 whitespace-pre-wrap">
              {procedures.experimental_design || "Not provided"}
            </p>
          </div>
          <div>
            <span className="font-medium">Euthanasia Method:</span>
            <p className="text-sm mt-1">
              {procedures.euthanasia_method || "Not provided"}
            </p>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Animal Welfare (3Rs)</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <span className="font-medium">Replacement:</span>
            <p className="text-sm mt-1 whitespace-pre-wrap">
              {welfare.replacement_statement || "Not provided"}
            </p>
          </div>
          <div>
            <span className="font-medium">Reduction:</span>
            <p className="text-sm mt-1 whitespace-pre-wrap">
              {welfare.reduction_statement || "Not provided"}
            </p>
          </div>
          <div>
            <span className="font-medium">Refinement:</span>
            <p className="text-sm mt-1 whitespace-pre-wrap">
              {welfare.refinement_statement || "Not provided"}
            </p>
          </div>
          <div>
            <span className="font-medium">Humane Endpoints:</span>
            <p className="text-sm mt-1 whitespace-pre-wrap">
              {welfare.humane_endpoints || "Not provided"}
            </p>
          </div>
          <div>
            <span className="font-medium">Monitoring Schedule:</span>
            <p className="text-sm mt-1">
              {welfare.monitoring_schedule || "Not provided"}
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
