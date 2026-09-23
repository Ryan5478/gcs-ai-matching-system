import { useState } from "react";
import toast from "react-hot-toast";
import {
  Search, Loader2, Sparkles, Users, Building2, Mail, Copy, Check, ShieldCheck,
} from "lucide-react";
import api from "../api/client";

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

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      onClick={() => {
        navigator.clipboard.writeText(text);
        setCopied(true);
        toast.success("Copied");
        setTimeout(() => setCopied(false), 1500);
      }}
      className="inline-flex items-center gap-1 text-xs text-slate-400 hover:text-neon-cyan transition"
    >
      {copied ? <Check size={12} /> : <Copy size={12} />}
      {copied ? "Copied" : "Copy"}
    </button>
  );
}

function Bullets({ items, marker = "▸", color = "text-neon-cyan" }: any) {
  if (!items?.length) return null;
  return (
    <ul className="space-y-1">
      {items.map((t: string, i: number) => (
        <li key={i} className="flex items-start gap-2 text-xs text-slate-300">
          <span className={`${color} shrink-0 mt-0.5`}>{marker}</span>
          <span>{t}</span>
        </li>
      ))}
    </ul>
  );
}

function renderReview(value: any) {
  if (!value) return null;
  if (typeof value === "string") {
    return <p className="text-sm text-slate-300 leading-relaxed">{value}</p>;
  }
  const stringKeys = Object.keys(value).filter((k) => typeof value[k] === "string" && value[k]);
  const arrayKeys = Object.keys(value).filter((k) => Array.isArray(value[k]) && value[k].length);
  return (
    <div className="space-y-3">
      {stringKeys.map((k) => (
        <div key={k}>
          <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-1">
            {k.replace(/_/g, " ")}
          </p>
          <p className="text-sm text-slate-300 leading-relaxed">{value[k]}</p>
        </div>
      ))}
      {arrayKeys.map((k) => (
        <div key={k}>
          <p className="text-[10px] uppercase tracking-wider text-slate-500 mb-1.5">
            {k.replace(/_/g, " ")}
          </p>
          <Bullets items={value[k]} />
        </div>
      ))}
    </div>
  );
}

