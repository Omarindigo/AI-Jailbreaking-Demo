"""
Jailbreaking Large AI Models - Interactive Demo
Computational Media | Assignment #4 | Spring 2026

Run: shiny run app.py
"""

from shiny import App, ui, render, reactive
import os
from dotenv import load_dotenv
load_dotenv()

from config import DIRECT_REQUESTS, JAILBREAK_TEMPLATES
from models import MODEL_REGISTRY, query_model


def card_box(title, content, border_color, bg_color):
    """Build a styled card for displaying prompt/response pairs."""
    return ui.div(
        ui.h4(title, style=f"margin:0 0 8px 0; font-size:1.1em; color:{border_color};"),
        ui.pre(
            content if content else "Waiting...",
            style="white-space:pre-wrap; word-wrap:break-word; margin:0; padding:12px; background:#f8f9fa; border-radius:6px; font-size:0.82em; max-height:300px; overflow-y:auto; font-family:'Courier New',monospace;"
        ),
        style=f"border-left:4px solid {border_color}; background:{bg_color}; padding:14px; border-radius:6px; margin-bottom:14px;",
    )


GLOBAL_CSS = """
body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 20px; background: #fafafa; color: #222; }
.btn-primary { background-color: #0d6efd; border-color: #0d6efd; color: white; padding: 10px 20px; }
.btn-danger { background-color: #dc3545; border-color: #dc3545; color: white; padding: 10px 20px; }
select.form-select { padding: 8px; }
label { font-weight: 600; margin-bottom: 4px; }
"""

app_ui = ui.page_fluid(
    ui.tags.style(GLOBAL_CSS),

    ui.h1("AI Jailbreaking Demo: System Override Probes"),

    ui.card(
        ui.p(
            "This app demonstrates jailbreaking as a diagnostic tool for probing LLM safety behavior. "
            "Three cybersecurity-related requests are tested in raw form and wrapped inside system override jailbreak probes, "
            "across multiple language models."
        ),
        style="background:#e8f4f8; color:#333; margin-bottom:18px;"
    ),

    # Controls panel
    ui.card(
        ui.row(
            ui.column(3, ui.input_select("provider", "LLM Provider:", choices=list(MODEL_REGISTRY.keys()))),
            ui.column(3, ui.input_select("template", "Jailbreak Template:", choices=list(JAILBREAK_TEMPLATES.keys()))),
            ui.column(3, ui.input_select("probe_id", "Select Probe:", choices=[str(r["id"]) for r in DIRECT_REQUESTS], selected="1")),
            ui.column(3,
                ui.input_action_button("run_single", "Run Single Probe", class_="btn-primary", style="width:100%; margin-bottom:8px;"),
                ui.input_action_button("run_all", "Run All 3 Probes", class_="btn-danger", style="width:100%;"),
            ),
        ),
        style="background:#f5f5f5; margin-bottom:18px;"
    ),

    # Status indicator
    ui.output_ui("status_bar"),

    # Results area
    ui.output_ui("results_area"),
)


def server(input, output, session):
    # Reactive values
    results = reactive.value([])
    is_running = reactive.value(False)
    status_msg = reactive.value("Ready - select a probe and click Run")

    @reactive.effect
    @reactive.event(input.run_single)
    def run_single_probe():
        is_running.set(True)
        status_msg.set("Running probe...")

        probe = next(r for r in DIRECT_REQUESTS if r["id"] == int(input.probe_id()))
        template_name = input.template()
        template_text = JAILBREAK_TEMPLATES[template_name]
        provider = input.provider()

        direct_resp = ""
        jailbreak_resp = ""

        try:
            status_msg.set(f"Querying {provider} (direct)...")
            direct_resp = query_model(provider, probe["prompt"])
        except Exception as e:
            direct_resp = f"Error: {type(e).__name__}: {e}"

        try:
            status_msg.set(f"Querying {provider} (jailbreak)...")
            jailbreak_prompt = template_text.format(request=probe["prompt"])
            jailbreak_resp = query_model(provider, jailbreak_prompt)
        except Exception as e:
            jailbreak_resp = f"Error: {type(e).__name__}: {e}"

        results.set([{
            "id": probe["id"],
            "category": probe["category"],
            "provider": provider,
            "template": template_name,
            "direct_prompt": probe["prompt"],
            "jailbreak_prompt": jailbreak_prompt,
            "direct_response": direct_resp,
            "jailbreak_response": jailbreak_resp,
        }])

        status_msg.set("Done!")
        is_running.set(False)

    @reactive.effect
    @reactive.event(input.run_all)
    def run_all_probes():
        is_running.set(True)
        template_name = input.template()
        template_text = JAILBREAK_TEMPLATES[template_name]
        provider = input.provider()

        all_results = []

        for i, probe in enumerate(DIRECT_REQUESTS):
            status_msg.set(f"[{i+1}/3] Querying {provider}: {probe['category']} (direct)...")

            direct_resp = ""
            jailbreak_resp = ""

            try:
                direct_resp = query_model(provider, probe["prompt"])
            except Exception as e:
                direct_resp = f"Error: {type(e).__name__}: {e}"

            status_msg.set(f"[{i+1}/3] Querying {provider}: {probe['category']} (jailbreak)...")

            try:
                jailbreak_prompt = template_text.format(request=probe["prompt"])
                jailbreak_resp = query_model(provider, jailbreak_prompt)
            except Exception as e:
                jailbreak_resp = f"Error: {type(e).__name__}: {e}"

            all_results.append({
                "id": probe["id"],
                "category": probe["category"],
                "provider": provider,
                "template": template_name,
                "direct_prompt": probe["prompt"],
                "jailbreak_prompt": jailbreak_prompt,
                "direct_response": direct_resp,
                "jailbreak_response": jailbreak_resp,
            })

        results.set(all_results)
        status_msg.set("All 3 probes complete!")
        is_running.set(False)

    @output
    @render.ui
    def status_bar():
        dot = "🟡" if is_running.get() else "🟢"
        return ui.div(
            ui.span(f"{dot} {status_msg.get()}", style="font-weight:bold; font-size:0.95em;"),
            style="margin-bottom:14px;"
        )

    @output
    @render.ui
    def results_area():
        res_list = results.get()
        if not res_list:
            return ui.card(
                ui.p("No results yet. Select a probe and click Run.", style="color:#666; font-style:italic;")
            )

        cards = []
        for res in res_list:
            cards.append(
                ui.card(
                    ui.h3(f"Probe {res['id']}: {res['category']}"),
                    ui.p(f"Provider: {res['provider']}  |  Template: {res['template']}", style="color:#555;"),
                    card_box("DIRECT REQUEST (what normally gets blocked)", res.get("direct_response", ""), "#dc3545", "#fff5f5"),
                    card_box("JAILBREAK REQUEST (system override wrapper)", res.get("jailbreak_response", ""), "#0d6efd", "#f0f4ff"),
                )
            )

        return ui.div(*cards)


app = App(app_ui, server)
