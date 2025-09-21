"use client"

import React, { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { Loader2, Github, Copy, HelpCircle, ExternalLink } from 'lucide-react';

// --- TYPE DEFINITIONS ---
interface PullRequest {
  number: number;
  title: string;
  created_at: string;
  user: string;
  state: 'open' | 'closed';
}

interface AutomatedReview {
  number: number;
  title: string;
  score: number;
}

interface ReviewResult {
  summary: string;
  comments: {
    file_path: string;
    line: number;
    severity: string;
    category: string;
    comment: string;
    suggestion?: string;
  }[];
  scores: {
    structure_design: number;
    standards_compliance: number;
    security_safety: number;
    performance: number;
    testing_reliability: number;
  };
  overall_score: number;
  recommendations: string[];
  positive_highlights: string[];
  markdown_summary: string;
}

// --- HELPER COMPONENTS ---
const ScoreCard = ({ title, score }: { title: string; score: number }) => (
    <div className="p-4 bg-secondary rounded-lg">
        <p className="text-sm text-muted-foreground">{title}</p>
        <p className="text-2xl font-bold">{score}/10</p>
    </div>
);

const CommentCard = ({ comment }: { comment: ReviewResult['comments'][0] }) => {
    const severityColors: { [key: string]: string } = {
        CRITICAL: 'border-red-500 bg-red-50',
        MAJOR: 'border-orange-500 bg-orange-50',
        MINOR: 'border-yellow-500 bg-yellow-50',
        SUGGESTION: 'border-blue-500 bg-blue-50',
    };
    return (
        <div className={`p-4 rounded-lg border-l-4 ${severityColors[comment.severity] || 'border-gray-500'}`}>
            <p className="font-mono text-sm font-semibold">{comment.file_path}:{comment.line}</p>
            <p className="mt-2">{comment.comment}</p>
            {comment.suggestion && (
                <div className="mt-2 p-2 bg-background rounded">
                    <p className="text-sm font-semibold">💡 Suggestion:</p>
                    <pre className="text-xs whitespace-pre-wrap font-mono"><code>{comment.suggestion}</code></pre>
                </div>
            )}
        </div>
    );
};

// --- MAIN COMPONENT ---
export default function AIReviewAgent() {
  // State Management
  const [step, setStep] = useState(1); // 1: Enter Repo, 2: Select PR
  const [githubUrl, setGithubUrl] = useState("");
  const [pullRequests, setPullRequests] = useState<PullRequest[]>([]);
  const [selectedPr, setSelectedPr] = useState<string>("");
  const [prFilter, setPrFilter] = useState<'open' | 'closed'>('open');
  const [prPage, setPrPage] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [isReviewing, setIsReviewing] = useState(false);
  const [result, setResult] = useState<ReviewResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [errorDetails, setErrorDetails] = useState<string | null>(null);

  // This function is defined within the parent component to access setSelectedPr
  const PRDisplayContent = ({ prs }: { prs: PullRequest[] }) => {
    // Sort PRs by number in descending order (newest first)
    const sortedPrs = [...prs].sort((a, b) => b.number - a.number);

    const PAGE_SIZE = 50;
    const totalPages = Math.ceil(sortedPrs.length / PAGE_SIZE);
    const startIndex = prPage * PAGE_SIZE;
    const endIndex = startIndex + PAGE_SIZE;
    const paginatedPrs = sortedPrs.slice(startIndex, endIndex);

    const pageRanges = Array.from({ length: totalPages }, (_, i) => {
      const pageStartIndex = i * PAGE_SIZE;
      const pageEndIndex = Math.min(pageStartIndex + PAGE_SIZE - 1, sortedPrs.length - 1);
      
      const startNumber = sortedPrs[pageStartIndex]?.number;
      const endNumber = sortedPrs[pageEndIndex]?.number;

      // The PR numbers are descending, so the 'start' of the range is the highest number
      return { label: `PRs #${startNumber} - #${endNumber}`, value: i };
    });

    return (
      <div className="space-y-4">
        {totalPages > 1 && (
          <div className="space-y-2">
            <Label>Filter by Range</Label>
            <Select onValueChange={(val) => setPrPage(Number(val))} value={String(prPage)}>
                <SelectTrigger>
                    <SelectValue placeholder="Select a PR range..." />
                </SelectTrigger>
                <SelectContent>
                    {pageRanges.map(range => (
                        <SelectItem key={range.value} value={String(range.value)}>
                            {range.label}
                        </SelectItem>
                    ))}
                </SelectContent>
            </Select>
          </div>
        )}
        <PRSelectContent prs={paginatedPrs} />
      </div>
    );
  };

  const PRSelectContent = ({ prs }: { prs: PullRequest[] }) => (
    <div className="space-y-2 pt-4">
        <Label htmlFor="pr-select">Select Pull Request</Label>
        <Select onValueChange={setSelectedPr} value={selectedPr}>
            <SelectTrigger id="pr-select">
                <SelectValue placeholder="Choose a PR to review..." />
            </SelectTrigger>
            <SelectContent>
                {prs.length > 0 ? (
                    prs.map((pr) => (
                        <SelectItem key={pr.number} value={String(pr.number)}>
                            #{pr.number}: {pr.title} ({pr.user})
                        </SelectItem>
                    ))
                ) : (
                    <div className="p-4 text-sm text-muted-foreground">No pull requests in this category.</div>
                )}
            </SelectContent>
        </Select>
    </div>
  );

  // --- API HANDLERS ---
  const handleFetchPRs = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!githubUrl.trim()) {
      setError("Please enter a GitHub repository URL");
      return;
    }

    setIsLoading(true);
    setError(null);
    setPullRequests([]);
    setResult(null);

    try {
      const response = await fetch('http://localhost:5001/api/validate_repo', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repo_url: githubUrl }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to fetch pull requests.');
      }

      const data: PullRequest[] = await response.json();
      if (data.length === 0) {
        setError("No pull requests (open or closed) found in this repository.");
      } else {
        setPullRequests(data);
        setStep(2);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const handleReviewPR = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedPr) {
      setError("Please select a pull request to review.");
      return;
    }

    setIsReviewing(true);
    setError(null);
    setErrorDetails(null);
    setResult(null);

    try {
      const repoPath = new URL(githubUrl).pathname.split('/').filter(p => p);
      const repo = `${repoPath[0]}/${repoPath[1]}`;

      const response = await fetch('http://localhost:5001/api/review', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repo, pr_id: Number(selectedPr), provider: 'github' }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        // Throw the whole error object so we can catch the details field
        throw errorData;
      }

      const data: ReviewResult = await response.json();
      setResult(data);
    } catch (err: any) {
      // Handle both standard errors and our custom structured errors
      setError(err.error || err.message || 'An unknown error occurred during analysis.');
      if (err.details) {
        setErrorDetails(err.details);
      }
    } finally {
      setIsReviewing(false);
    }
  };

  const getScoreColor = (score: number): string => {
    if (score >= 80) return "text-green-600";
    if (score >= 50) return "text-yellow-600";
    return "text-red-600";
  };

  const RepoStep = () => (
    <form onSubmit={handleFetchPRs} className="space-y-4 pt-4">
      <h2 className="text-2xl font-semibold text-center">Step 1: Enter Repository URL</h2>
      <div className="space-y-2">
        <Label htmlFor="github-url">GitHub Repository URL</Label>
        <Input
          id="github-url"
          type="url"
          placeholder="https://github.com/owner/repo"
          value={githubUrl}
          onChange={(e) => setGithubUrl(e.target.value)}
          required
          disabled={isLoading}
        />
      </div>
      <Button type="submit" className="w-full" disabled={isLoading}>
        {isLoading ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Fetching...</> : "Fetch Pull Requests"}
      </Button>
    </form>
  );

  const PRStep = () => (
    <form onSubmit={handleReviewPR} className="space-y-6 pt-4">
      <h2 className="text-2xl font-semibold text-center">Step 2: Select Pull Request</h2>
      <div className="space-y-2">
        <Label>Repository</Label>
        <Input value={githubUrl} disabled />
      </div>
      <Tabs value={prFilter} onValueChange={(value) => setPrFilter(value as 'open' | 'closed')} className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="open">Open</TabsTrigger>
          <TabsTrigger value="closed">Closed</TabsTrigger>
        </TabsList>
        <TabsContent value="open">
          <PRDisplayContent prs={pullRequests.filter(pr => pr.state === 'open')} />
        </TabsContent>
        <TabsContent value="closed">
            <PRDisplayContent prs={pullRequests.filter(pr => pr.state === 'closed')} />
        </TabsContent>
      </Tabs>
      <div className="flex gap-2">
          <Button type="button" variant="outline" onClick={resetState} className="w-1/3">Back</Button>
          <Button type="submit" className="w-2/3" disabled={isReviewing || !selectedPr}>
            {isReviewing ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Analyzing...</> : "Analyze PR"}
          </Button>
      </div>
    </form>
  );

  const resetState = () => {
    setStep(1);
    // Do not reset githubUrl, so the user can easily try again
    setPullRequests([]);
    setSelectedPr("");
    setResult(null);
    setError(null);
    setErrorDetails(null);
    setPrFilter('open');
    setPrPage(0);
  }

  const AutomatedReviewSetup = () => {
    const [repoUrl, setRepoUrl] = useState('');
    const [owner, setOwner] = useState('');
    const [repo, setRepo] = useState('');
    const [workflowExists, setWorkflowExists] = useState<boolean | null>(null);
    const [reviews, setReviews] = useState<AutomatedReview[]>([]);
    const [isLoading, setIsLoading] = useState(false);

    const handleUrlSubmit = async (url: string) => {
      setIsLoading(true);
      setWorkflowExists(null);
      setReviews([]);
      try {
        // 1. Check if workflow file exists
        const workflowRes = await fetch('http://localhost:5001/api/check_workflow', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ repo_url: url }),
        });
        const workflowData = await workflowRes.json();

        if (workflowData.exists) {
          setWorkflowExists(true);
          // 2. If it exists, fetch the reviews
          const reviewsRes = await fetch('http://localhost:5001/api/get_reviews', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ repo_url: url }),
          });
          const reviewsData = await reviewsRes.json();
          setReviews(reviewsData);
        } else {
          setWorkflowExists(false);
        }

      } catch (err) {
        setError('Failed to check repository status. Please ensure the backend is running and the URL is correct.');
        setWorkflowExists(false);
      } finally {
        setIsLoading(false);
      }
    };

    const handleUrlChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const url = e.target.value;
      setRepoUrl(url);
      try {
        const parsedUrl = new URL(url);
        if (parsedUrl.hostname === 'github.com') {
          const pathParts = parsedUrl.pathname.slice(1).split('/');
          if (pathParts.length >= 2) {
            setOwner(pathParts[0]);
            setRepo(pathParts[1].replace('.git', ''));
          }
        } else {
          setOwner('');
          setRepo('');
        }
      } catch (error) {
        setOwner('');
        setRepo('');
      }
    };

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        if (repoUrl) {
            handleUrlSubmit(repoUrl);
        }
    };

    const workflowYaml = `
name: AI Code Review

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout Repo
        uses: actions/checkout@v3

      - name: Run AI Review Agent
        uses: your-github-username/pr-review-agent-action@v1 # Replace with the actual action path when published
        with:
          repo_owner: "${owner}"
          repo_name: "${repo}"
          pr_number: $\{{ github.event.pull_request.number }}
          github_token: $\{{ secrets.GITHUB_TOKEN }}
          gemini_api_key: $\{{ secrets.GEMINI_API_KEY }}
          neo4j_uri: $\{{ secrets.NEO4J_URI }}
          neo4j_user: $\{{ secrets.NEO4J_USER }}
          neo4j_password: $\{{ secrets.NEO4J_PASSWORD }}
    `;

    const SetupInstructions = () => (
        <div className="space-y-6">
            <div className="p-4 border rounded-lg bg-muted/20">
              <h4 className="font-semibold text-lg mb-4">Step 1: Add Secrets to Your Repository</h4>
              <p className="text-muted-foreground mb-4">Go to your GitHub repository's <code className="bg-muted p-1 rounded">Settings &gt; Secrets and variables &gt; Actions</code> page and add the following repository secrets:</p>
              <ul className="list-disc list-inside space-y-2 text-sm">
                <li><code className="bg-muted p-1 rounded">GEMINI_API_KEY</code>: Your API key for the Gemini model.</li>
                <li><code className="bg-muted p-1 rounded">NEO4J_URI</code>: The connection URI for your Neo4j database.</li>
                <li><code className="bg-muted p-1 rounded">NEO4J_USER</code>: The username for your Neo4j database.</li>
                <li><code className="bg-muted p-1 rounded">NEO4J_PASSWORD</code>: The password for your Neo4j database.</li>
              </ul>
            </div>

            <div className="p-4 border rounded-lg bg-muted/20">
              <h4 className="font-semibold text-lg mb-2">Step 2: Create the Workflow File</h4>
              <p className="text-muted-foreground mb-4">In your repository, create a new file at the following path: <code className="bg-muted p-1 rounded">.github/workflows/ai-review.yml</code>. Paste the content below into the file.</p>
              <div className="bg-muted rounded-md p-4 relative">
                <pre className="text-sm whitespace-pre-wrap font-mono">{workflowYaml}</pre>
                <Button 
                  variant="ghost" 
                  size="icon" 
                  className="absolute top-2 right-2"
                  onClick={() => navigator.clipboard.writeText(workflowYaml)}
                >
                  <Copy className="h-4 w-4" />
                </Button>
              </div>
            </div>
             <div className="text-center pt-4">
                <p className="text-muted-foreground">Once you commit this file, the action will run on all new pull requests.</p>
            </div>
        </div>
    );

    const ReviewsDashboard = () => (
        <div className="space-y-4">
            <h3 className="text-2xl font-semibold">Automated Review Dashboard</h3>
            {reviews.length > 0 ? (
                <Card>
                    <CardContent className="p-0">
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm">
                                <thead className="bg-muted/50">
                                    <tr>
                                        <th className="p-4 text-left font-semibold">Pull Request</th>
                                        <th className="p-4 text-left font-semibold">Score</th>
                                        <th className="p-4 text-right font-semibold">Link</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {reviews.map(review => (
                                        <tr key={review.number} className="border-t">
                                            <td className="p-4 font-medium">#{review.number}: {review.title}</td>
                                            <td className={`p-4 font-bold ${getScoreColor(review.score)}`}>{review.score}/100</td>
                                            <td className="p-4 text-right">
                                                <a href={`${repoUrl}/pull/${review.number}`} target="_blank" rel="noopener noreferrer" className="inline-flex items-center text-primary hover:underline">
                                                    View <ExternalLink className="ml-1 h-4 w-4" />
                                                </a>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </CardContent>
                </Card>
            ) : (
                <div className="text-center py-12 border-2 border-dashed rounded-lg">
                    <p className="text-muted-foreground">No automated reviews found for this repository.</p>
                    <p className="text-sm text-muted-foreground mt-2">Open a new pull request to trigger the first review.</p>
                </div>
            )}
        </div>
    );

    return (
      <div className="space-y-6 pt-4">
        <div className="text-center">
            <h3 className="text-2xl font-semibold">Automated Reviews</h3>
            <p className="text-muted-foreground mt-2">Check the status of automated reviews or set them up for your repository.</p>
        </div>
        
        <form onSubmit={handleSubmit} className="flex items-end gap-2">
          <div className="flex-grow space-y-2">
            <Label htmlFor="repo-url-automated">Your GitHub Repository URL</Label>
            <Input 
              id="repo-url-automated" 
              placeholder="https://github.com/owner/repository" 
              value={repoUrl}
              onChange={handleUrlChange}
              disabled={isLoading}
            />
          </div>
          <Button type="submit" disabled={isLoading || !repoUrl}>
            {isLoading ? <Loader2 className="h-4 w-4 animate-spin" /> : "Check Status"}
          </Button>
        </form>

        {isLoading && (
            <div className="flex items-center justify-center py-8">
                <Loader2 className="mr-2 h-8 w-8 animate-spin text-primary" />
                <span className="text-muted-foreground">Checking repository...</span>
            </div>
        )}

        {workflowExists === false && owner && repo && <SetupInstructions />}
        
        {workflowExists === true && (
            <div className="space-y-6">
                <div className="flex justify-between items-center p-3 bg-green-100 text-green-800 rounded-lg border border-green-200">
                    <p className="font-semibold">Automated reviews are active for this repository.</p>
                    <Collapsible>
                        <CollapsibleTrigger asChild>
                            <Button variant="ghost" size="sm" className="flex items-center gap-1">
                                <HelpCircle className="h-4 w-4" /> Show Setup
                            </Button>
                        </CollapsibleTrigger>
                        <CollapsibleContent className="mt-4 p-4 border bg-background rounded-lg shadow-lg">
                           <SetupInstructions />
                        </CollapsibleContent>
                    </Collapsible>
                </div>
                <ReviewsDashboard />
            </div>
        )}
      </div>
    );

  };

  // --- RENDER LOGIC ---
  return (
    <div className="min-h-screen bg-background">
      <header className="bg-primary text-primary-foreground">
        <div className="container mx-auto px-4 py-8 text-center">
          <h1 className="text-4xl font-bold mb-2">AI Pull Request Review Agent</h1>
          <p className="text-lg opacity-90">Your automated assistant for high-quality code reviews.</p>
        </div>
      </header>

      <main className="container mx-auto px-4 py-8 max-w-4xl">
        <Card className="shadow-lg">
          <CardContent className="p-6">
            <Tabs defaultValue="interactive" className="w-full">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="interactive">Interactive Review</TabsTrigger>
                <TabsTrigger value="automated" onClick={() => setStep(1)}>Automated Reviews</TabsTrigger>
              </TabsList>

              <TabsContent value="interactive" className="space-y-6">
                {step === 1 && <RepoStep />}
                {step === 2 && <PRStep />}
              </TabsContent>

              <TabsContent value="automated">
                <AutomatedReviewSetup />
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>

        {/* Error and Results Section */}
        {(isLoading || isReviewing || result || error) && (
          <Card className="mt-8 shadow-lg">
            <CardContent className="p-6">
              {(isLoading || isReviewing) && (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-8 w-8 animate-spin mr-3" />
                  <span className="text-lg">{isLoading ? 'Fetching pull requests...' : 'Analyzing your pull request...'}</span>
                </div>
              )}

              {error && (
                <Alert variant="destructive">
                  <AlertDescription>
                    <strong>Error:</strong> {error}
                  </AlertDescription>
                  {errorDetails && (
                    <Collapsible className="mt-4">
                      <CollapsibleTrigger asChild>
                        <Button variant="secondary" size="sm">Show Details</Button>
                      </CollapsibleTrigger>
                      <CollapsibleContent className="mt-2">
                        <pre className="bg-muted p-4 rounded-md text-xs whitespace-pre-wrap font-mono">
                          <code>{errorDetails}</code>
                        </pre>
                      </CollapsibleContent>
                    </Collapsible>
                  )}
                </Alert>
              )}

              {result && (
                <div className="space-y-8">
                  <div className="text-center">
                    <p className={`text-4xl font-bold ${getScoreColor(result.overall_score * 10)}`}>
                      {result.overall_score.toFixed(1)} / 10
                    </p>
                    <p className="text-muted-foreground mt-2">Overall Quality Score</p>
                  </div>
                  <Alert><AlertDescription>{result.summary}</AlertDescription></Alert>
                  <div>
                    <h3 className="text-xl font-semibold mb-4">Detailed Scores</h3>
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-center">
                        <ScoreCard title="🏗️ Structure & Design" score={result.scores.structure_design} />
                        <ScoreCard title="📋 Standards" score={result.scores.standards_compliance} />
                        <ScoreCard title="🔒 Security & Safety" score={result.scores.security_safety} />
                        <ScoreCard title="⚡ Performance" score={result.scores.performance} />
                        <ScoreCard title="🧪 Testing" score={result.scores.testing_reliability} />
                    </div>
                  </div>
                  {result.positive_highlights?.length > 0 && (
                    <div>
                      <h3 className="text-xl font-semibold mb-3">✅ What You Did Well</h3>
                      <ul className="list-disc list-inside space-y-1 text-green-700">
                        {result.positive_highlights.map((h, i) => <li key={i}>{h}</li>)}
                      </ul>
                    </div>
                  )}
                  {result.recommendations?.length > 0 && (
                    <div>
                      <h3 className="text-xl font-semibold mb-3">🎯 Key Recommendations</h3>
                      <ul className="list-disc list-inside space-y-1">
                        {result.recommendations.map((r, i) => <li key={i}>{r}</li>)}
                      </ul>
                    </div>
                  )}
                  {result.comments?.length > 0 && (
                    <div>
                      <h3 className="text-xl font-semibold mb-3">📝 Detailed Suggestions</h3>
                      <div className="space-y-4">
                        {result.comments.map((c, i) => <CommentCard key={i} comment={c} />)}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </main>
    </div>
  )
}
