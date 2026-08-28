import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.eval_run import EvalRun
from app.models.eval_result import EvalResult
from app.models.prompt_config import PromptConfig
from app.services.llm_runner import LLMRunner
from app.services.judge_scorer import JudgeScorer
from app.services.dataset_loader import DatasetLoader
from app.services.prompt_loader import PromptLoader
from app.services.drift_engine import DriftEngine
from app.config import settings
from app.db.session import AsyncSessionLocal

logger = logging.getLogger(__name__)

async def execute_eval_run(eval_run_id: str):
    logger.info(f"Starting async eval run for {eval_run_id}")
    
    async with AsyncSessionLocal() as session:
        # Load EvalRun
        eval_run = await session.get(EvalRun, eval_run_id)
        if not eval_run:
            logger.error("EvalRun not found")
            return
            
        prompt_config = await session.get(PromptConfig, eval_run.prompt_config_id)
        
        eval_run.status = "running"
        await session.commit()
        
        try:
            # 1. Load dataset
            dataset_loader = DatasetLoader(settings.GOLDEN_DATASET_DIR)
            datasets = dataset_loader.load_all()
            target_dataset = next((d for d in datasets if d.feature_id == prompt_config.feature_id), None)
            
            if not target_dataset:
                raise ValueError(f"No golden dataset found for feature {prompt_config.feature_id}")

            # 2. Load prompt details
            prompt_loader = PromptLoader(settings.PROMPTS_DIR)
            prompts = prompt_loader.load_all()
            prompt_data = next((p for p in prompts if p.id == prompt_config.feature_id and p.version == prompt_config.version), None)
            
            if not prompt_data:
                raise ValueError("Prompt definition not found")

            runner = LLMRunner(
                model=prompt_data.model,
                temperature=prompt_data.temperature,
                max_tokens=prompt_data.max_tokens,
                system_prompt=prompt_data.system_prompt
            )
            
            judge = JudgeScorer()

            # 3. Execute queries
            inputs = [tc.input for tc in target_dataset.test_cases]
            runner_results = await runner.run_batch(inputs, few_shot_examples=prompt_data.few_shot_examples)
            
            # 4. Prepare judge inputs
            judge_inputs = []
            for tc, r_result in zip(target_dataset.test_cases, runner_results):
                judge_inputs.append({
                    "input": tc.input,
                    "expected_output": tc.expected_output,
                    "actual_output": r_result.get("output", {}) if r_result["status"] == "success" else {}
                })
                
            # 5. Execute judge
            judge_results = await judge.score_batch(judge_inputs)
            
            # 6. Save results
            total_latency = 0
            total_prompt_tokens = 0
            total_completion_tokens = 0
            passed = 0
            
            for tc, r_result, j_result in zip(target_dataset.test_cases, runner_results, judge_results):
                category_match = False
                if r_result["status"] == "success":
                    act_cat = r_result["output"].get("category", "").lower()
                    exp_cat = tc.expected_output.get("category", "").lower()
                    if act_cat and exp_cat and act_cat == exp_cat:
                        category_match = True
                        
                if category_match and j_result["relevance_score"] >= 4:
                    passed += 1

                res_obj = EvalResult(
                    eval_run_id=eval_run.id,
                    test_case_id=tc.id,
                    input=tc.input,
                    expected_output=tc.expected_output,
                    actual_output=r_result.get("output", {}) if r_result["status"] == "success" else {},
                    category_match=category_match,
                    relevance_score=j_result["relevance_score"],
                    latency_ms=r_result.get("latency_ms", 0),
                    prompt_tokens=r_result.get("prompt_tokens", 0),
                    completion_tokens=r_result.get("completion_tokens", 0),
                    status="pass" if (category_match and j_result["relevance_score"] >= 4) else "fail",
                    judge_reasoning=j_result.get("reasoning", "")
                )
                
                total_latency += r_result.get("latency_ms", 0)
                total_prompt_tokens += r_result.get("prompt_tokens", 0)
                total_completion_tokens += r_result.get("completion_tokens", 0)
                
                session.add(res_obj)

            # --- Simulating Experiment Assignments for A/B Testing ---
            # Check if this eval run is for an active experiment variant
            from app.models.experiment import Experiment, ExperimentStatus
            from app.models.experiment_variant import ExperimentVariant
            from app.models.experiment_assignment import ExperimentAssignment
            
            active_exp = await session.execute(
                select(Experiment).where(
                    Experiment.feature_id == prompt_config.feature_id,
                    Experiment.status == ExperimentStatus.RUNNING.value
                ).limit(1)
            )
            experiment = active_exp.scalar_one_or_none()
            if experiment:
                active_var = await session.execute(
                    select(ExperimentVariant).where(
                        ExperimentVariant.experiment_id == experiment.id,
                        ExperimentVariant.prompt_config_id == prompt_config.id
                    ).limit(1)
                )
                variant = active_var.scalar_one_or_none()
                if variant:
                    import hashlib
                    for tc in target_dataset.test_cases:
                        # Create deterministic hash from test case input
                        req_hash = hashlib.sha256(str(tc.input).encode('utf-8')).hexdigest()
                        assignment = ExperimentAssignment(
                            experiment_id=experiment.id,
                            variant_id=variant.id,
                            request_hash=req_hash,
                            eval_run_id=eval_run.id
                        )
                        session.add(assignment)

            total_cases = len(target_dataset.test_cases)
            eval_run.total_cases = total_cases
            eval_run.passed_cases = passed
            eval_run.failed_cases = total_cases - passed
            eval_run.overall_accuracy = passed / total_cases if total_cases > 0 else 0
            eval_run.avg_relevance_score = sum(j["relevance_score"] for j in judge_results) / total_cases if total_cases > 0 else 0
            eval_run.avg_latency_ms = total_latency / total_cases if total_cases > 0 else 0
            eval_run.total_tokens = total_prompt_tokens + total_completion_tokens
            
            eval_run.status = "completed"
            eval_run.completed_at = datetime.utcnow()
            
            # 7. Check Drift
            drift_engine = DriftEngine(session)
            await drift_engine.detect_drift(prompt_config.feature_id, str(eval_run.id))
            
            await session.commit()
            logger.info(f"Eval run {eval_run_id} completed successfully")
            
        except Exception as e:
            logger.exception(f"Eval run failed")
            eval_run.status = "failed"
            eval_run.error_message = str(e)
            await session.commit()
