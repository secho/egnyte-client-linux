export default function Home() {
  const highlights = [
    {
      title: "Native Egnyte plugin",
      description:
        "Authenticate once and browse Egnyte spaces directly inside ComfyUI. Search, preview, and fetch assets with version awareness.",
    },
    {
      title: "Custom Egnyte node",
      description:
        "Drop a dedicated node into any graph to pull inputs and publish outputs back to Egnyte with metadata, tags, and project context.",
    },
    {
      title: "Enterprise ready",
      description:
        "Respect existing permissions, audit trails, and retention policies. Keep creative pipelines aligned with Egnyte governance.",
    },
  ];

  const featureGroups = [
    {
      title: "Asset discovery",
      items: [
        "Browse spaces, folders, and shared links",
        "Search by name, tag, or project label",
        "Preview versions before pulling to the canvas",
      ],
    },
    {
      title: "Workflow acceleration",
      items: [
        "Cache assets locally with smart invalidation",
        "Pin favorites and reuse across pipelines",
        "Batch pull or push with one node trigger",
      ],
    },
    {
      title: "Delivery and approvals",
      items: [
        "Publish renders back to Egnyte automatically",
        "Attach run metadata and checkpoints",
        "Notify reviewers with links to outputs",
      ],
    },
  ];

  const workflow = [
    {
      step: "1",
      title: "Connect Egnyte",
      description:
        "Secure OAuth sign-in and policy-aware access to the right spaces.",
    },
    {
      step: "2",
      title: "Drag the Egnyte node",
      description:
        "Select assets, set destination folders, and map fields to prompts.",
    },
    {
      step: "3",
      title: "Run ComfyUI",
      description:
        "Generate, iterate, and publish outputs with automatic versioning.",
    },
    {
      step: "4",
      title: "Review and share",
      description:
        "Stakeholders review in Egnyte with approvals and audit history.",
    },
  ];

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="sticky top-0 z-20 border-b border-slate-200/70 bg-white/80 backdrop-blur">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-slate-900 text-sm font-semibold text-white">
              E
            </div>
            <div>
              <p className="text-sm font-semibold">Egnyte for ComfyUI</p>
              <p className="text-xs text-slate-500">
                Native plugin + custom node
              </p>
            </div>
          </div>
          <nav className="hidden items-center gap-6 text-sm text-slate-600 md:flex">
            <a className="hover:text-slate-900" href="#overview">
              Overview
            </a>
            <a className="hover:text-slate-900" href="#features">
              Features
            </a>
            <a className="hover:text-slate-900" href="#workflow">
              Workflow
            </a>
            <a className="hover:text-slate-900" href="#security">
              Security
            </a>
          </nav>
          <a
            className="hidden items-center justify-center rounded-full bg-slate-900 px-5 py-2 text-sm font-semibold text-white transition hover:bg-slate-800 md:inline-flex"
            href="#contact"
          >
            Request demo
          </a>
        </div>
      </header>

      <main>
        <section id="overview" className="px-6 py-16 md:py-24">
          <div className="mx-auto grid max-w-6xl items-center gap-12 lg:grid-cols-[1.2fr_1fr]">
            <div>
              <span className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-white px-4 py-1 text-xs font-semibold uppercase tracking-wide text-slate-500">
                Native Egnyte plugin + custom ComfyUI node
              </span>
              <h1 className="mt-5 text-4xl font-semibold tracking-tight text-slate-900 sm:text-5xl">
                Bring secure Egnyte assets into ComfyUI pipelines without
                friction.
              </h1>
              <p className="mt-5 text-lg leading-8 text-slate-600">
                Connect your Egnyte content library to ComfyUI and move from
                search to generation in seconds. The native plugin keeps assets
                synced and governed, while the custom node makes ingestion and
                delivery repeatable inside every graph.
              </p>
              <div className="mt-8 flex flex-col gap-3 sm:flex-row">
                <a
                  className="inline-flex items-center justify-center rounded-full bg-slate-900 px-6 py-3 text-sm font-semibold text-white transition hover:bg-slate-800"
                  href="#contact"
                >
                  Get a demo
                </a>
                <a
                  className="inline-flex items-center justify-center rounded-full border border-slate-300 bg-white px-6 py-3 text-sm font-semibold text-slate-700 transition hover:border-slate-400 hover:text-slate-900"
                  href="#features"
                >
                  View capabilities
                </a>
              </div>
              <div className="mt-8 flex flex-wrap gap-6 text-xs font-semibold uppercase tracking-wide text-slate-500">
                <span>SSO ready</span>
                <span>Audit trails</span>
                <span>Version aware</span>
                <span>Policy aligned</span>
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <div className="flex items-center justify-between">
                <p className="text-sm font-semibold">Egnyte Vault</p>
                <span className="text-xs text-slate-500">Live connection</span>
              </div>
              <div className="mt-6 grid gap-4">
                <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Input assets
                  </p>
                  <div className="mt-3 space-y-2 text-sm text-slate-700">
                    <div className="flex items-center justify-between rounded-lg bg-white px-3 py-2">
                      <span>Brand kit / 2026</span>
                      <span className="text-xs text-slate-500">Synced</span>
                    </div>
                    <div className="flex items-center justify-between rounded-lg bg-white px-3 py-2">
                      <span>Product shots / HD</span>
                      <span className="text-xs text-slate-500">Pinned</span>
                    </div>
                    <div className="flex items-center justify-between rounded-lg bg-white px-3 py-2">
                      <span>Campaign refs</span>
                      <span className="text-xs text-slate-500">v3</span>
                    </div>
                  </div>
                </div>
                <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                    ComfyUI output
                  </p>
                  <div className="mt-3 space-y-2 text-sm text-slate-700">
                    <div className="flex items-center justify-between rounded-lg bg-white px-3 py-2">
                      <span>Render batch / A</span>
                      <span className="text-xs text-slate-500">Published</span>
                    </div>
                    <div className="flex items-center justify-between rounded-lg bg-white px-3 py-2">
                      <span>Final selects</span>
                      <span className="text-xs text-slate-500">Shared</span>
                    </div>
                  </div>
                </div>
                <div className="rounded-xl border border-slate-200 bg-white p-4 text-sm text-slate-600">
                  Custom node keeps every run tied to the Egnyte project record
                  with auto-tagging and audit metadata.
                </div>
              </div>
            </div>
          </div>
        </section>

        <section
          id="features"
          className="border-t border-slate-200/80 bg-white px-6 py-16"
        >
          <div className="mx-auto max-w-6xl">
            <div className="flex flex-col gap-3">
              <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Product highlights
              </span>
              <h2 className="text-3xl font-semibold text-slate-900">
                Designed for modern AI production teams.
              </h2>
              <p className="max-w-2xl text-base leading-7 text-slate-600">
                The plugin and custom node combine file governance with
                repeatable AI workflows, so teams can move fast without losing
                control of creative assets.
              </p>
            </div>

            <div className="mt-10 grid gap-6 md:grid-cols-3">
              {highlights.map((item) => (
                <div
                  key={item.title}
                  className="rounded-2xl border border-slate-200 bg-slate-50 p-6"
                >
                  <h3 className="text-lg font-semibold text-slate-900">
                    {item.title}
                  </h3>
                  <p className="mt-3 text-sm leading-6 text-slate-600">
                    {item.description}
                  </p>
                </div>
              ))}
            </div>

            <div className="mt-12 grid gap-8 lg:grid-cols-3">
              {featureGroups.map((group) => (
                <div
                  key={group.title}
                  className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm"
                >
                  <h3 className="text-base font-semibold text-slate-900">
                    {group.title}
                  </h3>
                  <ul className="mt-4 space-y-3 text-sm text-slate-600">
                    {group.items.map((item) => (
                      <li
                        key={item}
                        className="flex items-start gap-3 rounded-lg bg-slate-50 px-3 py-2"
                      >
                        <span className="mt-1 h-2 w-2 rounded-full bg-slate-400" />
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section id="workflow" className="px-6 py-16">
          <div className="mx-auto grid max-w-6xl gap-12 lg:grid-cols-[1fr_1.1fr]">
            <div>
              <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Workflow
              </span>
              <h2 className="mt-3 text-3xl font-semibold text-slate-900">
                A repeatable path from vault to canvas.
              </h2>
              <p className="mt-4 text-base leading-7 text-slate-600">
                The native plugin keeps your Egnyte library close, while the
                custom node handles ingest and publish steps. Every graph run
                stays linked to the source files and the teams who approved
                them.
              </p>
              <div className="mt-8 space-y-4">
                {workflow.map((step) => (
                  <div
                    key={step.step}
                    className="flex gap-4 rounded-2xl border border-slate-200 bg-white p-4 shadow-sm"
                  >
                    <div className="flex h-10 w-10 items-center justify-center rounded-full bg-slate-900 text-sm font-semibold text-white">
                      {step.step}
                    </div>
                    <div>
                      <h3 className="text-base font-semibold text-slate-900">
                        {step.title}
                      </h3>
                      <p className="mt-1 text-sm text-slate-600">
                        {step.description}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
              <div className="flex items-center justify-between">
                <p className="text-sm font-semibold text-slate-900">
                  Egnyte Node Spec
                </p>
                <span className="text-xs text-slate-500">Custom module</span>
              </div>
              <div className="mt-6 space-y-4 text-sm text-slate-600">
                <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Inputs
                  </p>
                  <ul className="mt-3 space-y-2">
                    <li>Egnyte folder path</li>
                    <li>Asset selector and tag filter</li>
                    <li>Prompt bindings</li>
                  </ul>
                </div>
                <div className="rounded-xl border border-slate-200 bg-slate-50 p-4">
                  <p className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                    Outputs
                  </p>
                  <ul className="mt-3 space-y-2">
                    <li>Destination project folder</li>
                    <li>Version notes and run metadata</li>
                    <li>Reviewer notification hooks</li>
                  </ul>
                </div>
                <div className="rounded-xl border border-slate-200 bg-white p-4">
                  Built for teams running multiple models, render passes, and
                  approval cycles.
                </div>
              </div>
            </div>
          </div>
        </section>

        <section
          id="security"
          className="border-t border-slate-200/80 bg-white px-6 py-16"
        >
          <div className="mx-auto grid max-w-6xl gap-10 md:grid-cols-2">
            <div>
              <span className="text-xs font-semibold uppercase tracking-wide text-slate-500">
                Security and governance
              </span>
              <h2 className="mt-3 text-3xl font-semibold text-slate-900">
                Egnyte-grade control, ComfyUI velocity.
              </h2>
              <p className="mt-4 text-base leading-7 text-slate-600">
                Keep your AI workflows aligned with enterprise policies. The
                integration honors permissions and data residency while giving
                creators fast, local access to what they need.
              </p>
            </div>
            <div className="grid gap-4">
              {[
                "Fine-grained access mapped from Egnyte roles",
                "Audit logs for every asset pull and publish action",
                "Retention policies enforced on generated outputs",
                "Optional approvals before output is shared",
                "Admin dashboards with usage and storage insights",
              ].map((item) => (
                <div
                  key={item}
                  className="rounded-2xl border border-slate-200 bg-slate-50 p-4 text-sm text-slate-600"
                >
                  {item}
                </div>
              ))}
            </div>
          </div>
        </section>

        <section id="contact" className="px-6 py-16">
          <div className="mx-auto max-w-6xl rounded-2xl bg-slate-900 px-8 py-12 text-white sm:px-12">
            <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
              <div>
                <p className="text-xs font-semibold uppercase tracking-wide text-slate-300">
                  Ready to connect Egnyte and ComfyUI?
                </p>
                <h2 className="mt-3 text-3xl font-semibold">
                  Launch governed AI workflows faster.
                </h2>
                <p className="mt-3 max-w-xl text-sm text-slate-200">
                  Get a tailored demo, onboarding plan, and a custom node
                  package that fits your production pipeline.
                </p>
              </div>
              <div className="flex flex-col gap-3 sm:flex-row">
                <a
                  className="inline-flex items-center justify-center rounded-full bg-white px-6 py-3 text-sm font-semibold text-slate-900 transition hover:bg-slate-100"
                  href="mailto:partners@egnyte.com"
                >
                  Contact sales
                </a>
                <a
                  className="inline-flex items-center justify-center rounded-full border border-white/30 px-6 py-3 text-sm font-semibold text-white transition hover:border-white"
                  href="#overview"
                >
                  View overview
                </a>
              </div>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-slate-200 bg-white px-6 py-8 text-sm text-slate-500">
        <div className="mx-auto flex max-w-6xl flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <div className="flex items-center gap-2 font-semibold text-slate-700">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-slate-900 text-xs font-semibold text-white">
              E
            </span>
            Egnyte for ComfyUI
          </div>
          <div className="flex flex-wrap gap-6 text-xs uppercase tracking-wide">
            <span>Native plugin</span>
            <span>Custom node</span>
            <span>ComfyUI</span>
            <span>Egnyte</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
