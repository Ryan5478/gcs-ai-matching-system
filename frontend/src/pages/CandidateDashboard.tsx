import { useState, useRef, useEffect, useCallback } from "react";
import toast from "react-hot-toast";
import {
  Upload, Sparkles, Loader2, Copy, Check, FileText, Brain, ShieldCheck,
  RefreshCw, Mail, X,
} from "lucide-react";
import api from "../api/client";
import JobDiscovery from "../components/JobDiscovery";
/* ---------------- Small components ---------------- */

function ScoreRing({ score, size = 56 }: { score: number; size?: number }) {
  const pct = Math.round(score * 100);
  const angle = (score * 360).toFixed(1);
  const color = pct >= 70 ? "#22d3ee" : pct >= 50 ? "#a855f7" : "#6366f1";
  return (
    <div className="relative shrink-0" style={{ width: size, height: size }}>
      <div
        className="h-full w-full rounded-full"
        style={{
          background: `conic-gradient(${color} ${angle}deg, rgba(255,255,255,0.05) ${angle}deg)`,
          boxShadow: `0 0 16px ${color}55`,
        }}
      />
      <div className="absolute inset-[3px] rounded-full bg-void-800 flex items-center justify-center">
        <span className="text-sm font-bold text-white">{pct}%</span>
      </div>
    </div>
  );
}

function BigScoreDial({ score }: { score: number }) {
  const pct = Math.max(0, Math.min(100, score));
  const angle = (pct / 100) * 360;
  const color = pct >= 75 ? "#22d3ee" : pct >= 55 ? "#a855f7" : "#f59e0b";
  return (
    <div className="relative h-32 w-32">
      <div
        className="h-full w-full rounded-full"
        style={{
          background: `conic-gradient(${color} ${angle}deg, rgba(255,255,255,0.05) ${angle}deg)`,
          boxShadow: `0 0 32px ${color}66`,
        }}
      />
      <div className="absolute inset-[6px] rounded-full bg-void-800 flex flex-col items-center justify-center">
        <span className="text-4xl font-black text-white">{pct}</span>
        <span className="text-[10px] uppercase tracking-widest text-slate-500">ATS</span>
      </div>
    </div>
  );
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      onClick={() => {
        navigator.clipboard.writeText(text);
        setCopied(true);
        toast.success("Copied to clipboard");
        setTimeout(() => setCopied(false), 1500);
      }}
      className="inline-flex items-center gap-1 text-xs text-slate-400 hover:text-neon-cyan transition"
    >
      {copied ? <Check size={12} /> : <Copy size={12} />}
      {copied ? "Copied" : "Copy"}
    </button>
  );
}

function SkillChips({ skills }: { skills: string[] }) {
  if (!skills || skills.length === 0) {
    return <p className="text-xs text-slate-500 italic">No skills detected.</p>;
  }
  return (
    <div className="flex flex-wrap gap-1.5">
      {skills.map((s) => (
        <span key={s} className="chip">{s}</span>
      ))}
    </div>
  );
}

