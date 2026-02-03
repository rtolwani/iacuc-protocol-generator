"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";
import { Alert, AlertDescription } from "@/components/ui/alert";

export default function NewProtocolPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const [formData, setFormData] = useState({
    title: "",
    pi_name: "",
    pi_email: "",
    department: "",
  });

  const totalSteps = 1; // For now, just the basic info step
  const progress = (step / totalSteps) * 100;

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await fetch("http://localhost:8000/api/v1/protocols", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "Failed to create protocol");
      }

      const data = await response.json();
      router.push(`/protocols/${data.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  const isValid = 
    formData.title.length >= 10 &&
    formData.pi_name.length > 0 &&
    formData.pi_email.length > 0 &&
    formData.department.length > 0;

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Create New Protocol</h1>
        <p className="text-muted-foreground">Start a new IACUC protocol application</p>
      </div>

      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span>Step {step} of {totalSteps}</span>
          <span>{Math.round(progress)}% complete</span>
        </div>
        <Progress value={progress} />
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Basic Information</CardTitle>
          <CardDescription>
            Enter the basic details for your protocol
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="title">Protocol Title *</Label>
              <Input
                id="title"
                name="title"
                placeholder="Enter a descriptive title for your research"
                value={formData.title}
                onChange={handleInputChange}
                minLength={10}
                maxLength={300}
                required
              />
              <p className="text-xs text-muted-foreground">
                Minimum 10 characters. Be specific and descriptive.
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="pi_name">Principal Investigator Name *</Label>
              <Input
                id="pi_name"
                name="pi_name"
                placeholder="Dr. Jane Smith"
                value={formData.pi_name}
                onChange={handleInputChange}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="pi_email">PI Email *</Label>
              <Input
                id="pi_email"
                name="pi_email"
                type="email"
                placeholder="jsmith@university.edu"
                value={formData.pi_email}
                onChange={handleInputChange}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="department">Department *</Label>
              <Input
                id="department"
                name="department"
                placeholder="Department of Neuroscience"
                value={formData.department}
                onChange={handleInputChange}
                required
              />
            </div>

            <div className="flex gap-4 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => router.back()}
              >
                Cancel
              </Button>
              <Button
                type="submit"
                disabled={!isValid || loading}
              >
                {loading ? "Creating..." : "Create Protocol"}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
