"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface ProtocolSummary {
  id: string;
  protocol_number: string | null;
  title: string;
  status: string;
  pi_name: string;
  species: string[];
  total_animals: number;
  usda_category: string;
  completeness: number;
  created_at: string;
  updated_at: string;
}

export default function ProtocolsPage() {
  const [protocols, setProtocols] = useState<ProtocolSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchProtocols() {
      try {
        const response = await fetch("http://localhost:8000/api/v1/protocols");
        if (!response.ok) throw new Error("Failed to fetch protocols");
        const data = await response.json();
        setProtocols(data.protocols);
      } catch (err) {
        setError("Unable to load protocols. Make sure the backend is running.");
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    fetchProtocols();
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case "draft": return "secondary";
      case "submitted": return "default";
      case "under_review": return "default";
      case "approved": return "default";
      case "rejected": return "destructive";
      default: return "secondary";
    }
  };

  const getCategoryColor = (category: string) => {
    switch (category) {
      case "B": return "bg-green-100 text-green-800";
      case "C": return "bg-yellow-100 text-yellow-800";
      case "D": return "bg-orange-100 text-orange-800";
      case "E": return "bg-red-100 text-red-800";
      default: return "bg-gray-100 text-gray-800";
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Protocols</h1>
          <p className="text-muted-foreground">Manage your IACUC protocols</p>
        </div>
        <Button asChild>
          <Link href="/protocols/new">New Protocol</Link>
        </Button>
      </div>

      {loading && (
        <div className="text-center py-12">
          <p className="text-muted-foreground">Loading protocols...</p>
        </div>
      )}

      {error && (
        <Card className="border-destructive">
          <CardContent className="pt-6">
            <p className="text-destructive">{error}</p>
          </CardContent>
        </Card>
      )}

      {!loading && !error && protocols.length === 0 && (
        <Card>
          <CardContent className="pt-6 text-center">
            <p className="text-muted-foreground mb-4">No protocols found</p>
            <Button asChild>
              <Link href="/protocols/new">Create Your First Protocol</Link>
            </Button>
          </CardContent>
        </Card>
      )}

      {!loading && !error && protocols.length > 0 && (
        <div className="grid gap-4">
          {protocols.map((protocol) => (
            <Card key={protocol.id} className="hover:shadow-md transition-shadow">
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="text-lg">{protocol.title}</CardTitle>
                    <CardDescription>
                      {protocol.protocol_number || "No protocol number"} &bull; PI: {protocol.pi_name}
                    </CardDescription>
                  </div>
                  <div className="flex gap-2">
                    <Badge variant={getStatusColor(protocol.status)}>
                      {protocol.status}
                    </Badge>
                    <Badge className={getCategoryColor(protocol.usda_category)}>
                      Category {protocol.usda_category}
                    </Badge>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex justify-between items-center">
                  <div className="flex gap-4 text-sm text-muted-foreground">
                    <span>Species: {protocol.species.join(", ") || "TBD"}</span>
                    <span>Animals: {protocol.total_animals}</span>
                    <span>Completeness: {Math.round(protocol.completeness * 100)}%</span>
                  </div>
                  <Button variant="outline" size="sm" asChild>
                    <Link href={`/protocols/${protocol.id}`}>View Details</Link>
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