export default function EmployerDashboard() {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  async function search(e: React.FormEvent) {
    e.preventDefault();
    if (!description.trim()) return;

    setLoading(true);
    setResult(null);
    try {
      const { data } = await api.post("/best-candidates", {
        job_title: title || "Untitled Role",
        job_description: description,
      });
      setResult(data);
      toast.success(`${data.candidates_count ?? 0} candidates ranked`);
    } catch (err: any) {
      toast.error(err?.response?.data?.detail ?? "Search failed");
    } finally {
      setLoading(false);
    }
  }

  const count = result?.candidates_count ?? result?.candidates?.length ?? 0;

  return (
    <div className="max-w-7xl mx-auto px-6 py-10">
      <div className="animate-fade-in-up">
        <span className="chip">
          <Users size={11} />
          Recruiter console
        </span>
        <h1 className="mt-4 text-4xl font-black tracking-tight text-white">
          Find your <span className="neon-text">next hire</span>
        </h1>
        <p className="mt-3 text-slate-400 max-w-2xl">
          Paste a job description. We'll rank every candidate in the pool by semantic fit
          and give you AI-generated hiring notes for each.
        </p>
      </div>

      {/* Search form */}
      <form onSubmit={search} className="mt-8 rounded-2xl glass-strong p-6 space-y-5 glow-border">
        <div>
          <label className="block text-xs uppercase tracking-wider text-slate-400 mb-2">
            Job title
          </label>
          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder="e.g. Senior Backend Engineer"
            className="input-dark"
          />
        </div>

        <div>
          <label className="block text-xs uppercase tracking-wider text-slate-400 mb-2">
            Job description <span className="text-rose-400">*</span>
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Paste responsibilities, required skills, experience level…"
            required
            rows={8}
            className="input-dark font-mono text-sm leading-relaxed"
          />
        </div>

        <div className="flex items-center justify-between gap-4 flex-wrap">
          <p className="text-xs text-slate-500">
            Uses FAISS shortlist + LLM reasoning for explainable ranking
          </p>
          <button
            type="submit"
            disabled={loading || !description.trim()}
            className="btn-primary"
          >
            {loading ? (
              <><Loader2 size={16} className="animate-spin" /> Searching…</>
            ) : (
              <><Search size={16} /> Search candidates</>
            )}
          </button>
        </div>
      </form>

      {/* Results */}
      {result && (
        <div className="mt-8 animate-fade-in-up">
          {/* Summary card */}
          <div className="rounded-2xl glass-strong p-6">
            <div className="flex items-start justify-between gap-4 flex-wrap">
              <div>
                <div className="flex items-center gap-2">
                  <Sparkles size={14} className="text-neon-cyan" />
                  <h2 className="text-xl font-semibold text-white">
                    {result.job_title ?? title ?? "Candidates"}
                  </h2>
                </div>
                <p className="text-sm text-slate-400 mt-1">
                  {count} candidate{count === 1 ? "" : "s"} ranked
                </p>
              </div>
            </div>

            {result.hiring_summary && (
              <div className="mt-5 rounded-xl bg-neon-cyan/5 border border-neon-cyan/20 border-l-4 border-l-neon-cyan p-4">
                <p className="text-[10px] uppercase tracking-wider text-neon-cyan mb-2">
                  Hiring summary
                </p>
                <div className="text-sm text-slate-200">
                  {renderReview(result.hiring_summary)}
                </div>
              </div>
            )}

            {result.advice_summary && (
              <div className="mt-4 text-sm text-slate-300">
                {renderReview(result.advice_summary)}
              </div>
            )}
          </div>

          {/* Candidate cards */}
          <div className="mt-6 space-y-4">
            {result.candidates?.map((c: any, i: number) => {
              const score = c.score ?? c.match_score ?? 0;
              return (
                <div
                  key={i}
                  className="rounded-2xl glass p-6 hover:border-neon-indigo/40 transition-all duration-300 animate-fade-in-up"
                  style={{ animationDelay: `${i * 0.04}s` }}
                >
                  <div className="flex gap-5">
                    <ScoreRing score={score} />

                    <div className="min-w-0 flex-1">
                      <div className="flex items-start justify-between gap-3 flex-wrap">
                        <div className="min-w-0">
                          <h3 className="font-semibold text-white text-lg truncate">
                            {c.full_name ?? c.name ?? `Candidate ${i + 1}`}
                          </h3>
                          <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-1 text-xs text-slate-400">
                            {c.email && (
                              <span className="inline-flex items-center gap-1">
                                <Mail size={11} /> {c.email}
                              </span>
                            )}
                            {c.phone && <span>{c.phone}</span>}
                            {c.location && (
                              <span className="inline-flex items-center gap-1">
                                <Building2 size={11} /> {c.location}
                              </span>
                            )}
                          </div>
                        </div>
                        <CopyButton
                          text={`${c.full_name ?? ""} — ${c.email ?? ""}`}
                        />
                      </div>

                      {c.summary && (
                        <p className="mt-3 text-sm text-slate-300 leading-relaxed">
                          {c.summary}
                        </p>
                      )}

                      {Array.isArray(c.skills) && c.skills.length > 0 && (
                        <div className="mt-3 flex flex-wrap gap-1.5">
                          {c.skills.slice(0, 14).map((s: string, k: number) => (
                            <span key={k} className="chip">{s}</span>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>

                  {c.employer_review && (
                    <div className="mt-5 rounded-xl bg-white/[0.03] border border-white/10 p-4">
                      <p className="text-[10px] uppercase tracking-wider text-slate-400 mb-3 flex items-center gap-2">
                        <ShieldCheck size={11} className="text-neon-purple" />
                        AI review
                      </p>
                      {renderReview(c.employer_review)}
                    </div>
                  )}

                  {c.advice && (
                    <div className="mt-3 rounded-xl bg-neon-indigo/5 border border-neon-indigo/20 border-l-4 border-l-neon-indigo p-4">
                      <p className="text-[10px] uppercase tracking-wider text-neon-indigo mb-2">
                        Match advice
                      </p>
                      <div className="text-sm text-slate-200">
                        {typeof c.advice === "string"
                          ? c.advice
                          : renderReview(c.advice)}
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {count === 0 && (
            <div className="mt-6 rounded-2xl glass p-10 text-center">
              <p className="text-slate-300 font-medium">No candidates matched yet.</p>
              <p className="text-xs text-slate-500 mt-2">
                Register candidates and upload resumes, or bulk import a CSV from the admin page.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
