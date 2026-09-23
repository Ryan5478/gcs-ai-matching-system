import { Link } from "react-router-dom";
import { ArrowRight, Shield, Sparkles, Target, Zap, Brain, FileText, BarChart3 } from "lucide-react";

export default function Landing() {
  return (
    <div className="relative">
      {/* Hero */}
      <section className="max-w-7xl mx-auto px-6 pt-24 pb-32">
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          <div className="animate-fade-in-up">
            <span className="chip animate-glow-pulse">
              <Sparkles size={12} />
              Powered by transformer embeddings
            </span>

            <h1 className="mt-8 text-6xl lg:text-7xl font-black tracking-tight leading-[1.05]">
              <span className="text-white">Match talent </span>
              <br />
              <span className="neon-text">at the speed of AI</span>
            </h1>

            <p className="mt-8 text-lg text-slate-400 max-w-xl leading-relaxed">
              Semantic resume parsing, FAISS-powered retrieval, and explainable
              rankings. Every recommendation comes with reasoning you can
              defend to a hiring committee.
            </p>

            <div className="mt-10 flex flex-wrap gap-3">
              <Link to="/register" className="btn-primary">
                <Zap size={18} /> Launch the demo
                <ArrowRight size={18} />
              </Link>
              <Link to="/login" className="btn-ghost">
                Sign in
              </Link>
            </div>

            <div className="mt-10 flex items-center gap-6 text-xs text-slate-500">
              <div className="flex items-center gap-2">
                <span className="relative flex h-2 w-2">
                  <span className="absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75 animate-pulse-ring" />
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-400" />
                </span>
                Live system
              </div>
              <div>•</div>
              <div>Fairness monitored</div>
              <div>•</div>
              <div>Explainable rankings</div>
            </div>
          </div>

          {/* Hero visual — mock panel */}
          <div className="relative animate-fade-in-up" style={{ animationDelay: "0.2s" }}>
            <div className="absolute inset-0 bg-gradient-to-br from-neon-indigo/30 via-neon-purple/20 to-neon-cyan/20 rounded-3xl blur-3xl" />
            <div className="relative glass-strong rounded-3xl p-6 glow-border">
              <div className="flex items-center gap-2 mb-4">
                <div className="h-3 w-3 rounded-full bg-pink-500/70" />
                <div className="h-3 w-3 rounded-full bg-amber-500/70" />
                <div className="h-3 w-3 rounded-full bg-emerald-500/70" />
                <div className="ml-3 text-xs text-slate-500 font-mono">
                  ai-match --live
                </div>
              </div>

              <div className="space-y-3">
                {[
                  { title: "Senior Backend Engineer", company: "Nexus Labs", score: 94 },
                  { title: "Platform Engineer", company: "Orbital AI", score: 87 },
                  { title: "Data Engineer", company: "Quantic", score: 79 },
                ].map((job, i) => (
                  <div
                    key={i}
                    className="rounded-xl bg-white/[0.03] border border-white/[0.08] p-4 hover:border-neon-indigo/40 transition group"
                    style={{ animationDelay: `${0.3 + i * 0.1}s` }}
                  >
                    <div className="flex justify-between items-start gap-3">
                      <div className="min-w-0">
                        <p className="font-medium text-white truncate">{job.title}</p>
                        <p className="text-xs text-slate-500 mt-0.5">{job.company}</p>
                      </div>
                      <div className="shrink-0 text-right">
                        <div className="text-lg font-bold neon-text">{job.score}%</div>
                        <div className="text-[10px] uppercase tracking-wider text-slate-500">match</div>
                      </div>
                    </div>
                    <div className="mt-3 h-1 rounded-full bg-white/5 overflow-hidden">
                      <div
                        className="h-full rounded-full bg-gradient-to-r from-neon-indigo to-neon-purple transition-all duration-1000"
                        style={{ width: `${job.score}%` }}
                      />
                    </div>
                  </div>
                ))}
              </div>

              <div className="mt-4 flex items-center gap-2 text-xs text-slate-500 font-mono">
                <Brain size={12} className="text-neon-cyan" />
                <span>15 jobs ranked · 0.84s</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Feature grid */}
      <section className="max-w-7xl mx-auto px-6 pb-32">
        <div className="grid md:grid-cols-3 gap-6">
          {[
            { icon: Target, title: "Semantic matching", desc: "FAISS + transformer embeddings rank by meaning, not keyword overlap.", color: "from-neon-indigo to-neon-purple" },
            { icon: Sparkles, title: "Explainable AI", desc: "Every match ships with a human-readable rationale and improvement tips.", color: "from-neon-purple to-neon-pink" },
            { icon: Shield, title: "Fair by design", desc: "Continuous demographic parity and equal opportunity monitoring.", color: "from-neon-cyan to-neon-teal" },
            { icon: FileText, title: "Multi-format intake", desc: "PDF, DOCX, DOC, or TXT — text extraction is automatic.", color: "from-neon-indigo to-neon-cyan" },
            { icon: Zap, title: "Real-time pipeline", desc: "Streaming progress with side-by-side analysis and results.", color: "from-neon-pink to-neon-purple" },
            { icon: BarChart3, title: "Ops dashboard", desc: "KPI tiles, fairness charts, and one-click index rebuilds.", color: "from-neon-teal to-neon-cyan" },
          ].map(({ icon: Icon, title, desc, color }, i) => (
            <div
              key={title}
              className="group relative rounded-2xl glass p-6 hover:border-white/20 transition-all duration-300 hover:-translate-y-1 animate-fade-in-up"
              style={{ animationDelay: `${i * 0.05}s` }}
            >
              <div className={`inline-flex h-11 w-11 rounded-xl bg-gradient-to-br ${color} p-[1.5px]`}>
                <div className="h-full w-full rounded-[10px] bg-void-800 flex items-center justify-center">
                  <Icon size={20} className="text-white" />
                </div>
              </div>
              <h3 className="mt-5 font-semibold text-white text-lg">{title}</h3>
              <p className="mt-2 text-sm text-slate-400 leading-relaxed">{desc}</p>
            </div>
          ))}
        </div>
      </section>

      <footer className="border-t border-white/[0.06] py-10 text-center text-sm text-slate-500">
        <p className="font-mono">
          © {new Date().getFullYear()} GCS AI Matching · built with FastAPI + React
        </p>
      </footer>
    </div>
  );
}
