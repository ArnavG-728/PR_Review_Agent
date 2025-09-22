"use client"

import React, { useState, useEffect, useCallback, useMemo } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible"
import { Loader2, Github, Copy, HelpCircle, ExternalLink } from 'lucide-react';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5001';

// --- TYPE DEFINITIONS ---
interface GitProvider {
  id: string;
  name: string;
  description: string;
  icon: string;
  requires_token: boolean;
  supports_enterprise: boolean;
  implemented: boolean;
}

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
    title?: string;
    comment: string;
    evidence?: string;
    suggestion?: string;
    learning_opportunity?: string;
    priority?: number;
  }[];
  scores: {
    // Legacy scores (for backward compatibility)
    structure_design?: number;
    standards_compliance?: number;
    performance?: number;
    // Enhanced scores (new format)
    security_safety?: number;
    performance_efficiency?: number;
    architecture_design?: number;
    maintainability_readability?: number;
    testing_reliability?: number;
    documentation_clarity?: number;
  };
  overall_score: number;
  recommendations: string[] | {
    immediate_actions?: string[];
    short_term_improvements?: string[];
    long_term_considerations?: string[];
    learning_resources?: string[];
  };
  positive_highlights: string[] | {
    aspect: string;
    impact: string;
    encouragement: string;
  }[];
  markdown_summary: string;
  executive_summary?: string;
  action_items?: any[];
  meta_analysis?: {
    change_intent: string;
    risk_level: string;
    complexity_assessment: string;
    architectural_impact: string;
  };
  risk_assessment?: {
    deployment_readiness: string;
    security_risk: string;
    performance_risk: string;
    operational_risk: string;
  };
  mentorship_notes?: {
    growth_opportunities: string;
    strength_recognition: string;
    suggested_focus: string;
  };
  pr_details?: {
    number: number;
    title: string;
    author: string;
    provider: string;
    url: string;
  };
  // Legacy compatibility
  score?: number;
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
        POSITIVE: 'border-green-500 bg-green-50',
    };
    
    const priorityBadges: { [key: number]: string } = {
        1: 'bg-red-100 text-red-800',
        2: 'bg-orange-100 text-orange-800',
        3: 'bg-yellow-100 text-yellow-800',
        4: 'bg-blue-100 text-blue-800',
        5: 'bg-green-100 text-green-800',
    };
    
    return (
        <div className={`p-4 rounded-lg border-l-4 ${severityColors[comment.severity] || 'border-gray-500'}`}>
            <div className="flex items-start justify-between mb-2">
                <div>
                    <p className="font-mono text-sm font-semibold">{comment.file_path}:{comment.line}</p>
                    {comment.title && (
                        <h4 className="font-semibold text-lg mt-1">{comment.title}</h4>
                    )}
                </div>
                <div className="flex gap-2">
                    <span className="px-2 py-1 text-xs rounded-full bg-gray-100 text-gray-800">
                        {comment.category}
                    </span>
                    {comment.priority && (
                        <span className={`px-2 py-1 text-xs rounded-full ${priorityBadges[comment.priority] || 'bg-gray-100 text-gray-800'}`}>
                            P{comment.priority}
                        </span>
                    )}
                </div>
            </div>
            
            <p className="mt-2 text-gray-700">{comment.comment}</p>
            
            {comment.evidence && (
                <div className="mt-3 p-2 bg-gray-50 rounded border">
                    <p className="text-sm font-semibold text-gray-600 mb-1">📋 Evidence:</p>
                    <pre className="text-xs whitespace-pre-wrap font-mono text-gray-800">{comment.evidence}</pre>
                </div>
            )}
            
            {comment.suggestion && (
                <div className="mt-3 p-2 bg-background rounded border">
                    <p className="text-sm font-semibold text-green-600 mb-1">💡 Suggested Solution:</p>
                    <pre className="text-xs whitespace-pre-wrap font-mono text-gray-800">{comment.suggestion}</pre>
                </div>
            )}
            
            {comment.learning_opportunity && comment.learning_opportunity !== 'Consider researching best practices for this area' && (
                <div className="mt-3 p-2 bg-blue-50 rounded border border-blue-200">
                    <p className="text-sm font-semibold text-blue-600 mb-1">📚 Learning Opportunity:</p>
                    <p className="text-sm text-blue-800">{comment.learning_opportunity}</p>
                </div>
            )}
        </div>
    );
};

