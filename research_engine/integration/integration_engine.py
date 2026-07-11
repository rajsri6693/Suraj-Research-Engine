"""
Integration Engine

Implements IntegrationEngine, which connects the completed Research
Engine components into one end-to-end execution pipeline, per
project_documentation/RESEARCH_WORKFLOW.md, RESEARCH_PLANNER.md,
RESEARCH_RESULT_ASSEMBLY.md, KNOWLEDGE_VERIFICATION.md,
HUMAN_REVIEW.md, and RESEARCH_SESSION.md:

Research Planner -> Research Workflow -> Collector Factory ->
Collector Registry -> Collectors -> Research Result Assembly ->
Knowledge Verification -> Human Review

It does NOT call any live API, does NOT access the internet, does NOT
generate scripts or videos, and does NOT write to any database -- every
collector still returns placeholder/mock data exactly as each was
implemented in isolation; this phase only wires already-built
components together into one run.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional, Type

from research_engine.assembly.collector_result import (
    CollectorResult as AssemblyCollectorResult,
)
from research_engine.assembly.collector_result import (
    CollectorStatus as AssemblyCollectorStatus,
)
from research_engine.assembly.research_package import ResearchPackage
from research_engine.assembly.result_assembly import ResearchResultAssembly
from research_engine.chart.chart_generator import ChartGenerator, GeneratedChart
from research_engine.collectors.base_collector import BaseCollector
from research_engine.collectors.collector_factory import CollectorFactory
from research_engine.collectors.collector_registry import CollectorRegistry
from research_engine.collectors.company.company_collector import CompanyCollector
from research_engine.collectors.competitors.competitors_collector import (
    CompetitorsCollector,
)
from research_engine.collectors.corporate_actions.corporate_action_collector import (
    CorporateActionCollector,
)
from research_engine.collectors.financial.financial_collector import (
    FinancialCollector,
)
from research_engine.collectors.government_policy.government_policy_collector import (
    GovernmentPolicyCollector,
)
from research_engine.collectors.historical_price.historical_price_collector import (
    HistoricalPriceCollector,
)
from research_engine.collectors.management.management_collector import (
    ManagementCollector,
)
from research_engine.collectors.market_news.market_news_collector import (
    MarketNewsCollector,
)
from research_engine.collectors.metadata.metadata_collector import MetadataCollector
from research_engine.collectors.orders_contracts.orders_contracts_collector import (
    OrdersContractsCollector,
)
from research_engine.collectors.products_services.products_services_collector import (
    ProductsServicesCollector,
)
from research_engine.collectors.risks.risks_collector import RisksCollector
from research_engine.collectors.sector.sector_collector import SectorCollector
from research_engine.collectors.shareholding.shareholding_collector import (
    ShareholdingCollector,
)
from research_engine.collectors.sources.sources_collector import SourcesCollector
from research_engine.collectors.technical_analysis.technical_analysis_collector import (
    TechnicalAnalysisCollector,
)
from research_engine.planner.research_plan import KnowledgeSection, ResearchPlan
from research_engine.review.human_review import HumanReview
from research_engine.review.review_result import ReviewResult
from research_engine.session.research_session import ResearchSession
from research_engine.session.session_manager import SessionManager
from research_engine.verification.knowledge_verifier import KnowledgeVerifier
from research_engine.verification.verification_report import VerificationReport
from research_engine.workflow.research_workflow import ResearchWorkflow
from research_engine.workflow.workflow_state import WorkflowState

from .review_package import HumanReviewPackage, ReviewPackageStatus

# Every Knowledge Section this integration has a real collector for, per
# RESEARCH_COLLECTORS.md's one-collector-per-section model. A required
# Knowledge Section absent from this map has no collector registered --
# Research Result Assembly correctly reports it as Missing, per
# RESEARCH_RESULT_ASSEMBLY.md Section 6, rather than this engine
# fabricating a result for it.
_KNOWN_COLLECTORS: Dict[str, Type[BaseCollector]] = {
    "Company Information": CompanyCollector,
    "Financial Information": FinancialCollector,
    "Market News": MarketNewsCollector,
    "Sector Information": SectorCollector,
    "Technical Analysis": TechnicalAnalysisCollector,
    "Government Policies": GovernmentPolicyCollector,
    "Historical Price (OHLC)": HistoricalPriceCollector,
    "Corporate Actions": CorporateActionCollector,
    "Orders & Contracts": OrdersContractsCollector,
    "Competitors": CompetitorsCollector,
    "Management": ManagementCollector,
    "Shareholding": ShareholdingCollector,
    "Risks": RisksCollector,
    "Products & Services": ProductsServicesCollector,
    "Sources": SourcesCollector,
    "Metadata": MetadataCollector,
}


@dataclass
class IntegrationResult:
    """The final outcome of one end-to-end Integration Engine run,
    carrying the artifact produced by every stage of the pipeline.

    review_package is the complete Human Review Package assembled once
    Knowledge Verification completes, per IMP-09B; human_review_package
    is the ReviewResult the existing Human Review module produced from
    it -- two distinct artifacts kept as two distinct fields, matching
    HUMAN_REVIEW.md's own separation between what is handed to review
    and what a reviewer decides.

    generated_chart is the chart-ready data Chart Generator produced,
    per IMP-09D -- present only when research_plan.chart_required is
    True; None whenever the Research Plan carried no chart request,
    since Chart Generator never runs in that case.
    """

    research_session: ResearchSession
    workflow_state: WorkflowState
    research_package: ResearchPackage
    verification_report: VerificationReport
    review_package: HumanReviewPackage
    human_review_package: ReviewResult
    generated_chart: Optional[GeneratedChart] = None


class IntegrationEngine:
    """Connects a Research Plan through Research Workflow, Collectors,
    Research Result Assembly, Knowledge Verification, and Human Review
    into one pipeline run.

    Owns one SessionManager, one CollectorRegistry (pre-populated with
    every known real collector unless `registry`/`factory` override it),
    and one CollectorFactory across however many times run() is called;
    a fresh ResearchWorkflow is created for each run, since a workflow
    tracks exactly one Research Session's pass, per RESEARCH_WORKFLOW.md.

    `registry` and `factory` are optional, additive constructor
    parameters -- every existing caller that constructs
    `IntegrationEngine()` with no arguments keeps building the exact
    same zero-arg, placeholder-only collectors as before, unchanged.
    They exist so a production runtime can inject a CollectorRegistry
    whose collectors are bound to a live APIManager (a construction
    detail no collector's own source, and no other part of this class,
    needs to know about), without that runtime needing to re-implement
    run()'s own orchestration -- see research.py at the repository
    root. Passing `factory` alone (its own registry already built) is
    equally valid; passing `registry` alone builds a CollectorFactory
    from it the same way the zero-arg path already does.
    """

    def __init__(
        self,
        registry: Optional[CollectorRegistry] = None,
        factory: Optional[CollectorFactory] = None,
    ) -> None:
        self._session_manager = SessionManager()
        if registry is not None:
            self._registry = registry
        else:
            self._registry = CollectorRegistry()
            for section_name, collector_class in _KNOWN_COLLECTORS.items():
                self._registry.register_collector(section_name, collector_class)
        self._factory = factory if factory is not None else CollectorFactory(self._registry)
        self._assembly = ResearchResultAssembly()
        self._verifier = KnowledgeVerifier()
        self._human_review = HumanReview()
        self._chart_generator = ChartGenerator()

    def run(self, research_plan: ResearchPlan) -> IntegrationResult:
        """Execute the full pipeline for one Research Plan.

        1. Receive ResearchPlan -- `research_plan` is this method's input.
        2. Create Research Session.
        3. Determine required collectors.
        4. Execute collectors in workflow order.
        5. Collect all Collector Results.
        6. Generate Research Package.
        7. Run Knowledge Verification.
        8. Produce Human Review Package.
        9. Return final Integration Result.
        """
        session = self._create_research_session(research_plan)

        workflow = ResearchWorkflow()
        workflow.start_workflow(session, research_plan)  # Stage 1

        workflow.advance_stage()  # Stage 2 - Identify Required Collectors
        workflow.advance_stage()  # Stage 3 - Run Collectors in Parallel
        assembly_results = self._execute_collectors(workflow, research_plan)

        workflow.advance_stage()  # Stage 4 - Collect Results
        workflow.advance_stage()  # Stage 5 - Research Result Assembly
        research_package = self._assembly.create_research_package(
            assembly_results, session, research_plan
        )

        workflow.move_to_verification()  # Stage 6 - Verification
        verification_report = self._verifier.verify_research_package(
            research_package
        )

        # When chart_required=True: Historical Price Collector ->
        # Technical Analysis Collector -> Chart Generator -> Research
        # Package, per IMP-09D. Otherwise Chart Generator is skipped
        # completely and generated_chart stays None.
        generated_chart = (
            self._generate_chart(research_plan)
            if research_plan.chart_required
            else None
        )

        # When Verification completes: create the Human Review Package,
        # populated with everything the Human Review layer needs, per
        # IMP-09B, including chart data per IMP-09D.
        review_package = self._create_human_review_package(
            session,
            research_plan,
            research_package,
            verification_report,
            generated_chart,
        )

        workflow.advance_stage()  # Stage 7 - Knowledge Storage
        workflow.advance_stage()  # Stage 8 - Knowledge Viewer
        workflow.advance_stage()  # Stage 9 - Ready for Human Review

        # Pass the package to the existing Human Review module.
        human_review_package = self._human_review.review_verification_report(
            review_package.verification_report
        )

        return IntegrationResult(
            research_session=session,
            workflow_state=workflow.state,
            research_package=research_package,
            verification_report=verification_report,
            review_package=review_package,
            human_review_package=human_review_package,
            generated_chart=generated_chart,
        )

    def _create_research_session(self, research_plan: ResearchPlan) -> ResearchSession:
        """Create Research Session, per RESEARCH_SESSION.md, restated
        from the Research Plan's own restated Research Input."""
        return self._session_manager.create_session(
            research_topic=research_plan.research_topic,
            research_profile=", ".join(research_plan.research_profile),
            research_category=research_plan.research_category.value,
        )

    def _create_human_review_package(
        self,
        session: ResearchSession,
        research_plan: ResearchPlan,
        research_package: ResearchPackage,
        verification_report: VerificationReport,
        generated_chart: Optional[GeneratedChart],
    ) -> HumanReviewPackage:
        """Create Human Review Package.

        Populates Research Session, Research Plan, Research Package,
        Verification Report, Review Status, and Eligible Sections, per
        IMP-09B. Eligible Sections mirrors the Verification Report's own
        Verified Sections -- only Verified sections are ever eligible
        for Human Review, per HUMAN_REVIEW.md Section 5.

        Chart Available, Chart Type, and Chart Dataset are derived from
        `generated_chart`, per IMP-09D -- Chart Available is False and
        the other two are None whenever Chart Generator did not run.
        """
        return HumanReviewPackage(
            research_session=session,
            research_plan=research_plan,
            research_package=research_package,
            verification_report=verification_report,
            review_status=ReviewPackageStatus.PENDING_REVIEW,
            eligible_sections=list(verification_report.verified_sections),
            chart_available=generated_chart is not None,
            chart_type=generated_chart.chart_type if generated_chart else None,
            chart_dataset=generated_chart.price_dataset if generated_chart else None,
        )

    def _generate_chart(self, research_plan: ResearchPlan) -> GeneratedChart:
        """Run Historical Price Collector -> Technical Analysis
        Collector -> Chart Generator, per IMP-09D, when
        research_plan.chart_required is True.

        Both collectors now come from this engine's own CollectorFactory
        (`self._factory.create_collector(...)`) rather than being
        constructed directly -- with the default, zero-arg registry
        this is byte-identical to the direct construction it replaces
        (the same classes, the same zero constructor arguments), but it
        additionally means a caller who injected a live-APIManager-bound
        registry (per this class's own __init__ docstring) gets live
        chart data too, instead of chart generation silently staying on
        placeholder data forever regardless of that injection. Runs
        independent of whether Historical Price/Technical Analysis are
        also part of required_knowledge_sections -- since a chart
        request always needs both collectors' data regardless of which
        Knowledge Sections this Research Plan otherwise requires.
        """
        historical_price_result = self._factory.create_collector(
            "Historical Price (OHLC)"
        ).collect(research_plan.research_topic)
        technical_analysis_result = self._factory.create_collector("Technical Analysis").collect(
            research_plan.research_topic
        )
        return self._chart_generator.generate(
            historical_price_result, technical_analysis_result
        )

    def _execute_collectors(
        self, workflow: ResearchWorkflow, research_plan: ResearchPlan
    ) -> List[AssemblyCollectorResult]:
        """Determine required collectors and execute them in Research
        Workflow order (Stage 3), per RESEARCH_WORKFLOW.md's Collector
        Execution Rules -- one collector's failure never stops the
        others, whether it reports Failed itself or raises unexpectedly.
        """
        results: List[AssemblyCollectorResult] = []
        for section in research_plan.required_knowledge_sections:
            section_name = section.value
            if not self._factory.is_available(section_name):
                continue  # No collector registered; Assembly reports Missing.

            workflow.register_collector(section)
            collector = self._factory.create_collector(section_name)
            try:
                domain_result = collector.collect(research_plan.research_topic)
            except Exception:
                workflow.mark_collector_failed(section)
                continue

            if domain_result.collector_status.value == "Failed":
                workflow.mark_collector_failed(section)
                continue

            workflow.mark_collector_complete(section)
            results.append(
                self._adapt_to_assembly_result(section, collector, domain_result)
            )
        return results

    def _adapt_to_assembly_result(
        self,
        section: KnowledgeSection,
        collector: BaseCollector,
        domain_result: object,
    ) -> AssemblyCollectorResult:
        """Translate one real collector's own richly-typed Result object
        into the generic CollectorResult shape Research Result Assembly
        consumes.

        Each real collector under research_engine.collectors defines its
        own domain-specific dataclass (CompanyResult, FinancialResult,
        and so on) and its own local CollectorStatus enum, per each
        collector's own source-of-truth scoping -- this is the one place
        those sixteen different shapes converge into the single shape
        Assembly understands. collected_knowledge is the domain result's
        own str() rendering: this phase validates architecture and
        wiring, not presentation, so no bespoke per-collector formatting
        is introduced here.
        """
        return AssemblyCollectorResult(
            collector_name=collector.collector_name,
            knowledge_section=section,
            collected_knowledge=str(domain_result),
            sources=list(domain_result.sources),
            collection_time=domain_result.collection_time,
            collector_status=AssemblyCollectorStatus(
                domain_result.collector_status.value
            ),
        )
