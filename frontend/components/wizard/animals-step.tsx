"use client";

import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

export interface AnimalData {
  species: string;
  strain: string;
  sex: string;
  total_number: number;
  source: string;
  genetic_modification: string;
}

export interface AnimalsStepData {
  animals: AnimalData[];
  usda_category: string;
  animal_number_justification: string;
}

interface AnimalsStepProps {
  data: AnimalsStepData;
  onChange: (data: Partial<AnimalsStepData>) => void;
}

const COMMON_SPECIES = [
  "Mouse",
  "Rat",
  "Rabbit",
  "Guinea Pig",
  "Hamster",
  "Non-human Primate",
  "Pig",
  "Dog",
  "Cat",
  "Zebrafish",
  "Other",
];

const COMMON_STRAINS: Record<string, string[]> = {
  Mouse: ["C57BL/6J", "BALB/c", "FVB/N", "CD-1", "129S1/SvImJ", "Other"],
  Rat: ["Sprague-Dawley", "Wistar", "Fischer 344", "Long-Evans", "Other"],
};

export function AnimalsStep({ data, onChange }: AnimalsStepProps) {
  const [newAnimal, setNewAnimal] = useState<AnimalData>({
    species: "",
    strain: "",
    sex: "both",
    total_number: 0,
    source: "",
    genetic_modification: "",
  });

  const addAnimal = () => {
    if (newAnimal.species && newAnimal.total_number > 0 && newAnimal.source) {
      onChange({
        animals: [...data.animals, newAnimal],
      });
      setNewAnimal({
        species: "",
        strain: "",
        sex: "both",
        total_number: 0,
        source: "",
        genetic_modification: "",
      });
    }
  };

  const removeAnimal = (index: number) => {
    onChange({
      animals: data.animals.filter((_, i) => i !== index),
    });
  };

  const totalAnimals = data.animals.reduce((sum, a) => sum + a.total_number, 0);

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Animal Information</CardTitle>
          <CardDescription>
            Specify all species and strains used in this study
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {data.animals.length > 0 && (
            <div className="space-y-2">
              <Label>Added Animals</Label>
              <div className="space-y-2">
                {data.animals.map((animal, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-muted rounded-md"
                  >
                    <div>
                      <span className="font-medium">{animal.species}</span>
                      {animal.strain && <span className="text-muted-foreground"> ({animal.strain})</span>}
                      <span className="text-muted-foreground">
                        {" "}- {animal.sex}, n={animal.total_number}
                      </span>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => removeAnimal(index)}
                    >
                      Remove
                    </Button>
                  </div>
                ))}
              </div>
              <p className="text-sm font-medium">
                Total animals: {totalAnimals}
              </p>
            </div>
          )}

          <div className="border-t pt-4">
            <Label className="text-base font-medium">Add Animal Group</Label>
            <div className="grid md:grid-cols-2 gap-4 mt-4">
              <div className="space-y-2">
                <Label htmlFor="species">Species *</Label>
                <Select
                  value={newAnimal.species}
                  onValueChange={(value) => setNewAnimal({ ...newAnimal, species: value, strain: "" })}
                >
                  <SelectTrigger id="species">
                    <SelectValue placeholder="Select species" />
                  </SelectTrigger>
                  <SelectContent>
                    {COMMON_SPECIES.map((s) => (
                      <SelectItem key={s} value={s}>{s}</SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="strain">Strain</Label>
                {COMMON_STRAINS[newAnimal.species] ? (
                  <Select
                    value={newAnimal.strain}
                    onValueChange={(value) => setNewAnimal({ ...newAnimal, strain: value })}
                  >
                    <SelectTrigger id="strain">
                      <SelectValue placeholder="Select strain" />
                    </SelectTrigger>
                    <SelectContent>
                      {COMMON_STRAINS[newAnimal.species].map((s) => (
                        <SelectItem key={s} value={s}>{s}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                ) : (
                  <Input
                    id="strain"
                    placeholder="Enter strain"
                    value={newAnimal.strain}
                    onChange={(e) => setNewAnimal({ ...newAnimal, strain: e.target.value })}
                  />
                )}
              </div>
              <div className="space-y-2">
                <Label htmlFor="sex">Sex *</Label>
                <Select
                  value={newAnimal.sex}
                  onValueChange={(value) => setNewAnimal({ ...newAnimal, sex: value })}
                >
                  <SelectTrigger id="sex">
                    <SelectValue placeholder="Select sex" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="male">Male only</SelectItem>
                    <SelectItem value="female">Female only</SelectItem>
                    <SelectItem value="both">Both sexes</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="total_number">Number of Animals *</Label>
                <Input
                  id="total_number"
                  type="number"
                  min={1}
                  placeholder="40"
                  value={newAnimal.total_number || ""}
                  onChange={(e) => setNewAnimal({ ...newAnimal, total_number: parseInt(e.target.value) || 0 })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="source">Source *</Label>
                <Input
                  id="source"
                  placeholder="Jackson Laboratory, Charles River, etc."
                  value={newAnimal.source}
                  onChange={(e) => setNewAnimal({ ...newAnimal, source: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="genetic_modification">Genetic Modification</Label>
                <Input
                  id="genetic_modification"
                  placeholder="Transgenic, Knockout, etc."
                  value={newAnimal.genetic_modification}
                  onChange={(e) => setNewAnimal({ ...newAnimal, genetic_modification: e.target.value })}
                />
              </div>
            </div>
            <Button
              type="button"
              variant="outline"
              className="mt-4"
              onClick={addAnimal}
              disabled={!newAnimal.species || newAnimal.total_number <= 0 || !newAnimal.source}
            >
              Add Animal Group
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>USDA Pain Category</CardTitle>
          <CardDescription>
            Select the appropriate USDA pain and distress category
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="usda_category">Pain Category *</Label>
            <Select
              value={data.usda_category}
              onValueChange={(value) => onChange({ usda_category: value })}
            >
              <SelectTrigger id="usda_category">
                <SelectValue placeholder="Select USDA category" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="B">Category B - Breeding or holding only</SelectItem>
                <SelectItem value="C">Category C - No pain or distress</SelectItem>
                <SelectItem value="D">Category D - Pain/distress with appropriate relief</SelectItem>
                <SelectItem value="E">Category E - Pain/distress without relief</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <div className="space-y-2">
            <Label htmlFor="animal_number_justification">Animal Number Justification *</Label>
            <Textarea
              id="animal_number_justification"
              placeholder="Provide a detailed justification for the number of animals requested. Include power analysis calculations if applicable."
              value={data.animal_number_justification}
              onChange={(e) => onChange({ animal_number_justification: e.target.value })}
              rows={4}
            />
            <p className="text-xs text-muted-foreground">
              Explain why this number of animals is necessary for statistically valid results.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
