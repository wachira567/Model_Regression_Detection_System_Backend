import pytest
from app.services.judge_scorer import JudgeScorer
from app.models.prompt_config import PromptConfig

@pytest.mark.asyncio
async def test_deterministic_category_match():
    scorer = JudgeScorer(None)  # No settings needed for deterministic
    
    # Test pass
    result_pass = scorer._check_category_match(
        expected={"category": "billing"}, 
        actual={"category": "billing"}
    )
    assert result_pass is True
    
    # Test fail
    result_fail = scorer._check_category_match(
        expected={"category": "billing"}, 
        actual={"category": "technical"}
    )
    assert result_fail is False
    
    # Test invalid actual
    result_invalid = scorer._check_category_match(
        expected={"category": "billing"}, 
        actual=None
    )
    assert result_invalid is False
