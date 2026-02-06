"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";

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
        const data = await api.listProtocols();
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
      case "draft": return "bg-slate-100 text-slate-700";
      case "submitted": return "bg-blue-100 text-blue-700";
      case "under_review": return "bg-amber-100 text-amber-700";
      case "approved": return "bg-green-100 text-green-700";
      case "rejected": return "bg-red-100 text-red-700";
      default: return "bg-gray-100 text-gray-700";
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
      <div className="flex justify-between items-center p-6 rounded-xl bg-gradient-to-r from-indigo-500 to-purple-600 text-white shadow-lg">
        <div>
          <h1 className="text-3xl font-bold">📋 Protocols</h1>
          <p className="text-indigo-100">Manage your IACUC protocols</p>
        </div>
        <Button asChild className="bg-white text-purple-700 hover:bg-indigo-50 font-semibold">
          <Link href="/protocols/new">+ New Protocol</Link>
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
        <Card className="border-2 border-dashed border-purple-200 bg-purple-50/50">
          <CardContent className="pt-12 pb-12 text-center">
            <div className="w-16 h-16 rounded-full bg-purple-100 flex items-center justify-center mx-auto mb-4">
              <span className="text-3xl">📝</span>
            </div>
            <h3 className="text-lg font-semibold text-gray-800 mb-2">No protocols yet</h3>
            <p className="text-muted-foreground mb-6">Get started by creating your first IACUC protocol</p>
            <Button asChild className="bg-purple-600 hover:bg-purple-700">
              <Link href="/protocols/new">🚀 Create Your First Protocol</Link>
            </Button>
          </CardContent>
        </Card>
      )}

      {!loading && !error && protocols.length > 0 && (
        <div className="grid gap-4">
          {protocols.map((protocol) => (
            <Card key={protocol.id} className="hover:shadow-lg transition-all hover:border-purple-200 border-l-4 border-l-purple-500">
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="text-lg text-gray-800">{protocol.title}</CardTitle>
                    <CardDescription className="flex items-center gap-2">
                      <span className="font-mono text-xs bg-gray-100 px-2 py-0.5 rounded">{protocol.protocol_number || "No ID"}</span>
                      <span>&bull;</span>
                      <span>PI: {protocol.pi_name}</span>
                    </CardDescription>
                  </div>
                  <div className="flex gap-2">
                    <Badge className={getStatusColor(protocol.status)}>
                      {protocol.status.replace('_', ' ')}
                    </Badge>
                    <Badge className={getCategoryColor(protocol.usda_category)}>
                      Category {protocol.usda_category}
                    </Badge>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="flex justify-between items-center">
                  <div className="flex gap-6 text-sm">
                    <span className="flex items-center gap-1">
                      <span className="text-purple-500">🐁</span> {protocol.species.join(", ") || "TBD"}
                    </span>
                    <span className="flex items-center gap-1">
                      <span className="text-blue-500">📊</span> {protocol.total_animals} animals
                    </span>
                    <span className="flex items-center gap-1">
                      <span className="text-green-500">✓</span> {Math.round(protocol.completeness * 100)}% complete
                    </span>
                  </div>
                  <Button variant="default" size="sm" asChild className="bg-purple-600 hover:bg-purple-700">
                    <Link href={`/protocols/${protocol.id}`}>View Details →</Link>
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
