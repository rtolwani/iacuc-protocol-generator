"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Alert, AlertDescription } from "@/components/ui/alert";

interface PendingReview {
  workflow_id: string;
  checkpoint_id: string;
  checkpoint_name: string;
  status: string;
  created_at: string;
  agent_output: Record<string, unknown>;
}

interface ReviewAction {
  type: "approve" | "reject" | "revision";
  workflowId: string;
  checkpointType: string;
  checkpointName: string;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export default function ReviewPage() {
  const [pendingReviews, setPendingReviews] = useState<PendingReview[]>([]);
  const [completedReviews, setCompletedReviews] = useState<PendingReview[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionLoading, setActionLoading] = useState(false);
  
  // Dialog state
  const [reviewAction, setReviewAction] = useState<ReviewAction | null>(null);
  const [comments, setComments] = useState("");
  const [specificIssues, setSpecificIssues] = useState("");
  
  // Details dialog
  const [selectedReview, setSelectedReview] = useState<PendingReview | null>(null);

  useEffect(() => {
    fetchReviews();
  }, []);

  async function fetchReviews() {
    try {
      const response = await fetch(`${API_URL}/review/pending`);
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

  const openActionDialog = (type: "approve" | "reject" | "revision", review: PendingReview) => {
    setReviewAction({
      type,
      workflowId: review.workflow_id,
      checkpointType: review.checkpoint_id,
      checkpointName: review.checkpoint_name,
    });
    setComments("");
    setSpecificIssues("");
  };

  const closeActionDialog = () => {
    setReviewAction(null);
    setComments("");
    setSpecificIssues("");
  };

  const handleAction = async () => {
    if (!reviewAction) return;
    
    setActionLoading(true);
    try {
      const endpoint = `${API_URL}/review/workflows/${reviewAction.workflowId}/checkpoints/${reviewAction.checkpointType}/${reviewAction.type === "revision" ? "revision" : reviewAction.type}`;
      
      const body: Record<string, unknown> = {
        reviewer_id: "reviewer-1", // In production, this would come from auth
        comments: comments || undefined,
      };
      
      if (reviewAction.type !== "approve" && specificIssues) {
        body.specific_issues = specificIssues.split("\n").filter(Boolean);
      }
      
      const response = await fetch(endpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });
      
      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || "Action failed");
      }
      
      // Refresh reviews
      await fetchReviews();
      closeActionDialog();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Action failed");
    } finally {
      setActionLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "pending_review": return "secondary";
      case "approved": return "default";
      case "rejected": return "destructive";
      case "revision_requested": return "default";
      default: return "secondary";
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold">Review Dashboard</h1>
        <p className="text-muted-foreground">Review and approve protocol submissions</p>
      </div>

      {error && (
        <Alert variant="destructive">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <Tabs defaultValue="pending">
        <TabsList>
          <TabsTrigger value="pending">
            Pending Reviews
            {pendingReviews.length > 0 && (
              <Badge variant="secondary" className="ml-2">
                {pendingReviews.length}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="completed">Completed</TabsTrigger>
        </TabsList>

        <TabsContent value="pending" className="space-y-4 mt-4">
          {loading && (
            <div className="text-center py-12">
              <p className="text-muted-foreground">Loading reviews...</p>
            </div>
          )}

          {!loading && pendingReviews.length === 0 && (
            <Card>
              <CardContent className="pt-6 text-center">
                <div className="space-y-2">
                  <svg
                    className="mx-auto h-12 w-12 text-muted-foreground"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={1.5}
                      d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                  <p className="text-muted-foreground">No pending reviews</p>
                  <p className="text-sm text-muted-foreground">
                    All checkpoints have been reviewed
                  </p>
                </div>
              </CardContent>
            </Card>
          )}

          {!loading && pendingReviews.length > 0 && (
            <div className="grid gap-4">
              {pendingReviews.map((review) => (
                <Card key={`${review.workflow_id}-${review.checkpoint_id}`}>
                  <CardHeader>
                    <div className="flex justify-between items-start">
                      <div>
                        <CardTitle className="flex items-center gap-2">
                          {review.checkpoint_name}
                        </CardTitle>
                        <CardDescription>
                          Workflow: {review.workflow_id.slice(0, 8)}...
                        </CardDescription>
                      </div>
                      <Badge variant={getStatusColor(review.status)}>
                        {review.status.replace(/_/g, " ")}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-muted-foreground">
                        Submitted: {formatDate(review.created_at)}
                      </span>
                      <div className="flex gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setSelectedReview(review)}
                        >
                          View Details
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => openActionDialog("revision", review)}
                        >
                          Request Revision
                        </Button>
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={() => openActionDialog("reject", review)}
                        >
                          Reject
                        </Button>
                        <Button
                          size="sm"
                          onClick={() => openActionDialog("approve", review)}
                        >
                          Approve
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="completed" className="mt-4">
          <Card>
            <CardContent className="pt-6 text-center">
              <p className="text-muted-foreground">
                Completed reviews will appear here
              </p>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Action Dialog */}
      <Dialog open={!!reviewAction} onOpenChange={() => closeActionDialog()}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {reviewAction?.type === "approve"
                ? "Approve Checkpoint"
                : reviewAction?.type === "reject"
                ? "Reject Checkpoint"
                : "Request Revision"}
            </DialogTitle>
            <DialogDescription>
              {reviewAction?.checkpointName}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="comments">
                Comments {reviewAction?.type !== "approve" && "*"}
              </Label>
              <Textarea
                id="comments"
                placeholder={
                  reviewAction?.type === "approve"
                    ? "Optional comments..."
                    : "Provide detailed feedback..."
                }
                value={comments}
                onChange={(e) => setComments(e.target.value)}
                rows={4}
              />
            </div>

            {reviewAction?.type !== "approve" && (
              <div className="space-y-2">
                <Label htmlFor="issues">Specific Issues (one per line)</Label>
                <Textarea
                  id="issues"
                  placeholder="List specific issues that need to be addressed..."
                  value={specificIssues}
                  onChange={(e) => setSpecificIssues(e.target.value)}
                  rows={3}
                />
              </div>
            )}
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={closeActionDialog}>
              Cancel
            </Button>
            <Button
              onClick={handleAction}
              disabled={actionLoading || (reviewAction?.type !== "approve" && !comments)}
              variant={reviewAction?.type === "reject" ? "destructive" : "default"}
            >
              {actionLoading ? "Processing..." : "Confirm"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Details Dialog */}
      <Dialog open={!!selectedReview} onOpenChange={() => setSelectedReview(null)}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{selectedReview?.checkpoint_name}</DialogTitle>
            <DialogDescription>
              Review the agent output below
            </DialogDescription>
          </DialogHeader>

          {selectedReview?.agent_output && (
            <div className="space-y-4">
              <pre className="p-4 bg-muted rounded-md text-sm overflow-x-auto">
                {JSON.stringify(selectedReview.agent_output, null, 2)}
              </pre>
            </div>
          )}

          <DialogFooter>
            <Button variant="outline" onClick={() => setSelectedReview(null)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
