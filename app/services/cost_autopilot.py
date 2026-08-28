import hashlib
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.routing_decision import RoutingDecision

# Mock prices per 1M tokens (Input + Output average for simplicity)
MODEL_COSTS = {
    "gpt-4o": 10.00,
    "claude-3-5-sonnet-20240620": 12.00,
    "gpt-3.5-turbo": 1.00,
    "claude-3-haiku-20240307": 0.50
}

class CostAutopilot:
    def __init__(self, db: AsyncSession):
        self.db = db

    def calculate_complexity(self, prompt: str) -> float:
        """
        Calculates a heuristic complexity score between 0.0 and 1.0
        In production, this would be a trained lightweight classifier.
        """
        if not prompt:
            return 0.0
            
        length = len(prompt)
        # Simple heuristics: long prompts, JSON requests, code blocks indicate complexity
        score = 0.0
        
        if length > 500:
            score += 0.3
        if length > 2000:
            score += 0.2
            
        if "```" in prompt or "def " in prompt or "class " in prompt:
            score += 0.3
            
        if "{" in prompt and "}" in prompt and '"' in prompt:
            score += 0.2 # Likely JSON formatting
            
        return min(1.0, score)

    async def route_request(self, feature_id: str, prompt: str, fallback_model: str = "gpt-4o") -> Dict[str, Any]:
        """
        Routes the request to the cheapest capable model and logs the decision.
        """
        complexity = self.calculate_complexity(prompt)
        
        # Determine routing logic
        if complexity < 0.4:
            routed_model = "claude-3-haiku-20240307"
        elif complexity < 0.7:
            routed_model = "gpt-3.5-turbo"
        else:
            routed_model = fallback_model
            
        # Calculate savings
        # For a real implementation, we'd estimate token count. Here we just use a flat rate per request as a demo.
        # Assuming avg 500 tokens = 0.0005 * 1M
        avg_tokens = max(50, len(prompt) // 4) # rough estimate
        cost_expensive = (avg_tokens / 1_000_000) * MODEL_COSTS.get(fallback_model, 10.0)
        cost_routed = (avg_tokens / 1_000_000) * MODEL_COSTS.get(routed_model, 0.5)
        
        savings = max(0.0, cost_expensive - cost_routed)
        
        # Log decision
        input_hash = hashlib.sha256(prompt.encode()).hexdigest()
        decision = RoutingDecision(
            feature_id=feature_id,
            input_hash=input_hash,
            complexity_score=complexity,
            routed_model=routed_model,
            cost_saved_usd=savings
        )
        
        self.db.add(decision)
        await self.db.commit()
        
        return {
            "routed_model": routed_model,
            "complexity_score": complexity,
            "estimated_savings_usd": savings,
            "decision_id": str(decision.id)
        }