// --- MAIN COMPONENT ---
export default function AIReviewAgent() {
  // State Management
  const [step, setStep] = useState(1); // 1: Select Provider, 2: Enter Repo, 3: Select PR
  const [providers, setProviders] = useState<GitProvider[]>([]);
  const [selectedProvider, setSelectedProvider] = useState<string>("");
  const [repoUrl, setRepoUrl] = useState("");
  const [accessToken, setAccessToken] = useState("");
  const [pullRequests, setPullRequests] = useState<PullRequest[]>([]);
  const [selectedPr, setSelectedPr] = useState<string>("");
  const [prFilter, setPrFilter] = useState<'open' | 'closed'>('open');
  const [prPage, setPrPage] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [isReviewing, setIsReviewing] = useState(false);
  const [result, setResult] = useState<ReviewResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [errorDetails, setErrorDetails] = useState<string | null>(null);

  // Fetch providers on component mount
  useEffect(() => {
    const fetchProviders = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/providers`);
        if (response.ok) {
          const data = await response.json();
          setProviders(data.providers);
          // Auto-select GitHub if available
          const github = data.providers.find((p: GitProvider) => p.id === 'github');
          if (github) {
            setSelectedProvider('github');
          }
        }
      } catch (error) {
        console.error('Failed to fetch providers:', error);
      }
    };
    fetchProviders();
  }, []);

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
    if (!repoUrl.trim()) {
      setError("Please enter a repository URL");
      return;
    }
    if (!selectedProvider) {
      setError("Please select a Git provider");
      return;
    }

    setIsLoading(true);
    setError(null);
    setPullRequests([]);
    setResult(null);

    try {
      const requestBody: any = { 
        repo_url: repoUrl, 
        provider: selectedProvider 
      };
      
      // Add token if provided and required
      const provider = providers.find(p => p.id === selectedProvider);
      if (provider?.requires_token && accessToken.trim()) {
        requestBody.token = accessToken;
      }

      const response = await fetch(`${API_BASE_URL}/api/validate_repo`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to fetch pull requests.');
      }

      const data = await response.json();
      
      // Handle different response formats
      if (Array.isArray(data)) {
        // GitHub response with PR list
        if (data.length === 0) {
          setError("No pull requests (open or closed) found in this repository.");
        } else {
          setPullRequests(data);
          setStep(3);
        }
      } else if (data.valid) {
        // Other providers - just validation success
        setError(null);
        setStep(3);
        // For now, show empty PR list for non-GitHub providers
        setPullRequests([]);
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
      const url = new URL(repoUrl);
      const pathParts = url.pathname.slice(1).split('/');
      const repo = `${pathParts[0]}/${pathParts[1]}`;

      const requestBody: any = {
        repo: repo,
        pr_id: parseInt(selectedPr),
        provider: selectedProvider
      };

      // Add token if provided and required
      const provider = providers.find(p => p.id === selectedProvider);
      if (provider?.requires_token && accessToken.trim()) {
        requestBody.token = accessToken;
      }

      const response = await fetch(`${API_BASE_URL}/api/review`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
      });

      if (!response.ok) {
        const errorData = await response.json();
        setError(errorData.error || 'Failed to analyze pull request.');
        if (errorData.details) {
          setErrorDetails(errorData.details);
        }
        return;
      }

      const result: ReviewResult = await response.json();
      setResult(result);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setIsReviewing(false);
    }
  };

  const getScoreColor = useCallback((score: number): string => {
    if (score >= 80) return "text-green-600";
    if (score >= 50) return "text-yellow-600";
    return "text-red-600";
  }, []);

  const selectedProviderData = useMemo(() => 
    providers.find(p => p.id === selectedProvider), 
    [providers, selectedProvider]
  );

  const PRStep = () => (
    <form onSubmit={handleReviewPR} className="space-y-6 pt-4">
      <h2 className="text-2xl font-semibold text-center">Step 3: Select Pull Request</h2>
      <div className="space-y-2">
        <Label>Repository</Label>
        <div className="flex items-center gap-2 p-2 bg-muted rounded">
          <span className="font-mono text-sm">{repoUrl}</span>
          <Button type="button" variant="ghost" size="sm" onClick={() => setStep(2)}>
            Change
          </Button>
        </div>
      </div>
      
      {pullRequests.length > 0 ? (
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
      ) : (
        <div className="text-center py-8">
          <p className="text-muted-foreground">
            {selectedProvider === 'github' 
              ? "No pull requests found in this repository." 
              : `Pull request listing is not yet available for ${providers.find(p => p.id === selectedProvider)?.name}. You can manually enter a PR number below.`
            }
          </p>
          {!['github'].includes(selectedProvider) && (
            <div className="mt-4 space-y-2">
              <Label htmlFor="manual-pr">Pull Request Number</Label>
              <Input
                id="manual-pr"
                type="number"
                placeholder="Enter PR number..."
                value={selectedPr}
                onChange={(e) => setSelectedPr(e.target.value)}
                className="max-w-xs mx-auto"
              />
            </div>
          )}
        </div>
      )}
      
      <div className="flex gap-2">
          <Button type="button" variant="outline" onClick={() => setStep(2)} className="w-1/3">Back</Button>
          <Button type="submit" className="w-2/3" disabled={isReviewing || !selectedPr}>
            {isReviewing ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Analyzing...</> : "Analyze PR"}
          </Button>
      </div>
    </form>
  );

  const resetState = () => {
    setStep(1);
    // Do not reset repoUrl and selectedProvider, so the user can easily try again
    setPullRequests([]);
    setSelectedPr("");
    setResult(null);
    setError(null);
    setErrorDetails(null);
    setPrFilter('open');
    setPrPage(0);
  }

  // --- STEP COMPONENTS ---
  const ProviderStep = () => {
    return (
      <div className="space-y-6 pt-4">
        <h2 className="text-2xl font-semibold text-center">Step 1: Select Git Provider</h2>
        
        <div className="space-y-2">
          <Label htmlFor="provider-select">Git Provider</Label>
          <Select onValueChange={setSelectedProvider} value={selectedProvider}>
            <SelectTrigger id="provider-select">
              <SelectValue placeholder="Choose a Git provider..." />
            </SelectTrigger>
            <SelectContent>
              {providers.map((provider) => (
                <SelectItem key={provider.id} value={provider.id} disabled={!provider.implemented}>
                  <div className="flex items-center gap-2">
                    <span>{provider.name}</span>
                    {!provider.implemented && <span className="text-xs text-muted-foreground">(Coming Soon)</span>}
                  </div>
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {selectedProviderData && (
            <p className="text-sm text-muted-foreground">{selectedProviderData.description}</p>
          )}
        </div>

        <Button 
          onClick={() => setStep(2)} 
          className="w-full" 
          disabled={!selectedProvider || !providers.find(p => p.id === selectedProvider)?.implemented}
        >
          Continue to Repository
        </Button>
      </div>
    );
  };

  const RepoStep = () => {
    const requiresToken = selectedProviderData?.requires_token;
    
    return (
      <form onSubmit={handleFetchPRs} className="space-y-4 pt-4">
        <h2 className="text-2xl font-semibold text-center">Step 2: Enter Repository Details</h2>
        
        <div className="space-y-2">
          <Label>Selected Provider</Label>
          <div className="flex items-center gap-2 p-2 bg-muted rounded">
            <span className="font-medium">{selectedProviderData?.name}</span>
            <Button type="button" variant="ghost" size="sm" onClick={() => setStep(1)}>
              Change
            </Button>
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="repo-url">Repository URL</Label>
          <Input
            id="repo-url"
            type="url"
            placeholder={`https://${selectedProvider === 'github' ? 'github.com' : selectedProvider === 'gitlab' ? 'gitlab.com' : selectedProvider === 'gitea' ? 'gitea.com' : selectedProvider + '.com'}/owner/repo`}
            value={repoUrl}
            onChange={(e) => setRepoUrl(e.target.value)}
            required
            disabled={isLoading}
          />
        </div>

        {requiresToken && (
          <div className="space-y-2">
            <Label htmlFor="access-token">
              Access Token 
              <span className="text-sm text-muted-foreground ml-1">(Optional for public repos)</span>
            </Label>
            <Input
              id="access-token"
              type="password"
              placeholder="Enter your access token..."
              value={accessToken}
              onChange={(e) => setAccessToken(e.target.value)}
              disabled={isLoading}
            />
            <p className="text-xs text-muted-foreground">
              Required for private repositories or to avoid rate limits
            </p>
          </div>
        )}

        <div className="flex gap-2">
          <Button type="button" variant="outline" onClick={() => setStep(1)} className="w-1/3">
            Back
          </Button>
          <Button type="submit" className="w-2/3" disabled={isLoading}>
            {isLoading ? <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Validating...</> : "Validate Repository"}
          </Button>
        </div>
      </form>
    );
  };

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
                const workflowRes = await fetch(`${API_BASE_URL}/api/check_workflow`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ repo_url: url }),
        });
        const workflowData = await workflowRes.json();

        if (workflowData.exists) {
          setWorkflowExists(true);
          // 2. If it exists, fetch the reviews
                    const reviewsRes = await fetch(`${API_BASE_URL}/api/get_reviews`, {
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
                {step === 1 && <ProviderStep />}
                {step === 2 && <RepoStep />}
                {step === 3 && <PRStep />}
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
                  {/* PR Title Header */}
                  {result.pr_details && (
                    <div className="text-center border-b pb-4">
                      <h2 className="text-2xl font-bold text-primary mb-2">
                        #{result.pr_details.number} - {result.pr_details.title}
                      </h2>
                      <div className="flex items-center justify-center gap-4 text-sm text-muted-foreground">
                        <span>👤 {result.pr_details.author}</span>
                        <span>🔗 {result.pr_details.provider}</span>
                        {result.pr_details.url && (
                          <a 
                            href={result.pr_details.url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-primary hover:underline"
                          >
                            View PR <ExternalLink className="h-3 w-3" />
                          </a>
                        )}
                      </div>
                    </div>
                  )}
                  
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
                        {/* Enhanced scores (new format) */}
                        {result.scores.security_safety !== undefined && (
                          <>
                            <ScoreCard title="🔒 Security & Safety" score={result.scores.security_safety || 0} />
                            <ScoreCard title="⚡ Performance" score={result.scores.performance_efficiency || 0} />
                            <ScoreCard title="🏗️ Architecture" score={result.scores.architecture_design || 0} />
                            <ScoreCard title="📖 Maintainability" score={result.scores.maintainability_readability || 0} />
                            <ScoreCard title="🧪 Testing" score={result.scores.testing_reliability || 0} />
                            <ScoreCard title="📝 Documentation" score={result.scores.documentation_clarity || 0} />
                          </>
                        )}
                        {/* Legacy scores (backward compatibility) */}
                        {result.scores.structure_design !== undefined && (
                          <>
                            <ScoreCard title="🏗️ Structure & Design" score={result.scores.structure_design || 0} />
                            <ScoreCard title="📋 Standards" score={result.scores.standards_compliance || 0} />
                            <ScoreCard title="🔒 Security & Safety" score={result.scores.security_safety || 0} />
                            <ScoreCard title="⚡ Performance" score={result.scores.performance || 0} />
                            <ScoreCard title="🧪 Testing" score={result.scores.testing_reliability || 0} />
                          </>
                        )}
                    </div>
                  </div>
                  {/* Enhanced positive highlights */}
                  {result.positive_highlights && (
                    <div>
                      <h3 className="text-xl font-semibold mb-3">✅ What You Did Well</h3>
                      {Array.isArray(result.positive_highlights) ? (
                        <ul className="list-disc list-inside space-y-1 text-green-700">
                          {result.positive_highlights.map((h: any, i: number) => (
                            <li key={i}>
                              {typeof h === 'string' ? h : (
                                <div>
                                  <strong>{h.aspect}</strong>: {h.impact}
                                  {h.encouragement && <div className="text-sm mt-1">{h.encouragement}</div>}
                                </div>
                              )}
                            </li>
                          ))}
                        </ul>
                      ) : (
                        <div className="space-y-2">
                          {Object.entries(result.positive_highlights).map(([key, value]: [string, any]) => (
                            <div key={key} className="p-3 bg-green-50 rounded-lg">
                              <strong>{key}</strong>: {value}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                  
                  {/* Enhanced recommendations */}
                  {result.recommendations && (
                    <div>
                      <h3 className="text-xl font-semibold mb-3">🎯 Key Recommendations</h3>
                      {Array.isArray(result.recommendations) ? (
                        <ul className="list-disc list-inside space-y-1">
                          {result.recommendations.map((r: string, i: number) => <li key={i}>{r}</li>)}
                        </ul>
                      ) : (
                        <div className="space-y-4">
                          {result.recommendations.immediate_actions && result.recommendations.immediate_actions.length > 0 && (
                            <div>
                              <h4 className="font-semibold text-red-600 mb-2">🚨 Immediate Actions</h4>
                              <ul className="list-disc list-inside space-y-1">
                                {result.recommendations.immediate_actions.map((action: string, i: number) => (
                                  <li key={i} className="text-red-700">{action}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                          {result.recommendations.short_term_improvements && result.recommendations.short_term_improvements.length > 0 && (
                            <div>
                              <h4 className="font-semibold text-orange-600 mb-2">⏭️ Short-term Improvements</h4>
                              <ul className="list-disc list-inside space-y-1">
                                {result.recommendations.short_term_improvements.map((improvement: string, i: number) => (
                                  <li key={i} className="text-orange-700">{improvement}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                          {result.recommendations.long_term_considerations && result.recommendations.long_term_considerations.length > 0 && (
                            <div>
                              <h4 className="font-semibold text-blue-600 mb-2">🔮 Long-term Considerations</h4>
                              <ul className="list-disc list-inside space-y-1">
                                {result.recommendations.long_term_considerations.map((consideration: string, i: number) => (
                                  <li key={i} className="text-blue-700">{consideration}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                          {result.recommendations.learning_resources && result.recommendations.learning_resources.length > 0 && (
                            <div>
                              <h4 className="font-semibold text-purple-600 mb-2">📚 Learning Resources</h4>
                              <ul className="list-disc list-inside space-y-1">
                                {result.recommendations.learning_resources.map((resource: string, i: number) => (
                                  <li key={i} className="text-purple-700">{resource}</li>
                                ))}
                              </ul>
                            </div>
                          )}
                        </div>
                      )}
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

                  {/* Risk Assessment */}
                  {result.risk_assessment && (
                    <div>
                      <h3 className="text-xl font-semibold mb-3">🚀 Deployment Assessment</h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="p-4 border rounded-lg">
                          <h4 className="font-semibold mb-2">Deployment Readiness</h4>
                          <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                            result.risk_assessment.deployment_readiness === 'READY' ? 'bg-green-100 text-green-800' :
                            result.risk_assessment.deployment_readiness === 'NEEDS_MINOR_CHANGES' ? 'bg-yellow-100 text-yellow-800' :
                            result.risk_assessment.deployment_readiness === 'NEEDS_MAJOR_CHANGES' ? 'bg-orange-100 text-orange-800' :
                            'bg-red-100 text-red-800'
                          }`}>
                            {result.risk_assessment.deployment_readiness}
                          </span>
                        </div>
                        
                        {result.risk_assessment.security_risk !== 'No specific security risks identified' && (
                          <div className="p-4 border rounded-lg border-red-200 bg-red-50">
                            <h4 className="font-semibold mb-2 text-red-800">🔒 Security Risk</h4>
                            <p className="text-sm text-red-700">{result.risk_assessment.security_risk}</p>
                          </div>
                        )}
                        
                        {result.risk_assessment.performance_risk !== 'No specific performance risks identified' && (
                          <div className="p-4 border rounded-lg border-orange-200 bg-orange-50">
                            <h4 className="font-semibold mb-2 text-orange-800">⚡ Performance Risk</h4>
                            <p className="text-sm text-orange-700">{result.risk_assessment.performance_risk}</p>
                          </div>
                        )}
                        
                        {result.risk_assessment.operational_risk !== 'No specific operational risks identified' && (
                          <div className="p-4 border rounded-lg border-blue-200 bg-blue-50">
                            <h4 className="font-semibold mb-2 text-blue-800">🔧 Operational Risk</h4>
                            <p className="text-sm text-blue-700">{result.risk_assessment.operational_risk}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Meta Analysis */}
                  {result.meta_analysis && (
                    <div>
                      <h3 className="text-xl font-semibold mb-3">🧠 Analysis Overview</h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="p-4 border rounded-lg">
                          <h4 className="font-semibold mb-2">Change Intent</h4>
                          <p className="text-sm text-gray-700">{result.meta_analysis.change_intent}</p>
                        </div>
                        <div className="p-4 border rounded-lg">
                          <h4 className="font-semibold mb-2">Risk Level</h4>
                          <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                            result.meta_analysis.risk_level === 'LOW' ? 'bg-green-100 text-green-800' :
                            result.meta_analysis.risk_level === 'MEDIUM' ? 'bg-yellow-100 text-yellow-800' :
                            result.meta_analysis.risk_level === 'HIGH' ? 'bg-orange-100 text-orange-800' :
                            'bg-red-100 text-red-800'
                          }`}>
                            {result.meta_analysis.risk_level}
                          </span>
                        </div>
                        <div className="p-4 border rounded-lg">
                          <h4 className="font-semibold mb-2">Complexity</h4>
                          <p className="text-sm text-gray-700">{result.meta_analysis.complexity_assessment}</p>
                        </div>
                        <div className="p-4 border rounded-lg">
                          <h4 className="font-semibold mb-2">Architectural Impact</h4>
                          <p className="text-sm text-gray-700">{result.meta_analysis.architectural_impact}</p>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Mentorship Notes */}
                  {result.mentorship_notes && (
                    <div>
                      <h3 className="text-xl font-semibold mb-3">👨‍🏫 Mentorship Insights</h3>
                      <div className="space-y-4">
                        {result.mentorship_notes.strength_recognition && (
                          <div className="p-4 border rounded-lg border-green-200 bg-green-50">
                            <h4 className="font-semibold mb-2 text-green-800">💪 Strengths Demonstrated</h4>
                            <p className="text-sm text-green-700">{result.mentorship_notes.strength_recognition}</p>
                          </div>
                        )}
                        
                        {result.mentorship_notes.growth_opportunities && (
                          <div className="p-4 border rounded-lg border-blue-200 bg-blue-50">
                            <h4 className="font-semibold mb-2 text-blue-800">🌱 Growth Opportunities</h4>
                            <p className="text-sm text-blue-700">{result.mentorship_notes.growth_opportunities}</p>
                          </div>
                        )}
                        
                        {result.mentorship_notes.suggested_focus && (
                          <div className="p-4 border rounded-lg border-purple-200 bg-purple-50">
                            <h4 className="font-semibold mb-2 text-purple-800">🎯 Suggested Focus Areas</h4>
                            <p className="text-sm text-purple-700">{result.mentorship_notes.suggested_focus}</p>
                          </div>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Executive Summary */}
                  {result.executive_summary && (
                    <div>
                      <h3 className="text-xl font-semibold mb-3">📊 Executive Summary</h3>
                      <div className="p-4 border rounded-lg bg-gradient-to-r from-blue-50 to-indigo-50">
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                          {result.executive_summary.split(' | ').map((item: string, index: number) => {
                            const [label, value] = item.split(': ');
                            const cleanLabel = label.replace(/\*\*/g, '').trim();
                            const cleanValue = value?.replace(/\*\*/g, '').trim() || '';
                            
                            // Add icons and colors based on the label
                            let icon = '📋';
                            let valueClass = 'text-gray-700';
                            
                            if (cleanLabel.includes('Risk Level')) {
                              icon = cleanValue === 'LOW' ? '🟢' : cleanValue === 'MEDIUM' ? '🟡' : cleanValue === 'HIGH' ? '🟠' : '🔴';
                              valueClass = cleanValue === 'LOW' ? 'text-green-700 font-semibold' : 
                                          cleanValue === 'MEDIUM' ? 'text-yellow-700 font-semibold' : 
                                          cleanValue === 'HIGH' ? 'text-orange-700 font-semibold' : 'text-red-700 font-semibold';
                            } else if (cleanLabel.includes('Deployment Status')) {
                              icon = cleanValue === 'READY' ? '✅' : cleanValue.includes('MINOR') ? '⚠️' : cleanValue.includes('MAJOR') ? '🟠' : '🔴';
                              valueClass = cleanValue === 'READY' ? 'text-green-700 font-semibold' : 
                                          cleanValue.includes('MINOR') ? 'text-yellow-700 font-semibold' : 
                                          cleanValue.includes('MAJOR') ? 'text-orange-700 font-semibold' : 'text-red-700 font-semibold';
                            } else if (cleanLabel.includes('Quality Score')) {
                              const score = parseFloat(cleanValue);
                              icon = score >= 8 ? '🟢' : score >= 6 ? '🟡' : score >= 4 ? '🟠' : '🔴';
                              valueClass = score >= 8 ? 'text-green-700 font-semibold' : 
                                          score >= 6 ? 'text-yellow-700 font-semibold' : 
                                          score >= 4 ? 'text-orange-700 font-semibold' : 'text-red-700 font-semibold';
                            } else if (cleanLabel.includes('Issues Found')) {
                              icon = '🔍';
                              valueClass = 'text-orange-700 font-semibold';
                            } else if (cleanLabel.includes('Immediate Actions')) {
                              icon = '🚨';
                              valueClass = 'text-red-700 font-semibold';
                            } else if (cleanLabel.includes('Change Intent')) {
                              icon = '🎯';
                            }
                            
                            return (
                              <div key={index} className="p-3 bg-white rounded-lg border shadow-sm">
                                <div className="flex items-center gap-2 mb-1">
                                  <span className="text-lg">{icon}</span>
                                  <span className="font-semibold text-gray-800 text-sm">{cleanLabel}</span>
                                </div>
                                <div className={`text-sm ${valueClass} ml-7`}>
                                  {cleanValue}
                                </div>
                              </div>
                            );
                          })}
                        </div>
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
