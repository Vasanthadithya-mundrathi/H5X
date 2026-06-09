import React, { useEffect, useMemo, useState, useRef } from "react";
import { createRoot } from "react-dom/client";
import {
  uploadTelemetry,
  generateScenario,
  startRun,
  getRunStatus,
  getRunResults
} from "./api";
import "./styles.css";

const formatNumber = new Intl.NumberFormat("en-US");

const NODE_POSITIONS = {
  "gateway": { x: 60, y: 110 },
  "catalog": { x: 190, y: 50 },
  "cart": { x: 190, y: 170 },
  "checkout": { x: 330, y: 110 },
  "inventory": { x: 470, y: 50 },
  "payment": { x: 470, y: 170 }
};

const NAV_ITEMS = [
  { id: "import", label: "Import Telemetry" },
  { id: "traffic", label: "Traffic Intelligence" },
  { id: "journeys", label: "Journey Explorer" },
  { id: "scenario-builder", label: "Scenario Builder" },
  { id: "execution", label: "Run Execution" },
  { id: "results", label: "Comparison & Results" },
  { id: "comparison", label: "Method Comparison" }
];

const SAMPLE_TELEMETRY_FILES = {
  gatewayLogs: [
    { path: "/sample-telemetry/hex-ai-gateway.har", name: "hex-ai-gateway.har", type: "application/json" }
  ],
  traces: [
    { path: "/sample-telemetry/hex-ai-traces.json", name: "hex-ai-traces.json", type: "application/json" }
  ],
  podMetrics: [
    { path: "/sample-telemetry/hex-ai-pods.csv", name: "hex-ai-pods.csv", type: "text/csv" }
  ],
  applicationLogs: [
    { path: "/sample-telemetry/hex-ai-app.json", name: "hex-ai-app.json", type: "application/json" }
  ]
};

const SAMPLE_TELEMETRY_ZIP_FILES = {
  gatewayLogs: [
    { path: "/sample-telemetry/hex-ai-gateway.zip", name: "hex-ai-gateway.zip", type: "application/zip" }
  ],
  traces: [
    { path: "/sample-telemetry/hex-ai-traces.zip", name: "hex-ai-traces.zip", type: "application/zip" }
  ],
  podMetrics: [
    { path: "/sample-telemetry/hex-ai-pods.zip", name: "hex-ai-pods.zip", type: "application/zip" }
  ],
  applicationLogs: [
    { path: "/sample-telemetry/hex-ai-app.zip", name: "hex-ai-app.zip", type: "application/zip" }
  ]
};

async function fetchSampleTelemetryFiles(manifest = SAMPLE_TELEMETRY_FILES) {
  const entries = await Promise.all(
    Object.entries(manifest).map(async ([key, specs]) => {
      const files = await Promise.all(
        specs.map(async (spec) => {
          const response = await fetch(spec.path);
          if (!response.ok) {
            throw new Error(`Could not load ${spec.name}`);
          }
          const blob = await response.blob();
          return new File([blob], spec.name, { type: spec.type });
        })
      );
      return [key, files];
    })
  );
  return Object.fromEntries(entries);
}

function HexAiLogo({ size = 32 }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" fill="none" xmlns="http://www.w3.org/2000/svg">
      <polygon points="16,2 29,9.5 29,24.5 16,30 3,24.5 3,9.5" stroke="url(#logo-grad-1)" strokeWidth="2.5" strokeLinejoin="round" fill="rgba(99, 102, 241, 0.05)" />
      <polygon points="16,7 25,12 25,22 16,27 7,22 7,12" stroke="url(#logo-grad-2)" strokeWidth="1.5" strokeLinejoin="round" fill="none" />
      <path d="M12,11 V21 M20,11 V21 M12,16 H20" stroke="url(#logo-grad-1)" strokeWidth="2.5" strokeLinecap="round" />
      <defs>
        <linearGradient id="logo-grad-1" x1="3" y1="2" x2="29" y2="30" gradientUnits="userSpaceOnUse">
          <stop stopColor="#6366f1" />
          <stop offset="1" stopColor="#a855f7" />
        </linearGradient>
        <linearGradient id="logo-grad-2" x1="25" y1="12" x2="7" y2="27" gradientUnits="userSpaceOnUse">
          <stop stopColor="#a855f7" />
          <stop offset="1" stopColor="#6366f1" />
        </linearGradient>
      </defs>
    </svg>
  );
}

function NodeIcon({ id }) {
  if (id === "gateway") {
    return <path d="M-8,-2 C-8,-7 -4,-9 0,-9 C3,-9 6,-7 7,-4 C9,-4 10,-2 10,0 C10,3 8,5 5,5 H-5 C-7,5 -8,3 -8,-2 Z" stroke="currentColor" strokeWidth="1.5" fill="none" transform="translate(0, -3)" />;
  }
  if (id === "catalog") {
    return (
      <g transform="translate(0, -3)">
        <rect x="-8" y="-7" width="16" height="14" rx="1.5" stroke="currentColor" strokeWidth="1.5" fill="none" />
        <line x1="-4" y1="-2" x2="4" y2="-2" stroke="currentColor" strokeWidth="1.5" />
        <line x1="-4" y1="2" x2="1" y2="2" stroke="currentColor" strokeWidth="1.5" />
      </g>
    );
  }
  if (id === "cart") {
    return <path d="M-9,-8 H-6 L-3,2 H6 L9,-5 H-4.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" fill="none" transform="translate(0, -1)" />;
  }
  if (id === "checkout") {
    return (
      <g transform="translate(0, -3)">
        <rect x="-8" y="-7" width="16" height="14" rx="1.5" stroke="currentColor" strokeWidth="1.5" fill="none" />
        <path d="M-4,1 L-1,4 L4,-2" stroke="#10b981" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" fill="none" />
      </g>
    );
  }
  if (id === "inventory") {
    return (
      <g transform="translate(0, -3)">
        <rect x="-8" y="-8" width="16" height="5" rx="1" stroke="currentColor" strokeWidth="1.5" fill="none" />
        <rect x="-8" y="-1" width="16" height="5" rx="1" stroke="currentColor" strokeWidth="1.5" fill="none" />
        <circle cx="-4" cy="-5.5" r="0.75" fill="#10b981" />
        <circle cx="-4" cy="1.5" r="0.75" fill="#10b981" />
      </g>
    );
  }
  if (id === "payment") {
    return (
      <g transform="translate(0, -3)">
        <rect x="-9" y="-6" width="18" height="12" rx="1.5" stroke="currentColor" strokeWidth="1.5" fill="none" />
        <line x1="-9" y1="-1" x2="9" y2="-1" stroke="currentColor" strokeWidth="1.5" />
        <rect x="-5" y="2" width="3" height="2" rx="0.5" fill="currentColor" />
      </g>
    );
  }
  return null;
}

function TelemetryPipeline() {
  return (
    <article className="panel pipeline-card glass">
      <PanelHeading title="Telemetry Twin Architectural Pipeline" subtitle="Visual data intake processing: distributed observations flow into privacy-shielded state matrices." />
      <div className="pipeline-svg-wrap">
        <svg className="pipeline-svg" viewBox="0 0 760 180" xmlns="http://www.w3.org/2000/svg">
          <path d="M 120,40 H 260 C 290,40 290,90 320,90 H 370" className="pipeline-flow-path active" />
          <path d="M 120,90 H 370" className="pipeline-flow-path active-strong" />
          <path d="M 120,140 H 260 C 290,140 290,90 320,90 H 370" className="pipeline-flow-path active" />
          <path d="M 450,90 H 580" className="pipeline-flow-path active-strong" />

          <g className="pipeline-svg-node source" transform="translate(10, 20)">
            <rect width="110" height="40" rx="6" />
            <text x="55" y="24" textAnchor="middle" className="title">Gateway Logs</text>
            <text x="55" y="34" textAnchor="middle" className="sub">HTTP access CSV</text>
          </g>

          <g className="pipeline-svg-node source" transform="translate(10, 70)">
            <rect width="110" height="40" rx="6" />
            <text x="55" y="24" textAnchor="middle" className="title">OTel Traces</text>
            <text x="55" y="34" textAnchor="middle" className="sub">Distributed JSON</text>
          </g>

          <g className="pipeline-svg-node source" transform="translate(10, 120)">
            <rect width="110" height="40" rx="6" />
            <text x="55" y="24" textAnchor="middle" className="title">Pod Metrics</text>
            <text x="55" y="34" textAnchor="middle" className="sub">CPU / Memory CSV</text>
          </g>

          <g className="pipeline-svg-node processor" transform="translate(410, 90)">
            <circle r="40" />
            <text x="0" y="-8" textAnchor="middle" className="title" style={{ fill: "#a855f7" }}>TWIN CORE</text>
            <text x="0" y="8" textAnchor="middle" className="sub">Markov Matrices</text>
            <text x="0" y="20" textAnchor="middle" className="sub">Privacy Filter</text>
          </g>

          <g className="pipeline-svg-node target" transform="translate(600, 70)">
            <rect width="140" height="40" rx="6" />
            <text x="70" y="24" textAnchor="middle" className="title">k6 Script Twin</text>
            <text x="70" y="34" textAnchor="middle" className="sub">Stateful Load Scenario</text>
          </g>
        </svg>
      </div>
    </article>
  );
}

