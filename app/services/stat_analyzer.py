import numpy as np

class StatAnalyzer:
    @staticmethod
    def is_significant(curr_scores: list[float], base_scores: list[float]) -> bool:
        if not curr_scores or not base_scores:
            return False
            
        # Basic implementation of Welch's t-test (simplified)
        curr_mean = np.mean(curr_scores)
        base_mean = np.mean(base_scores)
        curr_var = np.var(curr_scores, ddof=1) if len(curr_scores) > 1 else 0
        base_var = np.var(base_scores, ddof=1) if len(base_scores) > 1 else 0
        
        if curr_var == 0 and base_var == 0:
            return curr_mean != base_mean
            
        t_stat = (curr_mean - base_mean) / np.sqrt((curr_var / len(curr_scores)) + (base_var / len(base_scores)))
        
        # Simple threshold check for significance (|t| > 1.96 for roughly 95% confidence)
        return abs(t_stat) > 1.96
