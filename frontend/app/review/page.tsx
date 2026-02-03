"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

interface PendingReview {
  workflow_id: string;
  checkpoint_id: string;
  checkpoint_name: string;
  status: string;
  created_at: string;
  agent_output: unknown;
}

export default function ReviewPage() {
  const [pendingReviews, setPendingReviews] = useState<PendingReview[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchPendingReviews() {
      try {
        const response = await fetch("http://localhost:8000/api/v1/review/pending");
        if (!response.ok) throw new Error("Failed to fetch pending reviews");
        const data = await response.json();
        setPendingReviews(data.pending_reviews || []);
      } catch (err) {
        setError("Unable to load reviews. Make sure the backend is running.");
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    fetchPendingReviews();
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case "pending_review": return "secondary";
      case "approved": return "default";
      case "rejected": return "destructive";
      case "revision_requested": return "default";
      default: return "secondary";
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Review Dashboard</h1>
        <p className="text-muted-foreground">Review and approve protocol submissions</p>
      </div>

      <Tabs defaultValue="pending">
        <TabsList>
          <TabsTrigger value="pending">Pending Reviews</TabsTrigger>
          <TabsTrigger value="completed">Completed</TabsTrigger>
        </TabsList>

        <TabsContent value="pending" className="space-y-4">
          {loading && (
            <div className="text-center py-12">
              <p className="text-muted-foreground">Loading reviews...</p>
            </div>
          )}

          {error && (
            <Card className="border-destructive">
              <CardContent className="pt-6">
                <p className="text-destructive">{error}</p>
              </CardContent>
            </Card>
          )}

          {!loading && !error && pendingReviews.length === 0 && (
            <Card>
              <CardContent className="pt-6 text-center">
                <p className="text-muted-foreground">No pending reviews</p>
              </CardContent>
            </Card>
          )}

          {!loading && !error && pendingReviews.length > 0 && (
            <div className="grid gap-4">
              {pendingReviews.map((review) => (
                <Card key={`${review.workflow_id}-${review.checkpoint_id}`}>
                  <CardHeader>
                    <div className="flex justify-between items-start">
                      <div>
                        <CardTitle>{review.checkpoint_name}</CardTitle>
                        <CardDescription>
                          Workflow: {review.workflow_id.slice(0, 8)}...
                        </CardDescription>
                      </div>
                      <Badge variant={getStatusColor(review.status)}>
                        {review.status.replace("_", " ")}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-muted-foreground">
                        Created: {new Date(review.created_at).toLocaleDateString()}
                      </span>
                      <div className="flex gap-2">
                        <Button variant="outline" size="sm">
                          View Details
                        </Button>
                        <Button size="sm">
                          Start Review
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="completed">
          <Card>
            <CardContent className="pt-6 text-center">
              <p className="text-muted-foreground">No completed reviews to display</p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
