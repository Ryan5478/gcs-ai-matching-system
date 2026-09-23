import { useState } from "react";
import toast from "react-hot-toast";
import {
  Search, Loader2, ExternalLink, Filter, Building2, Sparkles, Mail, Brain, Copy, Check,
} from "lucide-react";
import api from "../api/client";

type DiscoveredJob = {
  title: string;
  url: string;
  company: string;
  snippet: string;
  source: string;
};

function CoverLetterModal({
  job, resumeText, onClose,
}: {
  job: DiscoveredJob; resumeText: string; onClose: () => void;
}) {
  const [loading, setLoading] = useState(true);
  const [body, setBody] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  async function generate() {
    setLoading(true);
    setError(null);
    try {
      const { data } = await api.post("/ai/cover-letter", {
        job_title: job.title,
        company: job.company,
        job_description: job.snippet,
        resume_text: resumeText,
      });
      setBody(data.body);
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Failed to generate cover letter");
    } finally {
      setLoading(false);
    }
  }

  if (loading && !body && !error) generate();

  function copy() {
    navigator.clipboard.writeText(body);
    setCopied(true);
    toast.success("Cover letter copied");
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-3xl max-h-[85vh] flex flex-col rounded-2xl glass-strong glow-border"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between gap-4 p-6 border-b border-white/10">
          <div className="min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <Mail size={16} className="text-neon-cyan" />
              <span className="text-[10px] uppercase tracking-wider text-slate-400">
                AI Cover Letter
              </span>
            </div>
            <h2 className="text-xl font-bold text-white truncate">{job.title}</h2>
            {job.company && <p className="text-sm text-slate-400">{job.company}</p>}
          </div>
          <button onClick={onClose} className="shrink-0 text-slate-400 hover:text-white">✕</button>
        </div>

        <div className="flex-1 overflow-y-auto p-6">
          {loading && (
            <div className="space-y-4 animate-pulse">
              <div className="flex items-center gap-3 text-slate-400 text-sm">
                <Loader2 size={16} className="animate-spin text-neon-cyan" />
                Writing your cover letter…
              </div>
              {[1, 2, 3].map((i) => (
                <div key={i} className="space-y-2">
                  <div className="h-3 bg-white/5 rounded w-full" />
                  <div className="h-3 bg-white/5 rounded w-[92%]" />
                </div>
              ))}
            </div>
          )}

          {error && (
            <div className="rounded-xl bg-rose-500/10 border border-rose-500/30 p-4 text-rose-200 text-sm">
              {error}
            </div>
          )}

          {!loading && body && (
            <div className="rounded-xl bg-white/[0.03] border border-white/10 p-5">
              {body.split(/\n{2,}/).map((para, i) => (
                <p key={i} className="text-slate-200 leading-relaxed mb-4 last:mb-0 whitespace-pre-wrap">
                  {para}
                </p>
              ))}
            </div>
          )}
        </div>

        <div className="flex justify-end gap-3 p-6 border-t border-white/10">
          <button
            onClick={copy}
            disabled={loading || !body}
            className="btn-primary !py-2 !px-4 !text-sm"
          >
            {copied ? <Check size={14} /> : <Copy size={14} />}
            {copied ? "Copied" : "Copy"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function JobDiscovery({ resumeText }: { resumeText: string }) {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<any>(null);
  const [scores, setScores] = useState<Record<string, any>>({});
  const [scoring, setScoring] = useState<string | null>(null);
  const [coverJob, setCoverJob] = useState<DiscoveredJob | null>(null);

  async function search(e: React.FormEvent) {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setData(null);
    setScores({});
    try {
      const { data } = await api.post("/jobs/discover", {
        query: query.trim(),
        max_results: 20,
      });
      setData(data);
      toast.success(`${data.results.length} direct postings found`);
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? "Search failed");
    } finally {
      setLoading(false);
    }
  }

  async function deepScore(job: DiscoveredJob) {
    if (!resumeText) {
      toast.error("Upload a resume first to use AI scoring");
      return;
    }
    setScoring(job.url);
    try {
      const { data } = await api.post("/ai/match", {
        job_title: job.title,
        job_description: job.snippet,
        resume_text: resumeText,
      });
      setScores((prev) => ({ ...prev, [job.url]: data }));
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? "Scoring failed");
    } finally {
      setScoring(null);
    }
  }

  return (
    <div className="mt-12">
      <div className="flex items-center gap-3 mb-4">
        <div className="h-10 w-10 rounded-xl bg-gradient-to-br from-neon-cyan/20 to-neon-purple/20 border border-white/10 flex items-center justify-center">
          <Search size={18} className="text-neon-cyan" />
        </div>
        <div>
          <h2 className="text-xl font-semibold text-white">Discover fresh jobs</h2>
          <p className="text-xs text-slate-500">
            Live web search — job boards automatically filtered out
          </p>
        </div>
      </div>

      <form
        onSubmit={search}
        className="relative rounded-2xl glass p-3 flex flex-col md:flex-row gap-2"
      >
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="e.g. remote senior python backend engineer"
          className="input-dark flex-1 !py-3"
        />
        <button
          type="submit"
          disabled={loading || !query.trim()}
          className="btn-primary md:w-auto"
        >
          {loading ? (
            <><Loader2 size={16} className="animate-spin" /> Searching…</>
          ) : (
            <><Sparkles size={16} /> Search</>
          )}
        </button>
      </form>

      {data && (
        <div className="mt-4 flex flex-wrap items-center gap-3 text-xs">
          <span className="chip">
            <Sparkles size={11} />
            {data.results.length} results
          </span>
          <span className="text-slate-500">
            <Filter size={11} className="inline" /> {data.filtered_out} job boards filtered
          </span>
          <span className="text-slate-500">
            Searched: {data.total_searched}
          </span>
        </div>
      )}

      {data && data.results.length === 0 && (
        <div className="mt-6 rounded-2xl glass p-10 text-center">
          <p className="text-slate-300">No direct postings matched that query.</p>
          <p className="text-xs text-slate-500 mt-1">
            Try adding "remote", "senior", or a specific tech stack.
          </p>
        </div>
      )}

      <div className="mt-4 space-y-3">
        {data?.results.map((job: DiscoveredJob, i: number) => {
          const score = scores[job.url];
          return (
            <div
              key={i}
              className="rounded-2xl glass p-5 hover:border-neon-cyan/40 transition animate-fade-in-up"
              style={{ animationDelay: `${i * 0.03}s` }}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="min-w-0 flex-1">
                  <h3 className="font-semibold text-white">{job.title}</h3>
                  <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-1 text-xs text-slate-400">
                    {job.company && (
                      <span className="inline-flex items-center gap-1">
                        <Building2 size={11} /> {job.company}
                      </span>
                    )}
                    <span className="font-mono">{job.source}</span>
                  </div>
                  {job.snippet && (
                    <p className="mt-3 text-sm text-slate-300 leading-relaxed">
                      {job.snippet}
                    </p>
                  )}
                </div>
              </div>

              <div className="mt-4 flex flex-wrap items-center gap-2">
                <a
                  href={job.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1.5 text-xs text-slate-300 hover:text-white border border-white/10 hover:border-white/30 rounded-full px-3 py-1.5 transition"
                >
                  <ExternalLink size={11} /> Open job page
                </a>

                <button
                  onClick={() => deepScore(job)}
                  disabled={scoring === job.url || !resumeText}
                  className="inline-flex items-center gap-1.5 text-xs text-neon-cyan hover:text-white border border-neon-cyan/30 hover:border-neon-cyan/60 rounded-full px-3 py-1.5 transition disabled:opacity-40"
                >
                  {scoring === job.url ? (
                    <><Loader2 size={11} className="animate-spin" /> Scoring…</>
                  ) : (
                    <><Brain size={11} /> AI Deep Score</>
                  )}
                </button>

                <button
                  onClick={() => setCoverJob(job)}
                  disabled={!resumeText}
                  className="inline-flex items-center gap-1.5 text-xs text-neon-purple hover:text-white border border-neon-purple/30 hover:border-neon-purple/60 rounded-full px-3 py-1.5 transition disabled:opacity-40"
                >
                  <Mail size={11} /> Cover Letter
                </button>
              </div>

              {score && (
                <div className="mt-4 rounded-xl bg-white/[0.03] border border-white/10 p-4 animate-fade-in-up">
                  <div className="flex items-baseline gap-2 mb-2">
                    <span className="text-2xl font-black neon-text">{score.fit_score}</span>
                    <span className="text-xs text-slate-500">/100</span>
                    <span className={`text-[10px] uppercase tracking-wider rounded-full px-2 py-0.5 border ${
                      score.verdict === "strong_match"
                        ? "text-emerald-300 bg-emerald-500/10 border-emerald-500/30"
                        : score.verdict === "moderate_match"
                        ? "text-amber-300 bg-amber-500/10 border-amber-500/30"
                        : "text-slate-300 bg-white/5 border-white/10"
                    }`}>
                      {score.verdict.replace("_", " ")}
                    </span>
                  </div>
                  <p className="text-sm text-slate-300 leading-relaxed">{score.reasoning}</p>
                </div>
              )}
            </div>
          );
        })}
      </div>

      {coverJob && (
        <CoverLetterModal
          job={coverJob}
          resumeText={resumeText}
          onClose={() => setCoverJob(null)}
        />
      )}
    </div>
  );
}