function App() {
  const [analysis, setAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState("import");

  // Scenario Builder Config State
  const [testMode, setTestMode] = useState("mirror");
  const [targetUrl, setTargetUrl] = useState("http://localhost:8080");
  const [duration, setDuration] = useState("5m");
  const [rateLimit, setRateLimit] = useState("24");
  const [customScript, setCustomScript] = useState("");
  const [generatingScript, setGeneratingScript] = useState(false);

  // Execution Runner State
  const [runId, setRunId] = useState("");
  const [executionState, setExecutionState] = useState("idle"); // idle, running, completed, blocked
  const [runProgress, setRunProgress] = useState(0);
  const [liveMetrics, setLiveMetrics] = useState([]);
  const [terminalLogs, setTerminalLogs] = useState([]);
  const [runResults, setRunResults] = useState(null);
  const [runMetadata, setRunMetadata] = useState(null);
  const [uploadQualityIssue, setUploadQualityIssue] = useState(null);

  const terminalEndRef = useRef(null);

  // Scroll logs terminal automatically
  useEffect(() => {
    if (terminalEndRef.current) {
      terminalEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [terminalLogs]);

  // Handle file uploads
  async function handleUpload(files) {
    setLoading(true);
    setError("");
    try {
      const nextAnalysis = await uploadTelemetry(files);
      setAnalysis(nextAnalysis);
      setUploadQualityIssue(null);
      setCustomScript(nextAnalysis.k6Script);
      const purchase = nextAnalysis.journeys.find(j => j.name.toLowerCase().includes("purchase"));
      if (purchase) {
        setRateLimit(Math.max(5, Math.round(purchase.loadRate * 2)).toString());
      }
      if (nextAnalysis.autonomousAgent?.recommendedScenario) {
        setTestMode(nextAnalysis.autonomousAgent.recommendedScenario);
      }
      setActiveTab("traffic");
    } catch (err) {
      setError(err.message);
      setUploadQualityIssue(err.dataQuality ?? null);
    } finally {
      setLoading(false);
    }
  }

  // Handle generating custom scripts
  async function handleGenerateScript(e) {
    e.preventDefault();
    if (!analysis) return;
    setGeneratingScript(true);
    try {
      const res = await generateScenario(analysis.datasetName, testMode, targetUrl, duration, rateLimit);
      setCustomScript(res.k6Script);
    } catch (err) {
      setError(err.message);
    } finally {
      setGeneratingScript(false);
    }
  }

  // Handle starting a real k6 run or a blocked dry-run artifact generation
  async function handleStartExecution() {
    if (!analysis) return;
    setExecutionState("running");
    setRunProgress(0);
    setLiveMetrics([]);
    setTerminalLogs([]);
    setRunResults(null);
    setRunMetadata(null);
    setError("");

    try {
      const startRes = await startRun(analysis.datasetName, testMode, targetUrl, duration, rateLimit);
      const activeRunId = startRes.runId;
      setRunId(activeRunId);
      setRunMetadata(startRes);
      if (startRes.fallbackReason) {
        setTerminalLogs([{
          timestamp: new Date().toLocaleTimeString(),
          content: `[hex-ai] ${startRes.fallbackReason}`
        }]);
      }

      const interval = setInterval(async () => {
        try {
          const statusRes = await getRunStatus(activeRunId);
          setRunMetadata((current) => ({ ...(current || {}), ...statusRes }));
          setRunProgress(statusRes.progress);
          setLiveMetrics(statusRes.metrics);
          setTerminalLogs(statusRes.logs);

          if (statusRes.status === "completed" || statusRes.status === "blocked" || statusRes.status === "failed") {
            clearInterval(interval);
            setExecutionState(statusRes.status === "completed" ? "completed" : "blocked");

            const resultsRes = await getRunResults(activeRunId);
            setRunResults(resultsRes);

            setActiveTab("results");
          }
        } catch (pollErr) {
          clearInterval(interval);
          setError(pollErr.message);
          setExecutionState("idle");
        }
      }, 1000);

    } catch (err) {
      setError(err.message);
      setExecutionState("idle");
    }
  }

  if (loading && !analysis) {
    return <LoadingScreen />;
  }

  if (!analysis) {
    return (
      <main className="app-shell production-start">
        <section className="workspace workspace-single">
          <Header datasetName="No dataset loaded" activeTab="import" />
          {error ? <div className="error-banner">{error}</div> : null}
          <UploadPanel onUpload={handleUpload} loading={loading} />
          {uploadQualityIssue ? <DataQualityPanel dataQuality={uploadQualityIssue} /> : null}
          <ProductionInputPanel />
          <AiRolePanel />
        </section>
      </main>
    );
  }

  return (
    <main className="app-shell">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      <section className="workspace">
        <Header datasetName={analysis.datasetName} activeTab={activeTab} />
        <MobileNav activeTab={activeTab} setActiveTab={setActiveTab} />
        {error ? <div className="error-banner">{error}</div> : null}

        {activeTab === "import" && (
          <div className="tab-pane">
            <UploadPanel onUpload={handleUpload} loading={loading} />
            <MetricGrid summary={analysis.summary} />
                <DataQualityPanel dataQuality={uploadQualityIssue || analysis.dataQuality} />
                <AiAssistancePanel assistance={analysis.aiAssistance} />
                <CorrelationRulesPanel rules={analysis.correlationRules} />
                <TelemetryPipeline />

            <div className="panel glass" style={{ minHeight: "auto", marginTop: "1rem" }}>
              <PanelHeading title="Ingested Telemetry Specifications" subtitle="Production parameters extracted and structured for traffic twin simulations." />
              <div className="detail-list" style={{ marginTop: "0.5rem" }}>
                <Detail label="Privacy Masking" value={`${analysis.summary.maskedFields} sensitive values redacted`} />
                <Detail label="Topology Detection" value={analysis.summary.journeyDetection ? "Distributed Traces Active" : "Gateway Logs Fallback"} />
                <Detail
                  label="Autoscale Analysis"
                  value={
                    analysis.summary.replicaAnalysis
                      ? `Replica Evidence: ${(analysis.replicas?.source || "telemetry").replaceAll("_", " ")}`
                      : "No replica evidence ingested"
                  }
                />
              </div>
            </div>
          </div>
        )}

        {activeTab === "traffic" && (
          <div className="tab-pane">
            <RiskTable endpoints={analysis.endpoints} />
          </div>
        )}

        {activeTab === "journeys" && (
          <div className="tab-pane">
            <div style={{ display: "grid", gap: "1.5rem" }}>
              <JourneyPanel journeys={analysis.journeys} />
              <MarkovMatrixGrid matrix={analysis.markovMatrix} />
            </div>
          </div>
        )}

        {activeTab === "scenario-builder" && (
          <div className="tab-pane scenario-builder">
            <article className="panel config-card glass">
	              <PanelHeading title="Scenario Builder" subtitle="Customize the performance twin k6 workload model constraints." />
	              <AutonomousAgentPanel agent={analysis.autonomousAgent} onApply={setTestMode} />
	              <AiAssistancePanel assistance={analysis.aiAssistance} compact />
	              <CorrelationRulesPanel rules={analysis.correlationRules} compact />
              <form onSubmit={handleGenerateScript} className="config-card" style={{ padding: 0, border: "none", boxShadow: "none", background: "none", backdropFilter: "none" }}>
                <div className="config-group">
                  <label>Workload Strategy Profile</label>
                  <div className="mode-grid">
                    <ModeButton mode="mirror" title="Production Mirror" desc="Probabilistic Markov-chain transition replay." activeMode={testMode} setMode={setTestMode} />
                    <ModeButton mode="peak" title="Peak hour Replay" desc="Scales traffic rate to match highest telemetry throughput." activeMode={testMode} setMode={setTestMode} />
                    <ModeButton mode="spike" title="Spike Test" desc="Rapid VU scaling stages to verify pod autoscaler limits." activeMode={testMode} setMode={setTestMode} />
                    <ModeButton mode="breakpoint" title="Breakpoint Test" desc="Linear rate ramp up until latency threshold breaches." activeMode={testMode} setMode={setTestMode} />
                    <ModeButton mode="critical" title="Critical Transactions" desc="Target payment/checkout workflows only." activeMode={testMode} setMode={setTestMode} />
                    <ModeButton mode="load_balance" title="Load Balance check" desc="Stress routes to validate ingress distribution." activeMode={testMode} setMode={setTestMode} />
                  </div>
                </div>

                <div style={{ display: "grid", gridTemplateColumns: "1.5fr 1fr 1fr", gap: "1rem" }}>
                  <div className="config-group">
                    <label>Staging Target URL</label>
                    <input type="text" value={targetUrl} onChange={(e) => setTargetUrl(e.target.value)} required />
                  </div>
                  <div className="config-group">
                    <label>Duration Limit</label>
                    <select value={duration} onChange={(e) => setDuration(e.target.value)}>
                      <option value="1m">1 minute</option>
                      <option value="5m">5 minutes (Default)</option>
                      <option value="15m">15 minutes</option>
                    </select>
                  </div>
                  <div className="config-group">
                    <label>Target Arrival Rate (req/s)</label>
                    <input type="text" value={rateLimit} onChange={(e) => setRateLimit(e.target.value)} required />
                  </div>
                </div>

                <button type="submit" disabled={generatingScript} style={{ width: "100%", marginTop: "0.5rem" }}>
                  {generatingScript ? "Recompiling script..." : "Regenerate Test Script"}
                </button>
              </form>
            </article>

            <ScriptPanel script={customScript} onExecute={() => setActiveTab("execution")} />
          </div>
        )}

        {activeTab === "execution" && (
          <div className="tab-pane run-grid">
            <article className="panel progress-card glass">
              <div>
                <PanelHeading title="Twin Load Execution Board" subtitle="Runs real k6 only when enabled and target-safe; otherwise falls back to deterministic replay." />
                <RunModeNotice metadata={runMetadata} targetUrl={targetUrl} />

                {executionState === "idle" && (
                  <div style={{ textAlign: "center", padding: "3rem 1rem" }}>
                    <div className="logo-mark" style={{ background: "rgba(255,255,255,0.03)", color: "var(--muted)", boxShadow: "none", width: "4rem", height: "4rem" }}>▶</div>
                    <h3 style={{ margin: "1rem 0 0.5rem", fontSize: "1.1rem" }}>Ready to execute k6 script</h3>
                    <p style={{ color: "var(--muted)", fontSize: "0.85rem", marginBottom: "1.5rem" }}>
                      Deploys a stateful load testing runner for <code>{targetUrl}</code> using the '{testMode}' transition workload.
                    </p>
                    <button onClick={handleStartExecution}>Start Load Test Replay</button>
                  </div>
                )}

                {executionState === "running" && (
                  <div>
                    <div className="progress-header">
                      <strong>{runMetadata?.executionMode === "real" ? "Running k6 Load Test..." : "Preparing Execution Artifact..."}</strong>
                      <span style={{ color: "var(--accent)" }}>{runProgress}% Completed</span>
                    </div>
                    <div className="progress-bar-container">
                      <div className="progress-bar-fill" style={{ width: `${runProgress}%` }} />
                    </div>

                    <div className="progress-stats">
                      <div>
                        <span>Active VUs</span>
                        <strong>{liveMetrics.length > 0 ? liveMetrics[liveMetrics.length - 1].vus : 0}</strong>
                      </div>
                      <div>
                        <span>Request Rate</span>
                        <strong>{liveMetrics.length > 0 ? liveMetrics[liveMetrics.length - 1].rate : 0} /s</strong>
                      </div>
                      <div>
                        <span>p95 Latency</span>
                        <strong>{liveMetrics.length > 0 ? liveMetrics[liveMetrics.length - 1].latencyMs : 0} ms</strong>
                      </div>
                    </div>
                  </div>
                )}

                {executionState === "completed" && (
                  <div style={{ textAlign: "center", padding: "2.5rem 1rem" }}>
                    <div className="logo-mark" style={{ background: "var(--success-glow)", border: "1px solid rgba(16,185,129,0.2)", color: "var(--success)", boxShadow: "none", width: "4rem", height: "4rem" }}>✓</div>
                    <h3 style={{ margin: "1.5rem 0 0.5rem", fontSize: "1.1rem" }}>Test Twin Replay Completed</h3>
                    <p style={{ color: "var(--muted)", fontSize: "0.85rem", marginBottom: "1.5rem" }}>
                      Analysing run metrics against production baseline limits...
                    </p>
                    <button onClick={() => setActiveTab("results")}>Inspect Comparisons & Remediation</button>
                  </div>
                )}

                {executionState === "blocked" && (
                  <div style={{ textAlign: "center", padding: "2.5rem 1rem" }}>
                    <div className="logo-mark" style={{ background: "var(--warning-glow)", border: "1px solid rgba(245,158,11,0.2)", color: "var(--warning)", boxShadow: "none", width: "4rem", height: "4rem" }}>!</div>
                    <h3 style={{ margin: "1.5rem 0 0.5rem", fontSize: "1.1rem" }}>Real Execution Not Started</h3>
                    <p style={{ color: "var(--muted)", fontSize: "0.85rem", marginBottom: "1.5rem" }}>
                      HEX AI saved the generated script but did not produce load-test metrics because the real runner guard blocked execution.
                    </p>
                    <button onClick={() => setActiveTab("results")}>Inspect Script Artifact & Source Findings</button>
                  </div>
                )}
              </div>
            </article>

            <article className="panel terminal-card glass">
              <div className="terminal-header">
                <div className="window-controls">
                  <span className="control-dot close" />
                  <span className="control-dot minimize" />
                  <span className="control-dot maximize" />
                </div>
                <div className="terminal-title">k6-runner-agent@hex-ai</div>
                <div style={{ width: 42 }}></div>
              </div>
              <div className="terminal-output">
                {terminalLogs.length === 0 ? (
                  <div style={{ color: "var(--subtle)" }}>Terminal console inactive. Waiting for load run...</div>
                ) : (
                  terminalLogs.map((log, index) => (
                    <div className="terminal-line" key={index}>
                      <span>[{log.timestamp}]</span>
                      <strong>{log.content}</strong>
                    </div>
                  ))
                )}
                <div ref={terminalEndRef} />
              </div>
            </article>
          </div>
        )}

        {activeTab === "results" && (
          <div className="tab-pane">
            {runResults ? (
              <>
                <ExecutionSummary results={runResults} />
                <ResultsPanel results={runResults.results} />
                <LoadBalanceEvidencePanel evidence={runResults.loadBalanceEvidence} />

                <div className="dashboard-grid">
                  {/* SVG Topology Graph Panel */}
                  <article className="panel glass">
                    <PanelHeading title="Service Trace Topology Map" subtitle="Distributed trace relationships mapping Gateway nodes to microservices. Heatmaps represent latency hot spots." />

                    <TopologyGraph dependencies={analysis.dependencies} />

                    <div className="detail-list" style={{ marginTop: "1rem" }}>
                      <Detail label="Topology Status" value={`${analysis.dependencies.nodes.length} services traced`} />
                      <Detail label="Bottleneck service" value={runResults.results.bottleneck} />
                      <Detail label="Max Trace contribution" value={`${runResults.results.bottleneckShare}%`} />
                    </div>
                  </article>

                  {/* Replica imbalance detail list */}
                  <article className="panel glass">
                    <PanelHeading title="Ingress Replica Balancer validation" subtitle="Load-balancing verification showing requests distribution share and hotspots across individual replica pods." />

                    <div style={{ display: "flex", flexDirection: "column", flexGrow: 1 }}>
                      <ReplicaDistributionList replicas={analysis.replicas} />
                    </div>
                  </article>

                  {/* Endpoint proportion bars */}
                  <article className="panel glass">
                    <PanelHeading title="Endpoint Traffic Distribution Comparison" subtitle="Learned Production mix versus Twin Load test run proportions." />

                    <div className="chart-comparison">
                      {runResults.comparisons.endpoints.slice(0, 5).map((ep, idx) => (
                        <div className="comparison-row" key={idx}>
                          <div className="comparison-label">{ep.route}</div>
                          <div className="comparison-bars">
                            <div className="bar-container">
                              <div className="bar-track">
                                <div className="bar-fill production" style={{ width: `${ep.productionShare}%` }} />
                              </div>
                              <span style={{ color: "var(--accent)" }}>{ep.productionShare}%</span>
                            </div>
                            <div className="bar-container">
                              <div className="bar-track">
                                <div className="bar-fill test-run" style={{ width: `${ep.testRunShare}%` }} />
                              </div>
                              <span style={{ color: "var(--accent-strong)" }}>{ep.testRunShare}%</span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>

                    <div className="chart-legend">
                      <div className="legend-item">
                        <div className="legend-color production" />
                        <span>Telemetry Production Share</span>
                      </div>
                      <div className="legend-item">
                        <div className="legend-color test-run" />
                        <span>Twin execution Replay Share</span>
                      </div>
                    </div>
                  </article>

                  {/* Journey comparison */}
                  <article className="panel glass">
                    <PanelHeading title="User Workflows Mix Comparison" subtitle="Observed session sequences compared with generated workload targets or real k6 output when available." />

                    <div className="chart-comparison">
                      {runResults.comparisons.journeys.map((jr, idx) => (
                        <div className="comparison-row" key={idx} style={{ gridTemplateColumns: "14rem 1fr" }}>
                          <div className="comparison-label">{jr.name}</div>
                          <div className="comparison-bars">
                            <div className="bar-container">
                              <div className="bar-track">
                                <div className="bar-fill production" style={{ width: `${jr.productionShare}%` }} />
                              </div>
                              <span style={{ color: "var(--accent)" }}>{jr.productionShare}%</span>
                            </div>
                            <div className="bar-container">
                              <div className="bar-track">
                                <div className="bar-fill test-run" style={{ width: `${jr.testRunShare}%` }} />
                              </div>
                              <span style={{ color: "var(--accent-strong)" }}>{jr.testRunShare}%</span>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>

                    <div className="chart-legend">
                      <div className="legend-item">
                        <div className="legend-color production" />
                        <span>Production Journeys Mix</span>
                      </div>
                      <div className="legend-item">
                        <div className="legend-color test-run" />
                        <span>Twin Markov Replay Mix</span>
                      </div>
                    </div>
                  </article>
                </div>

                {/* Autonomous Remediation Advisor Cards section */}
                <article className="panel glass" style={{ minHeight: "auto", gridColumn: "span 2" }}>
                  <PanelHeading title="Autonomous Performance Remediation Advisor" subtitle="AI recommendations calculated by parsing latency distributions, trace query fan-outs, and replica load balancer imbalances." />
                  <RemediationAdvisor advices={runResults.remediationAdvice} />
                </article>
              </>
            ) : (
              <article className="panel glass" style={{ textAlign: "center", padding: "5rem 1rem" }}>
                <div className="logo-mark" style={{ background: "rgba(255,255,255,0.03)", color: "var(--muted)", boxShadow: "none", width: "4rem", height: "4rem" }}>!</div>
                <h3 style={{ margin: "1rem 0 0.5rem", fontSize: "1.1rem" }}>No results available</h3>
                <p style={{ color: "var(--muted)", fontSize: "0.85rem", marginBottom: "1.5rem" }}>
                  Please generate and run a twin test script in the 'Scenario Builder' and 'Run Execution' tabs first.
                </p>
                <button onClick={() => setActiveTab("scenario-builder")}>Configure Scenario</button>
              </article>
            )}
          </div>
        )}

        {/* Quantitative Comparison Tab */}
        {activeTab === "comparison" && (
          <div className="tab-pane">
            <div className="panel glass" style={{ minHeight: "auto", marginBottom: "1.5rem" }}>
              <PanelHeading title="Methodology Performance Benchmarking" subtitle="How Telemetry-Derived twins perform against alternative scripting paradigms." />
              <p style={{ color: "var(--muted)", fontSize: "0.88rem", marginTop: "0.5rem", lineHeight: "1.6" }}>
                To prove the business case for production-traffic performance twin generators, we compare HEX AI quantitatively with three standard industry techniques on key QA indicators. Let the numbers do the talking.
              </p>
            </div>

            <div className="benchmark-section">
              {analysis.benchmarks && analysis.benchmarks.map((bm, index) => (
                <BenchmarkCard key={index} benchmark={bm} />
              ))}
            </div>
          </div>
        )}
      </section>
    </main>
  );
}

function LoadingScreen() {
  return (
    <main className="state-screen">
      <div className="logo-mark" style={{ width: "4rem", height: "4rem" }}>
        <HexAiLogo size={40} />
      </div>
      <h1>HEX AI</h1>
      <p>Analyzing telemetry pipelines and building performance model twin...</p>
    </main>
  );
}

function Sidebar({ activeTab, setActiveTab }) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <div className="logo-mark">
          <HexAiLogo size={24} />
        </div>
        <div>
          <strong>HEX AI</strong>
          <span>Team H5X</span>
        </div>
      </div>
      <nav className="nav-list" aria-label="Sections">
        {NAV_ITEMS.map((item) => (
          <button
            className={activeTab === item.id ? "active" : ""}
            onClick={() => setActiveTab(item.id)}
            key={item.id}
          >
            {item.label}
          </button>
        ))}
      </nav>
      <div className="sidebar-card">
        <span>Model Twin</span>
        <strong>Markov Workloads</strong>
        <p>Production telemetry validation & automated remediation advice.</p>
      </div>
    </aside>
  );
}

function MobileNav({ activeTab, setActiveTab }) {
  return (
    <nav className="mobile-nav" aria-label="Sections">
      {NAV_ITEMS.map((item) => (
        <button
          className={activeTab === item.id ? "active" : ""}
          key={item.id}
          onClick={() => setActiveTab(item.id)}
          type="button"
        >
          {item.label}
        </button>
      ))}
    </nav>
  );
}

function Header({ datasetName, activeTab }) {
  const titles = {
    "import": "1. Import Telemetry Data",
    "traffic": "2. Traffic Performance Intelligence",
    "journeys": "3. Observed Journeys Explorer",
    "scenario-builder": "4. Scenario Builder Options",
    "execution": "5. Twin Load Execution",
    "results": "6. Verification & Fidelity Comparison",
    "comparison": "Comparative Benchmarking Metrics"
  };

  return (
    <header className="topbar">
      <div>
        <h1>{titles[activeTab] || "Production Telemetry Twin"}</h1>
        <p>Reconstruct probabilistic workflows, auto-generate state-machine scripts, and diagnose system bottlenecks.</p>
      </div>
      <div className="target-card">
        <span>Dataset Source</span>
        <strong>{datasetName}</strong>
      </div>
    </header>
  );
}

function UploadPanel({ onUpload, loading }) {
  const [gatewayLogs, setGatewayLogs] = useState([]);
  const [traces, setTraces] = useState([]);
  const [podMetrics, setPodMetrics] = useState([]);
  const [applicationLogs, setApplicationLogs] = useState([]);
  const [sampleLoading, setSampleLoading] = useState(false);
  const [sampleZipLoading, setSampleZipLoading] = useState(false);
  const [sampleError, setSampleError] = useState("");

  function submit(event) {
    event.preventDefault();
    if (gatewayLogs.length === 0 && traces.length === 0) return;
    onUpload({ gatewayLogs, traces, podMetrics, applicationLogs });
  }

  function selectedFiles(event) {
    return Array.from(event.target.files || []);
  }

  function fileCount(files) {
    if (!files.length) return "No files selected";
    if (files.length === 1) return files[0].name;
    return `${files.length} files selected`;
  }

  async function loadSampleTelemetry() {
    setSampleError("");
    setSampleLoading(true);
    try {
      const sampleFiles = await fetchSampleTelemetryFiles();
      setGatewayLogs(sampleFiles.gatewayLogs);
      setTraces(sampleFiles.traces);
      setPodMetrics(sampleFiles.podMetrics);
      setApplicationLogs(sampleFiles.applicationLogs);
      await onUpload(sampleFiles);
    } catch (err) {
      setSampleError(err.message || "Sample telemetry could not be loaded");
    } finally {
      setSampleLoading(false);
    }
  }

  async function loadSampleTelemetryZip() {
    setSampleError("");
    setSampleZipLoading(true);
    try {
      const sampleFiles = await fetchSampleTelemetryFiles(SAMPLE_TELEMETRY_ZIP_FILES);
      setGatewayLogs(sampleFiles.gatewayLogs);
      setTraces(sampleFiles.traces);
      setPodMetrics(sampleFiles.podMetrics);
      setApplicationLogs(sampleFiles.applicationLogs);
      await onUpload(sampleFiles);
    } catch (err) {
      setSampleError(err.message || "Sample ZIP telemetry could not be loaded");
    } finally {
      setSampleZipLoading(false);
    }
  }

  return (
    <form className="upload-panel glass" onSubmit={submit}>
      <div>
        <h2>Upload Telemetry Sources</h2>
        <p>Ingest real gateway logs or OpenTelemetry HTTP traces, plus application logs, optional pod metrics, or compressed archives.</p>
      </div>
      <label>
        Gateway Logs (CSV/JSON/HAR/LOG/GZ/ZIP)
        <input type="file" multiple accept=".csv,.json,.jsonl,.ndjson,.har,.log,.txt,.gz,.zip" onChange={(event) => setGatewayLogs(selectedFiles(event))} />
        <small>{fileCount(gatewayLogs)}</small>
      </label>
      <label>
        OTel Traces (JSON/GZ/ZIP, can be primary)
        <input type="file" multiple accept=".json,.gz,.zip" onChange={(event) => setTraces(selectedFiles(event))} />
        <small>{fileCount(traces)}</small>
      </label>
      <label>
        Pod Metrics (CSV/PROM/OpenMetrics/GZ/ZIP)
        <input type="file" multiple accept=".csv,.prom,.openmetrics,.txt,.gz,.zip" onChange={(event) => setPodMetrics(selectedFiles(event))} />
        <small>{fileCount(podMetrics)}</small>
      </label>
      <label>
        App Logs (JSON/CSV/TXT/GZ/ZIP)
        <input type="file" multiple accept=".json,.jsonl,.ndjson,.csv,.log,.txt,.gz,.zip" onChange={(event) => setApplicationLogs(selectedFiles(event))} />
        <small>{fileCount(applicationLogs)}</small>
      </label>
      <button disabled={(gatewayLogs.length === 0 && traces.length === 0) || loading} type="submit">
        {loading ? "Analyzing..." : "Ingest Telemetry"}
      </button>
      <div className="sample-telemetry">
        <span>Demo-ready dataset</span>
        <p>Load the bundled enterprise checkout sample, or upload the same data as ZIP archives to exercise decompression plus HAR correlation, trace diagnosis, pod imbalance, and guarded k6 generation.</p>
        <button type="button" className="secondary-button" disabled={loading || sampleLoading} onClick={loadSampleTelemetry}>
          {sampleLoading ? "Loading sample..." : "Load Sample Telemetry"}
        </button>
        <button type="button" className="secondary-button" disabled={loading || sampleZipLoading} onClick={loadSampleTelemetryZip}>
          {sampleZipLoading ? "Uploading ZIPs..." : "Load Sample ZIPs"}
        </button>
        {sampleError ? <small className="sample-error">{sampleError}</small> : null}
      </div>
    </form>
  );
}

function MetricGrid({ summary }) {
  const cards = [
    ["Telemetry Events", formatNumber.format(summary.requestsImported)],
    ["Logical Routes", summary.routesFound],
    ["Traffic Source", summary.traceDerivedTraffic ? "OTel traces" : "Gateway logs"],
    ["Critical Journeys", summary.criticalJourneys],
    ["High-Risk APIs", summary.riskApis],
    ["Correlation Rules", summary.dynamicCorrelations ?? 0],
    ["Telemetry Readiness", `${summary.fidelityScore}%`],
    ["Peak Load Rate", `${summary.peakThroughput}/min`],
  ];

  return (
    <section className="metric-grid">
      {cards.map(([label, value]) => (
        <article className="metric-card glass" key={label}>
          <span>{label}</span>
          <strong>{value}</strong>
        </article>
      ))}
    </section>
  );
}

function ProductionInputPanel() {
  const required = [
    ["Gateway access logs", "CSV/JSON/JSONL/HAR/access-log files with timestamp, method, route/path/url, status, duration. Optional when traces contain HTTP spans."],
    ["OpenTelemetry traces", "resourceSpans or span-list JSON files with http.route, method, status, and duration. Can be the primary traffic source."],
    ["Application logs", "one or more JSON/JSONL/CSV/text/OTLP resourceLogs files or archives with level, message, service.name, traceId when available"],
    ["Pod metrics", "CSV, Prometheus, or OpenMetrics files with service, pod, request count, CPU, p95 latency, error rate"],
  ];

  return (
    <article className="panel glass production-inputs">
      <PanelHeading title="Production Input Contract" subtitle="HEX AI starts empty and only analyzes uploaded telemetry. No bundled data is injected into production analysis." />
      <div className="input-contract-grid">
        {required.map(([title, fields]) => (
          <div key={title}>
            <strong>{title}</strong>
            <span>{fields}</span>
          </div>
        ))}
      </div>
    </article>
  );
}

function AiRolePanel() {
  return (
    <article className="panel glass production-inputs">
      <PanelHeading title="Where AI Fits" subtitle="AI is constrained to evidence from uploaded telemetry and real run output." />
      <div className="input-contract-grid ai-grid">
        <div>
          <strong>Schema Inference</strong>
          <span>Map messy enterprise field names into a normalized telemetry model.</span>
        </div>
        <div>
          <strong>Scenario Selection</strong>
          <span>Recommend mirror, critical, spike, or load-balance tests from endpoint risk and journeys.</span>
        </div>
        <div>
          <strong>Root-Cause Explanation</strong>
          <span>Explain bottlenecks using traces, app logs, pod metrics, and k6 summaries.</span>
        </div>
      </div>
    </article>
  );
}

function AiAssistancePanel({ assistance, compact = false }) {
  if (!assistance) return null;

  const summary = assistance.summary || {};
  const statusLabel = assistance.llmConfigured
    ? assistance.llmStatus === "completed"
      ? "Gemini completed"
      : assistance.llmStatus === "error"
        ? "Gemini fallback"
        : "Gemini configured"
    : "Rules engine only";
  const notes = summary.scriptGenerationNotes || [];
  const cautions = summary.cautions || [];

  return (
    <article className={`ai-assistance-panel glass ${assistance.llmStatus || "not_configured"} ${compact ? "compact" : ""}`}>
      <div className="ai-assistance-header">
        <div>
          <span>{assistance.mode?.replaceAll("_", " ") || "rules engine"}</span>
          <strong>{statusLabel}</strong>
        </div>
        <small>{assistance.provider || "local"} {assistance.model ? `- ${assistance.model}` : ""}</small>
      </div>
      {!compact && (
        <p>{summary.executiveSummary || assistance.note}</p>
      )}
      <div className="ai-assistance-grid">
        <div>
          <span>Risk readout</span>
          <strong>{summary.riskNarrative || "Risk will be explained after telemetry upload."}</strong>
        </div>
        <div>
          <span>Scenario rationale</span>
          <strong>{summary.scenarioRationale || assistance.evidence?.topRiskEndpoint || "Evidence pending."}</strong>
        </div>
        <div>
          <span>Judge answer</span>
          <strong>{summary.judgeAnswer || assistance.note}</strong>
        </div>
      </div>
      {notes.length > 0 ? (
        <ul className="ai-assistance-list">
          {notes.slice(0, compact ? 2 : 4).map((note) => (
            <li key={note}>{note}</li>
          ))}
        </ul>
      ) : null}
      {assistance.llmError ? <p className="ai-warning">Gemini error: {assistance.llmError}</p> : null}
      {!compact && cautions.length > 0 ? (
        <p className="ai-warning">{cautions.slice(0, 2).join(" ")}</p>
      ) : null}
    </article>
  );
}

function DataQualityPanel({ dataQuality }) {
  if (!dataQuality) return null;

  const status = dataQuality.status || "ok";
  const inputs = dataQuality.inputs || {};
  const capabilities = dataQuality.capabilities || {};
  const issues = [
    ...(dataQuality.errors || []).map((message) => ({ level: "error", message })),
    ...(dataQuality.warnings || []).map((message) => ({ level: "warning", message })),
  ];

  const cards = [
    ["Gateway files", inputs.gatewayLogs?.sourceFiles ?? 0],
    ["Gateway rows", inputs.gatewayLogs?.acceptedRows ?? 0],
    ["Trace files", inputs.traces?.sourceFiles ?? 0],
    ["Trace spans", inputs.traces?.acceptedRows ?? 0],
    ["App log rows", inputs.applicationLogs?.acceptedRows ?? 0],
    ["Pod records", inputs.podMetrics?.acceptedRows ?? 0],
    ["Replica source", (dataQuality.replicaSource || "none").replaceAll("_", " ")],
    ["Traffic source", (dataQuality.trafficSource || "none").replaceAll("_", " ")],
    ["Journey mining", capabilities.journeyMining ? "Ready" : "Limited"],
    ["Replica analysis", capabilities.replicaAnalysis ? "Ready" : "Skipped"],
    ["Correlation mining", capabilities.correlationMining ? "Ready" : "Limited"],
  ];

  return (
    <article className={`quality-card glass ${status}`}>
      <PanelHeading
        title={`Data Quality: ${status.toUpperCase()}`}
        subtitle="Input resilience report showing accepted rows, degraded capabilities, and parser warnings before script generation."
      />
      <div className="quality-grid">
        {cards.map(([label, value]) => (
          <div key={label}>
            <span>{label}</span>
            <strong>{value}</strong>
          </div>
        ))}
      </div>
      {issues.length > 0 ? (
        <div className="quality-issue-list">
          {issues.slice(0, 5).map((issue, index) => (
            <div className={`quality-issue ${issue.level}`} key={`${issue.level}-${index}`}>
              <strong>{issue.level}</strong>
              <span>{issue.message}</span>
            </div>
          ))}
        </div>
      ) : (
        <p className="quality-ok">All required telemetry fields were accepted. Optional observability files can still improve diagnosis depth.</p>
      )}
    </article>
  );
}

function CorrelationRulesPanel({ rules = [], compact = false }) {
  if (!rules || rules.length === 0) {
    return compact ? null : (
      <article className="panel glass" style={{ minHeight: "auto" }}>
        <PanelHeading title="Dynamic Correlation Rules" subtitle="No response-to-request value reuse was detected yet. HAR request/response bodies or headers improve this signal." />
      </article>
    );
  }

  return (
    <article className="panel glass" style={{ minHeight: "auto" }}>
      <PanelHeading
        title="Dynamic Correlation Rules"
        subtitle="Sensitive values are fingerprint-matched only; raw tokens, IDs, and body values are not stored in the analysis."
      />
      <div className="detail-list">
        {rules.slice(0, compact ? 3 : 6).map((rule) => (
          <Detail
            key={`${rule.sourceState}-${rule.targetState}-${rule.name}-${rule.injectionField}`}
            label={`${rule.name} -> ${rule.injectionField}`}
            value={`${rule.sourceState} extracts ${rule.extractorPath}; ${rule.targetState} injects into ${rule.targetLocation}`}
          />
        ))}
      </div>
    </article>
  );
}

function AutonomousAgentPanel({ agent, onApply }) {
  if (!agent) return null;
  const target = agent.targetEndpoint?.route
    ? `${agent.targetEndpoint.method} ${agent.targetEndpoint.route}`
    : "No endpoint selected yet";

  return (
    <article className={`agent-panel ${agent.status}`}>
      <div className="agent-header">
        <div>
          <span>{agent.autonomy}</span>
          <strong>{agent.name}</strong>
        </div>
        <button type="button" onClick={() => onApply(agent.recommendedScenario)}>
          Use {agent.recommendedScenario}
        </button>
      </div>
      <p>{agent.objective}</p>
      <div className="agent-facts">
        <div>
          <span>Status</span>
          <strong>{agent.status}</strong>
        </div>
        <div>
          <span>Evidence</span>
          <strong>{(agent.evidenceSource || "none").replaceAll("_", " ")}</strong>
        </div>
        <div>
          <span>Target service</span>
          <strong>{agent.targetService || "none"}</strong>
        </div>
        <div>
          <span>Target endpoint</span>
          <strong>{target}</strong>
        </div>
        <div>
          <span>Imbalance</span>
          <strong>{agent.imbalanceScore}</strong>
        </div>
      </div>
      <div className="agent-plan">
        <div>
          <span>Hypothesis</span>
          <strong>{agent.hypothesis}</strong>
        </div>
        <div>
          <span>Probe plan</span>
          <strong>{agent.probePlan?.probeType?.replaceAll("_", " ") || "not selected"}</strong>
          <small>{agent.probePlan?.expectedEvidence}</small>
        </div>
        <div>
          <span>Pass criteria</span>
          <ul>
            {(agent.passCriteria || []).map((criterion) => (
              <li key={criterion}>{criterion}</li>
            ))}
          </ul>
        </div>
      </div>
      <div className="agent-steps">
        {agent.actions.map((action) => (
          <div className={`agent-step ${action.status}`} key={action.step}>
            <strong>{action.step}</strong>
            <span>{action.detail}</span>
          </div>
        ))}
      </div>
    </article>
  );
}

function RiskTable({ endpoints }) {
  return (
    <article className="panel panel-large glass" id="traffic">
      <PanelHeading title="Endpoint Risk Rankings" subtitle="API routes ranked by traffic weights, p95 latencies, error percentages, distributed trace fan-outs, and business criticality." />
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Endpoint</th>
              <th>Observed Latency (p95)</th>
              <th>Error Rate</th>
              <th>Risk Score</th>
              <th>Twin Prioritization Finding</th>
            </tr>
          </thead>
          <tbody>
            {endpoints.map((endpoint) => (
              <tr key={`${endpoint.method}-${endpoint.route}`}>
                <td>
                  <span className={`method ${endpoint.method.toLowerCase()}`}>{endpoint.method}</span>
                  <code>{endpoint.route}</code>
                </td>
                <td style={{ fontWeight: 600 }}>{endpoint.p95LatencyMs} ms</td>
                <td style={{ color: endpoint.errorRate > 0.02 ? "var(--danger)" : "var(--success)", fontWeight: 600 }}>
                  {(endpoint.errorRate * 100).toFixed(1)}%
                </td>
                <td>
                  <RiskBar value={endpoint.riskScore} />
                </td>
                <td>{endpoint.reason}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </article>
  );
}

function JourneyPanel({ journeys }) {
  const primary = journeys[0];
  return (
    <article className="panel glass" id="journeys">
      <PanelHeading title="Mined User Workflow journeys" subtitle="Sequences discovered by grouping traces and calculating think-time distributions." />
      {primary ? (
        <div style={{ display: "flex", flexDirection: "column", flexGrow: 1 }}>
          <div className="journey-title">
            <strong>{primary.name}</strong>
            <span>{Math.round(primary.share * 100)}% traffic share</span>
          </div>
          <div className="journey-flow">
            {primary.sequence.map((step, index) => (
              <React.Fragment key={`${step}-${index}`}>
                <span>{step}</span>
                {index < primary.sequence.length - 1 ? <em>→</em> : null}
              </React.Fragment>
            ))}
          </div>
          <div className="detail-list">
            <Detail label="Think time pacing" value={primary.thinkTimeSeconds} />
            <Detail label="Avg sequence duration" value={`${primary.avgDurationMs} ms`} />
            <Detail label="Correlated parameters" value={primary.dynamicValues.join(", ") || "none"} />
          </div>
        </div>
      ) : (
        <p>No journeys detected. Upload distributed traces to cluster sequences.</p>
      )}
    </article>
  );
}

function MarkovMatrixGrid({ matrix }) {
  const states = Object.keys(matrix || {});
  if (states.length === 0) return null;

  return (
    <div className="panel glass">
      <PanelHeading title="Workload Markov State Transition Matrix" subtitle="State-to-state transition probabilities computed from production log order matrices. Maps user navigation flows." />
      <div className="table-wrap">
        <table className="matrix-table">
          <thead>
            <tr>
              <th style={{ textAlign: "left" }}>From State</th>
              {states.map(s => <th key={s}>{formatMatrixState(s)}</th>)}
              <th>Session End</th>
            </tr>
          </thead>
          <tbody>
            {states.map(fromState => (
              <tr key={fromState}>
                <td className="matrix-state" style={{ fontFamily: "monospace", fontSize: "0.8rem" }}>{fromState}</td>
                {states.map(toState => {
                  const val = matrix[fromState][toState] || 0;
                  return (
                    <td key={toState} className={`matrix-val ${val === 0 ? "zero" : ""}`}>
                      {val > 0 ? `${Math.round(val * 100)}%` : "-"}
                    </td>
                  );
                })}
                <td className={`matrix-val ${matrix[fromState]["END"] ? "" : "zero"}`}>
                  {matrix[fromState]["END"] ? `${Math.round(matrix[fromState]["END"] * 100)}%` : "-"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function formatMatrixState(state) {
  if (state === "__START__") {
    return "Session Start";
  }
  return state.replace("GET ", "").replace("POST ", "");
}

function TopologyGraph({ dependencies }) {
  const edges = dependencies.edges;
  const nodes = dependencies.nodes;

  return (
    <svg className="topo-svg" viewBox="0 0 540 220">
      <defs>
        <marker id="arrow" viewBox="0 0 10 10" refX="20" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="rgba(255,255,255,0.25)" />
        </marker>
      </defs>

      {edges.map((edge, index) => {
        const fromPos = NODE_POSITIONS[edge.source];
        const toPos = NODE_POSITIONS[edge.target];
        if (!fromPos || !toPos) return null;

        const isBottleneck = edge.target === "inventory" || edge.source === "checkout" && edge.target === "payment";

        return (
          <line
            key={index}
            x1={fromPos.x}
            y1={fromPos.y}
            x2={toPos.x}
            y2={toPos.y}
            className={`topo-edge ${isBottleneck ? "active" : ""}`}
            markerEnd="url(#arrow)"
          />
        );
      })}

      {nodes.map((node) => {
        const pos = NODE_POSITIONS[node.id];
        if (!pos) return null;

        const nodeClass = node.id === "gateway" ? "gateway" : (node.risk === "bottleneck" ? "bottleneck" : "normal");

        return (
          <g className={`topo-node ${nodeClass}`} key={node.id} transform={`translate(${pos.x}, ${pos.y})`}>
            <circle r="25" />
            <NodeIcon id={node.id} />
            <text y="36" style={{ textTransform: "capitalize", fontSize: "9px", fontWeight: 700 }}>{node.id}</text>
            <text y="45" style={{ fontSize: "8px", fill: "var(--accent-strong)", fontWeight: 600 }}>{node.latencyMs}ms</text>
          </g>
        );
      })}
    </svg>
  );
}

function ReplicaDistributionList({ replicas }) {
  if (!replicas.available || !replicas.services) {
    return <p>No pod replica configurations loaded in this telemetry file.</p>;
  }

  const hotspot = replicas.services.find((s) => s.status === "hotspot");

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100%" }}>
      {hotspot && (
        <div className="finding-card danger" style={{ margin: "0 0 1.25rem" }}>
          <strong>Load Distribution Imbalance Breach</strong>
          <span>Service <code>{hotspot.serviceName}</code> has breached ingress affinity limits. Pod <code>{hotspot.topPod}</code> is processing an overloaded traffic share. Imbalance Score: {hotspot.imbalanceScore}</span>
        </div>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: "1rem", flexGrow: 1 }}>
        {replicas.services.map((service) => {
          const maxRequests = Math.max(...service.pods.map(p => p.requests), 1);

          return (
            <div key={service.serviceName}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "0.35rem" }}>
                <strong style={{ fontSize: "0.85rem", textTransform: "uppercase", color: "var(--accent)" }}>{service.serviceName} replicas</strong>
                <span style={{ fontSize: "0.75rem", color: service.status === "hotspot" ? "var(--danger)" : "var(--muted)" }}>
                  Imbalance: {service.imbalanceScore}
                </span>
              </div>

              <div className="replica-dist">
                {service.pods.map((pod) => {
                  const percent = Math.round(pod.requests / maxRequests * 100);
                  const isPodHotspot = pod.podName === service.topPod && service.status === "hotspot";

                  return (
                    <div className={`replica-row ${isPodHotspot ? "hotspot" : ""}`} key={pod.podName}>
                      <span className="replica-name">{pod.podName}</span>
                      <div className="replica-bar-container">
                        <div className="replica-bar-fill" style={{ width: `${percent}%` }} />
                      </div>
                      <span style={{ textAlign: "right", fontFamily: "monospace", fontSize: "0.75rem" }}>{pod.requests} reqs</span>
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function LoadBalanceEvidencePanel({ evidence }) {
  if (!evidence) return null;
  const status = evidence.status || "not_collected";
  const replicas = evidence.replicas || [];

  return (
    <article className={`load-balance-evidence glass ${status}`}>
      <div>
        <span>Real Run Replica Evidence</span>
        <strong>{status.replaceAll("_", " ")}</strong>
        <p>
          {status === "not_executed"
            ? evidence.reason
            : status === "not_collected"
              ? "No k6 replica-hit samples were collected yet."
              : `${evidence.totalHits} samples captured. ${evidence.topReplica || "unknown"} served ${evidence.maxSharePercent}% of observed probe traffic.`}
        </p>
      </div>
      <div className="load-balance-bars">
        {replicas.length === 0 ? (
          <div className="replica-evidence-empty">Real k6 execution or served-by headers are required for this panel.</div>
        ) : (
          replicas.map((replica) => (
            <div className="replica-evidence-row" key={replica.replica}>
              <span>{replica.replica}</span>
              <div>
                <i style={{ width: `${replica.sharePercent}%` }} />
              </div>
              <strong>{replica.sharePercent}%</strong>
            </div>
          ))
        )}
      </div>
    </article>
  );
}

function ScriptPanel({ script, onExecute }) {
  const preview = script.split("\n").slice(0, 30).join("\n");
  const flowName = script.includes("loadBalanceProbeFlow")
    ? "loadBalanceProbeFlow"
    : script.includes("markovTwinFlow")
      ? "markovTwinFlow"
      : "k6 workload";
  const routeMatch = script.match(/const loadBalanceTarget = [\s\S]*?"route":\s*"([^"]+)"/);
  const scriptFacts = [
    ["Execution flow", flowName],
    ["Correlation runtime", script.includes("applyCorrelationRulesAfterResponse") ? "Ready" : "Not detected"],
    ["Focus route", routeMatch?.[1] || "Markov journey mix"],
    ["Script size", `${formatNumber.format(script.length)} chars`],
  ];

  function handleCopy() {
    navigator.clipboard.writeText(script);
    alert("Full script code copied to clipboard!");
  }

  return (
    <article className="panel panel-code glass">
      <PanelHeading title="Synthesized k6 Script Output" subtitle="Markov state engine compiled from telemetry; runtime data, auth, API keys and headers are injected through HEX_AI_* env vars." />
      <div className="script-facts">
        {scriptFacts.map(([label, value]) => (
          <div key={label}>
            <span>{label}</span>
            <strong>{value}</strong>
          </div>
        ))}
      </div>
      <pre>{preview}\n// ... [Full Markov state machine logic compiled successfully: click proceed to run]</pre>
      <p style={{ color: "var(--muted)", fontSize: "0.78rem", lineHeight: 1.6, marginTop: "0.75rem" }}>
        Generated scripts avoid embedded demo users, passwords, product IDs, payment values, auth tokens and API keys. Provide staging-safe data and headers at execution time.
      </p>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "0.5rem" }}>
        <button onClick={handleCopy} style={{ background: "rgba(255,255,255,0.03)", border: "1px solid var(--panel-border)", color: "#fff", boxShadow: "none" }}>
          Copy to Clipboard
        </button>
        <button onClick={onExecute}>Proceed to Execution</button>
      </div>
    </article>
  );
}

function RunModeNotice({ metadata, targetUrl }) {
  const mode = metadata?.executionMode || "guarded";
  const fallbackReason = metadata?.fallbackReason;

  return (
    <div className={`run-mode-notice ${mode}`}>
      <div>
        <span>Execution guard</span>
        <strong>{mode === "real" ? "Real k6 runner active" : "Dry run only"}</strong>
      </div>
      <p>
        {fallbackReason || `HEX AI will only run real k6 when enabled and the target ${targetUrl} is local, private, or allowlisted.`}
      </p>
      {metadata?.scriptPath ? <code>{metadata.scriptPath}</code> : null}
    </div>
  );
}

function ExecutionSummary({ results }) {
  return (
    <article className="execution-summary glass">
      <div>
        <span>Execution mode</span>
        <strong>{results.executionMode === "real" ? "Real k6" : "Dry run only"}</strong>
      </div>
      <div>
        <span>Target</span>
        <strong>{results.targetUrl}</strong>
      </div>
      <div>
        <span>Artifact</span>
        <strong>{results.artifacts?.scriptPath ? "Script saved" : "Not available"}</strong>
      </div>
      <p>{results.fallbackReason || "Real runner metrics were accepted from k6 summary output."}</p>
    </article>
  );
}

function ResultsPanel({ results }) {
  const fidelity = useMemo(
    () => [
      ["Endpoint Mix", results.endpointMixSimilarity],
      ["Journey Mix", results.journeyMixSimilarity],
      ["Think Time", results.thinkTimeSimilarity],
      ["Parameter Loop", results.dynamicWorkflowCompletion],
    ],
    [results],
  );

  const verdictClass = results.status === "passed"
    ? "passed"
    : results.status === "not_executed"
      ? "not-executed"
      : "failed";
  const verdictColor = results.status === "passed"
    ? "var(--success)"
    : results.status === "not_executed"
      ? "var(--warning)"
      : "var(--danger)";
  const verdictReason = results.verdictReason || results.firstFailure;

  return (
    <section className={`results-panel glass ${verdictClass}`}>
      <div>
        <h2>Execution Verdict: <strong style={{ color: verdictColor }}>{results.status.replace("_", " ").toUpperCase()}</strong></h2>
        <p>
          {verdictReason}. Distribution bottleneck located: <strong>{results.bottleneck}</strong> service. {results.loadBalanceFinding}.
        </p>
      </div>
      <div className="fidelity-grid">
        {fidelity.map(([label, value]) => (
          <div key={label}>
            <span>{label}</span>
            <strong>{value}%</strong>
          </div>
        ))}
      </div>
    </section>
  );
}

function RemediationAdvisor({ advices }) {
  if (!advices || advices.length === 0) return null;

  function handleCopyCommand(text) {
    navigator.clipboard.writeText(text);
    alert("Copied advice snippet to clipboard!");
  }

  return (
    <div className="remediation-grid">
      {advices.map((adv, idx) => {
        const catClass = adv.category.toLowerCase().includes("database") ? "database" : (adv.category.toLowerCase().includes("kubernetes") ? "kubernetes" : "api");
        const termLabel = adv.category.toLowerCase().includes("database") ? "SQL query" : "BASH command";

        return (
          <div className={`remediation-card ${catClass}`} key={idx}>
            <div>
              <span className="remediation-badge">{adv.category}</span>
              <h4>{adv.title}</h4>
              <p>{adv.description}</p>
              <div style={{ fontSize: "0.75rem", color: "var(--text)", marginBottom: "1rem", display: "flex", gap: "0.25rem", flexDirection: "column" }}>
                <span style={{ color: "var(--muted)", fontSize: "0.65rem", textTransform: "uppercase" }}>Expected Impact</span>
                <strong>{adv.impact}</strong>
              </div>
            </div>

            <div className="remediation-terminal" onClick={() => handleCopyCommand(adv.actionText)}>
              <span>{termLabel}</span>
              <code>{adv.actionText}</code>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function BenchmarkCard({ benchmark }) {
  const maxVal = Math.max(...benchmark.methods.map(m => m.value), 1);

  return (
    <article className="benchmark-card glass" style={{ minHeight: "20rem" }}>
      <PanelHeading title={benchmark.metric} subtitle={`Measured in ${benchmark.unit}`} />

      <div className="benchmark-bar-list">
        {benchmark.methods.map((method, idx) => {
          const isHexAI = method.name.toLowerCase().includes("hex ai");

          let widthPercent = 0;
          if (benchmark.lowerIsBetter) {
            widthPercent = method.value > 0 ? (maxVal / method.value) * 10 : 100;
            widthPercent = Math.min(100, Math.max(5, widthPercent));
          } else {
            widthPercent = (method.value / maxVal) * 100;
          }

          return (
            <div className="benchmark-bar-row" key={idx}>
              <span className={`benchmark-method-name ${isHexAI ? "highlight" : ""}`}>
                {method.name}
              </span>
              <div className="benchmark-bar-track">
                <div
                  className="benchmark-bar-fill"
                  style={{
                    width: `${widthPercent}%`,
                    background: isHexAI ? "linear-gradient(90deg, var(--accent), var(--accent-strong))" : "rgba(255, 255, 255, 0.12)"
                  }}
                />
              </div>
              <span className={`benchmark-value ${isHexAI ? "highlight" : ""}`}>
                {method.value}
              </span>
            </div>
          );
        })}
      </div>
    </article>
  );
}

function PanelHeading({ title, subtitle }) {
  return (
    <div className="panel-heading">
      <div>
        <h2>{title}</h2>
        <p style={{ textAlign: "left" }}>{subtitle}</p>
      </div>
    </div>
  );
}

function Detail({ label, value }) {
  return (
    <div>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function RiskBar({ value }) {
  return (
    <div className="risk-bar" aria-label={`Risk score ${value}`}>
      <span style={{ width: `${Math.min(value, 100)}%` }} />
      <strong>{value}</strong>
    </div>
  );
}

function ModeButton({ mode, title, desc, activeMode, setMode }) {
  return (
    <button
      type="button"
      className={`mode-option ${activeMode === mode ? "active" : ""}`}
      onClick={() => setMode(mode)}
      style={{ display: "block", height: "auto", boxShadow: "none" }}
    >
      <strong>{title}</strong>
      <p>{desc}</p>
    </button>
  );
}

const rootElement = document.getElementById("root");
const root = window.__hexAiRoot ?? createRoot(rootElement);
window.__hexAiRoot = root;
root.render(<App />);