function ResumeAdvice({ advice }: { advice: any }) {
  if (!advice) return null;
  if (typeof advice === "string") {
    return <p className="text-sm text-slate-300 whitespace-pre-wrap">{advice}</p>;
  }
  return (
    <div className="space-y-4 text-sm">
      {advice.experience_level && (
        <div>
          <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-1.5">Experience</p>
          <span className="chip">{advice.experience_level}</span>
        </div>
      )}
      {advice.profile_summary && (
        <div>
          <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-1.5">Summary</p>
          <p className="text-slate-300 leading-relaxed">{advice.profile_summary}</p>
        </div>
      )}
      {advice.best_fit_roles?.length > 0 && (
        <div>
          <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-1.5">Best fit roles</p>
          <ul className="space-y-1">
            {advice.best_fit_roles.map((r: string, i: number) => (
              <li key={i} className="flex items-start gap-2 text-slate-300">
                <span className="text-neon-cyan shrink-0 mt-0.5">▸</span>
                {r}
              </li>
            ))}
          </ul>
        </div>
      )}
      {advice.improvement_tips?.length > 0 && (
        <div>
          <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-1.5">Tips</p>
          <ul className="space-y-1">
            {advice.improvement_tips.map((t: string, i: number) => (
              <li key={i} className="flex items-start gap-2 text-slate-300">
                <span className="text-neon-purple shrink-0 mt-0.5">→</span>
                {t}
              </li>
            ))}
          </ul>
        </div>
      )}
      {advice.missing_skills?.length > 0 && (
        <div>
          <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-1.5">Consider adding</p>
          <div className="flex flex-wrap gap-1.5">
            {advice.missing_skills.map((s: string, i: number) => (
              <span key={i} className="text-xs bg-amber-500/10 text-amber-300 border border-amber-500/30 rounded-full px-2.5 py-1">
                {s}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/* ---------------- ATS Analysis Card ---------------- */

function AtsCard({ resumeText }: { resumeText: string }) {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<any>(null);

  async function run() {
    setLoading(true);
    try {
      const { data } = await api.post("/ai/resume-strength", { resume_text: resumeText });
      setData(data);
      toast.success(`ATS score: ${data.overall_score}/100`);
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? "ATS analysis failed");
    } finally {
      setLoading(false);
    }
  }

  const sectionLabels: Record<string, string> = {
    impact: "Impact",
    clarity: "Clarity",
    keywords: "Keywords",
    formatting: "Formatting",
    achievements: "Achievements",
  };

  return (
    <div className="rounded-2xl glass p-5">
      <div className="flex items-center justify-between mb-3">
        <h3 className="font-semibold text-white text-sm flex items-center gap-2">
          <ShieldCheck size={14} className="text-neon-cyan" />
          ATS Resume Analysis
        </h3>
        <button
          onClick={run}
          disabled={loading || !resumeText}
          className="btn-primary !py-1.5 !px-3 !text-xs"
        >
          {loading ? (
            <><Loader2 size={12} className="animate-spin" /> Analyzing…</>
          ) : data ? (
            <><RefreshCw size={12} /> Re-run</>
          ) : (
            <><Brain size={12} /> Analyze</>
          )}
        </button>
      </div>

      {!data && !loading && (
        <p className="text-xs text-slate-500">
          Get an ATS readiness score with subsection breakdown and specific fixes.
        </p>
      )}

      {loading && !data && (
        <div className="animate-pulse space-y-3">
          <div className="h-24 w-24 rounded-full bg-white/5 mx-auto" />
          <div className="h-3 w-3/4 bg-white/5 rounded mx-auto" />
          <div className="h-3 w-1/2 bg-white/5 rounded mx-auto" />
        </div>
      )}

      {data && (
        <div className="space-y-4 animate-fade-in-up">
          <div className="flex justify-center">
            <BigScoreDial score={data.overall_score} />
          </div>

          {Object.keys(data.sections ?? {}).length > 0 && (
            <div className="space-y-2">
              {Object.entries(data.sections).map(([k, v]: any) => (
                <div key={k}>
                  <div className="flex justify-between text-xs mb-1">
                    <span className="text-slate-400">{sectionLabels[k] ?? k}</span>
                    <span className="text-slate-300 font-medium">{v}</span>
                  </div>
                  <div className="h-1.5 rounded-full bg-white/5 overflow-hidden">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-neon-indigo to-neon-purple transition-all duration-1000"
                      style={{ width: `${v}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          )}

          {data.issues?.length > 0 && (
            <div>
              <p className="text-[10px] uppercase tracking-wider text-rose-400 mb-2">Issues</p>
              <ul className="space-y-1.5">
                {data.issues.map((s: string, i: number) => (
                  <li key={i} className="flex items-start gap-2 text-xs text-slate-300">
                    <span className="text-rose-400 shrink-0 mt-0.5">✕</span>
                    {s}
                  </li>
                ))}
              </ul>
            </div>
          )}

          {data.improvements?.length > 0 && (
            <div>
              <p className="text-[10px] uppercase tracking-wider text-emerald-400 mb-2">Improvements</p>
              <ul className="space-y-1.5">
                {data.improvements.map((s: string, i: number) => (
                  <li key={i} className="flex items-start gap-2 text-xs text-slate-300">
                    <span className="text-emerald-400 shrink-0 mt-0.5">→</span>
                    {s}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/* ---------------- Cover Letter Modal ---------------- */

function CoverLetterModal({
  job, resumeText, onClose,
}: {
  job: any; resumeText: string; onClose: () => void;
}) {
  const [loading, setLoading] = useState(true);
  const [body, setBody] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const title = job.title ?? job.job_title ?? "Role";
  const company = job.company ?? job.employer ?? "";

  const generate = useCallback(async () => {
    const description = job.description ?? job.job_description ?? job.summary ?? "";
    if (!description) {
      setError("This job has no description to base a letter on.");
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const { data } = await api.post("/ai/cover-letter", {
        job_title: title,
        company,
        job_description: description,
        resume_text: resumeText,
      });
      setBody(data.body);
    } catch (err: any) {
      setError(err?.response?.data?.detail ?? "Failed to generate cover letter");
    } finally {
      setLoading(false);
    }
  }, [job, resumeText, title, company]);

  useEffect(() => { generate(); }, [generate]);

  // ESC to close
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  function copy() {
    navigator.clipboard.writeText(body);
    setCopied(true);
    toast.success("Cover letter copied");
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/70 backdrop-blur-sm animate-fade-in-up"
      onClick={onClose}
    >
      <div
        className="relative w-full max-w-3xl max-h-[85vh] flex flex-col rounded-2xl glass-strong glow-border animate-fade-in-up"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-start justify-between gap-4 p-6 border-b border-white/10">
          <div className="min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <Mail size={16} className="text-neon-cyan shrink-0" />
              <span className="text-[10px] uppercase tracking-wider text-slate-400">
                AI Cover Letter
              </span>
            </div>
            <h2 className="text-xl font-bold text-white truncate">{title}</h2>
            {company && <p className="text-sm text-slate-400">{company}</p>}
          </div>
          <button
            onClick={onClose}
            className="shrink-0 rounded-lg p-2 text-slate-400 hover:text-white hover:bg-white/5 transition"
            title="Close (Esc)"
          >
            <X size={18} />
          </button>
        </div>

        {/* Body */}
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
                  <div className="h-3 bg-white/5 rounded w-[88%]" />
                </div>
              ))}
            </div>
          )}

          {error && (
            <div className="rounded-xl bg-rose-500/10 border border-rose-500/30 p-4 text-rose-200 text-sm">
              {error}
            </div>
          )}

          {!loading && !error && body && (
            <div className="space-y-4">
              <p className="text-xs text-slate-500 italic">
                Body text only — add your own greeting and signature before sending.
              </p>
              <div className="rounded-xl bg-white/[0.03] border border-white/10 p-5">
                {body.split(/\n{2,}/).map((para, i) => (
                  <p key={i} className="text-slate-200 leading-relaxed mb-4 last:mb-0 whitespace-pre-wrap">
                    {para}
                  </p>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between gap-3 p-6 border-t border-white/10">
          <button
            onClick={generate}
            disabled={loading}
            className="btn-ghost !py-2 !px-4 !text-sm"
          >
            <RefreshCw size={14} className={loading ? "animate-spin" : ""} />
            Regenerate
          </button>
          <button
            onClick={copy}
            disabled={loading || !body}
            className="btn-primary !py-2 !px-4 !text-sm"
          >
            {copied ? <Check size={14} /> : <Copy size={14} />}
            {copied ? "Copied" : "Copy cover letter"}
          </button>
        </div>
      </div>
    </div>
  );
}

/* ---------------- Per-job card ---------------- */

function JobCard({
  job, index, resumeText, onCoverLetter,
}: {
  job: any; index: number; resumeText: string;
  onCoverLetter: (job: any) => void;
}) {
  const score = job.score ?? job.match_score ?? 0;
  const [aiScore, setAiScore] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  async function deepScore() {
    const description = job.description ?? job.job_description ?? job.summary ?? "";
    if (!description) {
      toast.error("This job has no description to analyze");
      return;
    }
    setLoading(true);
    try {
      const { data } = await api.post("/ai/match", {
        job_title: job.title ?? job.job_title ?? "Role",
        job_description: description,
        resume_text: resumeText,
      });
      setAiScore(data);
      toast.success(`AI fit: ${data.fit_score}/100`);
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? "AI scoring failed");
    } finally {
      setLoading(false);
    }
  }

  const jobText = `${job.title ?? job.job_title} at ${job.company ?? ""}`;
  const verdictColor =
    aiScore?.verdict === "strong_match"
      ? "text-emerald-300 bg-emerald-500/10 border-emerald-500/30"
      : aiScore?.verdict === "moderate_match"
      ? "text-amber-300 bg-amber-500/10 border-amber-500/30"
      : "text-slate-300 bg-white/5 border-white/10";

  return (
    <div
      className="group rounded-2xl glass p-5 hover:border-neon-indigo/40 transition-all duration-300 animate-fade-in-up"
      style={{ animationDelay: `${index * 0.04}s` }}
    >
      <div className="flex gap-4">
        <ScoreRing score={score} />
        <div className="min-w-0 flex-1">
          <div className="flex items-start justify-between gap-2">
            <div className="min-w-0">
              <h3 className="font-semibold text-white truncate">
                {job.title ?? job.job_title ?? "Role"}
              </h3>
              <p className="text-sm text-slate-400 mt-0.5">
                {job.company ?? ""}
                {job.location ? ` · ${job.location}` : ""}
              </p>
            </div>
            <CopyButton text={jobText} />
          </div>

          {job.advice && (
            <p className="mt-3 text-sm text-slate-300 leading-relaxed bg-white/[0.03] rounded-lg p-3 border-l-2 border-neon-indigo/50">
              {typeof job.advice === "string"
                ? job.advice
                : job.advice.summary ?? job.advice.message ?? ""}
            </p>
          )}

          <div className="mt-3 flex flex-wrap gap-2">
            {!aiScore && (
              <button
                onClick={deepScore}
                disabled={loading}
                className="inline-flex items-center gap-1.5 text-xs text-neon-cyan hover:text-white border border-neon-cyan/30 hover:border-neon-cyan/60 rounded-full px-3 py-1.5 transition"
              >
                {loading ? (
                  <><Loader2 size={11} className="animate-spin" /> Scoring…</>
                ) : (
                  <><Brain size={11} /> AI Deep Score</>
                )}
              </button>
            )}
            <button
              onClick={() => onCoverLetter(job)}
              disabled={!resumeText}
              className="inline-flex items-center gap-1.5 text-xs text-neon-purple hover:text-white border border-neon-purple/30 hover:border-neon-purple/60 rounded-full px-3 py-1.5 transition disabled:opacity-40"
            >
              <Mail size={11} /> Cover Letter
            </button>
          </div>

          {aiScore && (
            <div className="mt-3 rounded-xl bg-white/[0.03] border border-white/10 p-4 animate-fade-in-up">
              <div className="flex items-center justify-between gap-3 mb-3">
                <div className="flex items-baseline gap-2">
                  <span className="text-2xl font-black neon-text">{aiScore.fit_score}</span>
                  <span className="text-xs text-slate-500">/100</span>
                  <span className={`text-[10px] uppercase tracking-wider rounded-full px-2 py-0.5 border ${verdictColor}`}>
                    {aiScore.verdict.replace("_", " ")}
                  </span>
                </div>
                <CopyButton text={JSON.stringify(aiScore, null, 2)} />
              </div>

              <p className="text-sm text-slate-300 leading-relaxed mb-3">
                {aiScore.reasoning}
              </p>

              <div className="grid grid-cols-2 gap-3">
                {aiScore.strengths?.length > 0 && (
                  <div>
                    <p className="text-[10px] uppercase tracking-wider text-emerald-400 mb-1.5">Strengths</p>
                    <ul className="space-y-1">
                      {aiScore.strengths.map((s: string, i: number) => (
                        <li key={i} className="text-xs text-slate-300 flex items-start gap-1.5">
                          <span className="text-emerald-400 shrink-0">+</span>{s}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
                {aiScore.gaps?.length > 0 && (
                  <div>
                    <p className="text-[10px] uppercase tracking-wider text-amber-400 mb-1.5">Gaps</p>
                    <ul className="space-y-1">
                      {aiScore.gaps.map((s: string, i: number) => (
                        <li key={i} className="text-xs text-slate-300 flex items-start gap-1.5">
                          <span className="text-amber-400 shrink-0">−</span>{s}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              {aiScore.recommendation && (
                <p className="mt-3 text-xs text-neon-cyan bg-neon-cyan/5 rounded-lg p-2.5 border-l-2 border-neon-cyan/50">
                  {aiScore.recommendation}
                </p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/* ---------------- Main dashboard ---------------- */

export default function CandidateDashboard() {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState("");
  const [result, setResult] = useState<any>(null);
  const [resumeText, setResumeText] = useState("");
  const [dragOver, setDragOver] = useState(false);
  const [coverLetterJob, setCoverLetterJob] = useState<any>(null);

  const [leftWidth, setLeftWidth] = useState(58);
  const containerRef = useRef<HTMLDivElement>(null);
  const dragging = useRef(false);

  const startDrag = useCallback(() => {
    dragging.current = true;
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
  }, []);

  useEffect(() => {
    function onMove(e: MouseEvent) {
      if (!dragging.current || !containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const pct = ((e.clientX - rect.left) / rect.width) * 100;
      setLeftWidth(Math.min(75, Math.max(30, pct)));
    }
    function onUp() {
      dragging.current = false;
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    }
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mouseup", onUp);
    return () => {
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mouseup", onUp);
    };
  }, []);

  const doUpload = useCallback(async (f: File) => {
    setLoading(true);
    setResult(null);
    setProgress("Extracting resume text…");

    try {
      await new Promise((r) => setTimeout(r, 300));
      setProgress("Extracting skills…");
      const form = new FormData();
      form.append("resume", f);
      const { data } = await api.post("/match-resume", form);

      setProgress("Ranking jobs…");
      await new Promise((r) => setTimeout(r, 250));

      setResult(data);
      setProgress("");
      toast.success(`Found ${data.recommendations?.length ?? 0} matches`);
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? "Upload failed. Is the backend running?");
      setProgress("");
    } finally {
      setLoading(false);
    }
  }, []);

  function onFileSelected(f: File | null) {
    if (!f) return;
    setFile(f);
    doUpload(f);
    const reader = new FileReader();
    reader.onload = (e) => setResumeText(String(e.target?.result ?? ""));
    if (f.type === "text/plain" || f.name.endsWith(".txt")) {
      reader.readAsText(f);
    }
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault();
    setDragOver(false);
    const f = e.dataTransfer.files?.[0];
    if (f) onFileSelected(f);
  }

  const skills: string[] = result?.extracted_skills ?? result?.skills ?? [];
  const advice = result?.resume_advice;
  const recommendations = result?.recommendations ?? [];
  const extractedResume = result?.resume_text ?? resumeText;

  return (
    <div className="max-w-7xl mx-auto px-6 py-10">
      <div className="animate-fade-in-up">
        <span className="chip">
          <Sparkles size={11} />
          AI matching engine online
        </span>
        <h1 className="mt-4 text-4xl font-black tracking-tight text-white">
          Your <span className="neon-text">AI copilot</span> for job discovery
        </h1>
        <p className="mt-3 text-slate-400 max-w-2xl">
          Drop your resume below. We'll parse it, extract your skills, rank thousands
          of roles, run an ATS readiness check, and draft cover letters — all automatically.
        </p>
      </div>

      {/* Upload zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        className={`mt-8 relative rounded-2xl border-2 border-dashed transition-all duration-300 p-10 text-center ${
          dragOver
            ? "border-neon-cyan bg-neon-cyan/5 scale-[1.01]"
            : loading
            ? "border-neon-purple/50 bg-neon-purple/5"
            : "border-white/15 hover:border-neon-indigo/50 bg-white/[0.02]"
        }`}
      >
        <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-neon-indigo/0 via-neon-purple/5 to-neon-cyan/0 pointer-events-none" />

        {loading ? (
          <div className="relative">
            <div className="relative inline-flex h-16 w-16 items-center justify-center mb-4">
              <div className="absolute inset-0 rounded-full bg-gradient-to-br from-neon-indigo to-neon-purple opacity-40 blur-xl animate-pulse" />
              <Loader2 size={40} className="relative text-neon-cyan animate-spin" />
            </div>
            <p className="text-white font-medium">{progress || "Working…"}</p>
          </div>
        ) : (
          <div className="relative">
            <div className="inline-flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-neon-indigo/20 to-neon-purple/20 border border-white/10 mb-4">
              <Upload size={24} className="text-neon-cyan" />
            </div>
            <p className="text-white font-semibold text-lg">
              Drag & drop, or{" "}
              <label className="text-neon-cyan hover:text-neon-cyan/80 cursor-pointer underline decoration-dotted underline-offset-4">
                browse
                <input
                  type="file"
                  accept=".pdf,.docx,.doc,.txt"
                  className="hidden"
                  onChange={(e) => onFileSelected(e.target.files?.[0] ?? null)}
                />
              </label>
            </p>
            <p className="mt-2 text-xs text-slate-500">
              PDF · DOCX · DOC · TXT — analysis runs automatically
            </p>
            {file && (
              <div className="mt-4 inline-flex items-center gap-2 text-sm text-slate-400 bg-white/5 rounded-full px-3 py-1.5 border border-white/10">
                <FileText size={14} className="text-neon-cyan" />
                {file.name}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Results */}
      {result && (
        <div
          ref={containerRef}
          className="mt-8 flex gap-4 animate-fade-in-up"
          style={{ minHeight: 400 }}
        >
          <div style={{ width: `${leftWidth}%` }} className="space-y-4">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-white">
                Top matches{" "}
                <span className="text-sm font-normal text-slate-500">
                  ({recommendations.length})
                </span>
              </h2>
              <span className="text-xs text-slate-500 font-mono">
                ranked by semantic similarity
              </span>
            </div>

            <div className="space-y-3 max-h-[70vh] overflow-y-auto pr-1">
              {recommendations.map((job: any, i: number) => (
                <JobCard
                  key={i}
                  job={job}
                  index={i}
                  resumeText={extractedResume}
                  onCoverLetter={setCoverLetterJob}
                />
              ))}
            </div>
          </div>

          <div
            onMouseDown={startDrag}
            className="w-1.5 cursor-col-resize rounded-full bg-white/5 hover:bg-neon-indigo/50 transition-colors flex-shrink-0 group"
            title="Drag to resize"
          >
            <div className="h-full w-full flex items-center justify-center">
              <div className="h-12 w-0.5 rounded-full bg-white/20 group-hover:bg-neon-cyan/80 transition" />
            </div>
          </div>

          <div style={{ width: `${100 - leftWidth}%` }} className="space-y-4">
            <h2 className="text-lg font-semibold text-white">Resume analysis</h2>

            <div className="space-y-4 max-h-[70vh] overflow-y-auto pr-1">
              <AtsCard resumeText={extractedResume} />

              <div className="rounded-2xl glass p-5">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-semibold text-white text-sm">Extracted skills</h3>
                  <CopyButton text={skills.join(", ")} />
                </div>
                <SkillChips skills={skills} />
              </div>

              {advice && (
                <div className="rounded-2xl glass p-5">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="font-semibold text-white text-sm">Resume advice</h3>
                    <CopyButton
                      text={typeof advice === "string" ? advice : JSON.stringify(advice, null, 2)}
                    />
                  </div>
                  <ResumeAdvice advice={advice} />
                </div>
              )}

              {result.advice_summary && (
                <div className="rounded-2xl glass p-5 border-l-2 border-neon-cyan/50">
                  <h3 className="font-semibold text-white text-sm mb-2">Summary</h3>
                  <p className="text-sm text-slate-300 leading-relaxed">
                    {typeof result.advice_summary === "string"
                      ? result.advice_summary
                      : result.advice_summary.summary ?? ""}
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Cover letter modal */}
      {coverLetterJob && (
        <CoverLetterModal
          job={coverLetterJob}
          resumeText={extractedResume}
          onClose={() => setCoverLetterJob(null)}
        />
      )}
            {/* Job discovery */}
      <JobDiscovery resumeText={extractedResume} />
    </div>
  );
}
