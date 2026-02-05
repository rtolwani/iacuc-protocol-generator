import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export default function Home() {
  return (
    <div className="space-y-12">
      {/* Hero Section with Gradient */}
      <section className="text-center py-16 rounded-2xl bg-gradient-to-br from-blue-600 via-purple-600 to-indigo-700 text-white shadow-xl">
        <div className="inline-flex items-center gap-2 bg-white/20 backdrop-blur-sm rounded-full px-4 py-2 mb-6">
          <span className="animate-pulse w-2 h-2 bg-green-400 rounded-full"></span>
          <span className="text-sm font-medium">AI-Powered Research Compliance</span>
        </div>
        <h1 className="text-5xl font-bold tracking-tight mb-4">
          IACUC Protocol Generator
        </h1>
        <p className="text-xl text-blue-100 max-w-2xl mx-auto mb-8">
          Streamline your IACUC protocol submissions with AI-powered assistance. 
          Generate compliant protocols in minutes, not days.
        </p>
        <div className="flex gap-4 justify-center">
          <Button asChild size="lg" className="bg-white text-purple-700 hover:bg-blue-50 font-semibold shadow-lg">
            <Link href="/protocols/new">🚀 Start New Protocol</Link>
          </Button>
          <Button variant="outline" size="lg" asChild className="border-white text-white hover:bg-white/20">
            <Link href="/protocols">View Protocols</Link>
          </Button>
        </div>
      </section>

      {/* Features Section */}
      <section>
        <h2 className="text-3xl font-bold text-center mb-2">Key Features</h2>
        <p className="text-center text-muted-foreground mb-8">Everything you need for IACUC compliance</p>
        <div className="grid md:grid-cols-3 gap-6">
          <Card className="border-t-4 border-t-blue-500 hover:shadow-lg transition-all hover:-translate-y-1">
            <CardHeader>
              <div className="w-12 h-12 rounded-lg bg-blue-100 flex items-center justify-center mb-3">
                <svg className="h-6 w-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
              </div>
              <CardTitle>Guided Questionnaire</CardTitle>
              <CardDescription>
                Step-by-step questions with intelligent branching
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Answer questions about your research and watch as the system 
                adapts to show only relevant sections based on your responses.
              </p>
            </CardContent>
          </Card>

          <Card className="border-t-4 border-t-green-500 hover:shadow-lg transition-all hover:-translate-y-1">
            <CardHeader>
              <div className="w-12 h-12 rounded-lg bg-green-100 flex items-center justify-center mb-3">
                <svg className="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <CardTitle>Compliance Checking</CardTitle>
              <CardDescription>
                Real-time regulatory compliance validation
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Automatically checks against USDA regulations, AVMA guidelines, 
                and institutional policies to flag potential issues early.
              </p>
            </CardContent>
          </Card>

          <Card className="border-t-4 border-t-purple-500 hover:shadow-lg transition-all hover:-translate-y-1">
            <CardHeader>
              <div className="w-12 h-12 rounded-lg bg-purple-100 flex items-center justify-center mb-3">
                <svg className="h-6 w-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
              </div>
              <CardTitle>3Rs Assessment</CardTitle>
              <CardDescription>
                AI-powered literature search for alternatives
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Automatically searches databases to support your 3Rs statements 
                for Replacement, Reduction, and Refinement.
              </p>
            </CardContent>
          </Card>

          <Card className="border-t-4 border-t-orange-500 hover:shadow-lg transition-all hover:-translate-y-1">
            <CardHeader>
              <div className="w-12 h-12 rounded-lg bg-orange-100 flex items-center justify-center mb-3">
                <svg className="h-6 w-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <CardTitle>Power Analysis</CardTitle>
              <CardDescription>
                Statistical calculations for sample size
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Built-in power analysis tools help you determine the minimum 
                number of animals needed for statistically valid results.
              </p>
            </CardContent>
          </Card>

          <Card className="border-t-4 border-t-pink-500 hover:shadow-lg transition-all hover:-translate-y-1">
            <CardHeader>
              <div className="w-12 h-12 rounded-lg bg-pink-100 flex items-center justify-center mb-3">
                <svg className="h-6 w-6 text-pink-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                </svg>
              </div>
              <CardTitle>Drug Formulary</CardTitle>
              <CardDescription>
                Species-specific drug dosing validation
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Access institutional drug formulary with validated doses, 
                routes, and species-specific recommendations.
              </p>
            </CardContent>
          </Card>

          <Card className="border-t-4 border-t-cyan-500 hover:shadow-lg transition-all hover:-translate-y-1">
            <CardHeader>
              <div className="w-12 h-12 rounded-lg bg-cyan-100 flex items-center justify-center mb-3">
                <svg className="h-6 w-6 text-cyan-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
              </div>
              <CardTitle>Export Options</CardTitle>
              <CardDescription>
                Download protocols in multiple formats
              </CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Export your completed protocol to PDF or Word format, 
                ready for submission to your IACUC office.
              </p>
            </CardContent>
          </Card>
        </div>
      </section>

      {/* CTA Section */}
      <section className="rounded-2xl p-12 text-center bg-gradient-to-r from-emerald-500 to-teal-600 text-white shadow-xl">
        <h2 className="text-3xl font-bold mb-4">Ready to Get Started?</h2>
        <p className="text-emerald-100 mb-8 text-lg">
          Create your first AI-assisted IACUC protocol in minutes.
        </p>
        <Button asChild size="lg" className="bg-white text-emerald-700 hover:bg-emerald-50 font-semibold shadow-lg">
          <Link href="/protocols/new">🎯 Start New Protocol</Link>
        </Button>
      </section>
    </div>
  );
}
