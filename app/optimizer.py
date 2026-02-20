"""Prompt optimization and tuning engine."""

from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
import json
from loguru import logger


class OptimizationMetric(str, Enum):
    """Metrics for optimization."""
    ACCURACY = "accuracy"
    LATENCY = "latency"
    COST = "cost"
    CONSISTENCY = "consistency"
    RELEVANCE = "relevance"


@dataclass
class PromptVariant:
    """Represents a prompt variant with metrics."""
    prompt: str
    metrics: Dict[str, float]
    model_config: Dict[str, Any]
    version: int
    score: float = 0.0


class PromptOptimizer:
    """Optimizes prompts using various strategies."""
    
    def __init__(self, target_metrics: Optional[List[str]] = None):
        self.target_metrics = target_metrics or [
            OptimizationMetric.ACCURACY.value,
            OptimizationMetric.LATENCY.value,
        ]
        self.variants: List[PromptVariant] = []
        self.best_variant: Optional[PromptVariant] = None
    
    def add_variant(
        self,
        prompt: str,
        metrics: Dict[str, float],
        model_config: Dict[str, Any],
        version: int = 1,
    ) -> PromptVariant:
        """Add a prompt variant for tracking."""
        score = self._calculate_score(metrics)
        variant = PromptVariant(
            prompt=prompt,
            metrics=metrics,
            model_config=model_config,
            version=version,
            score=score,
        )
        self.variants.append(variant)
        
        if self.best_variant is None or variant.score > self.best_variant.score:
            self.best_variant = variant
            logger.info(f"New best variant found with score: {variant.score:.4f}")
        
        return variant
    
    def _calculate_score(self, metrics: Dict[str, float]) -> float:
        """Calculate composite score from metrics."""
        score = 0.0
        weights = self._get_metric_weights()
        
        for metric_name, weight in weights.items():
            if metric_name in metrics:
                value = metrics[metric_name]
                
                # Normalize based on metric type
                if metric_name == OptimizationMetric.LATENCY.value:
                    # Lower latency is better, invert it
                    normalized = 1.0 / (1.0 + value) if value > 0 else 0.0
                elif metric_name == OptimizationMetric.COST.value:
                    # Lower cost is better, invert it
                    normalized = 1.0 / (1.0 + value) if value > 0 else 0.0
                else:
                    # Higher is better (accuracy, consistency, relevance)
                    normalized = value
                
                score += normalized * weight
        
        return score
    
    def _get_metric_weights(self) -> Dict[str, float]:
        """Get weights for each metric."""
        metric_count = len(self.target_metrics)
        return {metric: 1.0 / metric_count for metric in self.target_metrics}
    
    def suggest_improvements(self, prompt: str) -> List[str]:
        """Suggest improvements to a prompt using auto-techniques."""
        suggestions = []
        
        # Check prompt length
        if len(prompt.split()) > 100:
            suggestions.append("Consider shortening the prompt for faster processing")
        
        # Check for specificity
        if len(prompt.split()) < 10:
            suggestions.append("Consider making the prompt more specific/detailed")
        
        # Check for clarity
        if "?" in prompt and "." not in prompt:
            suggestions.append("Consider adding more context after the question")
        
        # Check for structured format
        if not any(marker in prompt for marker in ["1.", "-", "*", "###"]):
            suggestions.append("Consider using structured formatting (lists, sections)")
        
        return suggestions
    
    def optimize_prompt(
        self,
        base_prompt: str,
        optimization_strategy: str = "iterative",
    ) -> str:
        """Auto-optimize a prompt using various strategies."""
        
        if optimization_strategy == "iterative":
            return self._optimize_iterative(base_prompt)
        elif optimization_strategy == "chain_of_thought":
            return self._optimize_chain_of_thought(base_prompt)
        elif optimization_strategy == "few_shot":
            return self._optimize_few_shot(base_prompt)
        else:
            logger.warning(f"Unknown strategy: {optimization_strategy}")
            return base_prompt
    
    def _optimize_iterative(self, prompt: str) -> str:
        """Iterative prompt optimization."""
        optimized = prompt
        suggestions = self.suggest_improvements(prompt)
        
        # Apply specific optimizations
        if "Consider shortening" in str(suggestions):
            # Summarize prompt
            words = optimized.split()[:50]
            optimized = " ".join(words)
        
        if "Consider making" in str(suggestions):
            optimized = f"{optimized}\n\nBe specific and detailed in your response."
        
        if "Consider using structured" in str(suggestions):
            optimized = f"{optimized}\n\nFormat your response with clear sections and bullet points."
        
        return optimized
    
    def _optimize_chain_of_thought(self, prompt: str) -> str:
        """Chain-of-thought prompt optimization."""
        return f"""{prompt}

Let's think step by step:
1. First, identify the key components
2. Then analyze each component
3. Finally, synthesize the answer

Provide your reasoning and final answer."""
    
    def _optimize_few_shot(self, prompt: str) -> str:
        """Few-shot prompt optimization with examples."""
        return f"""{prompt}

Examples:
- Example 1: [Your first example here]
- Example 2: [Your second example here]

Now, please follow this pattern for your response."""
    
    def get_best_prompt(self) -> Optional[str]:
        """Get the best optimized prompt."""
        if self.best_variant:
            return self.best_variant.prompt
        return None
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """Generate optimization report."""
        if not self.variants:
            return {"status": "No variants tracked"}
        
        return {
            "total_variants": len(self.variants),
            "best_score": self.best_variant.score if self.best_variant else 0.0,
            "best_prompt": self.best_variant.prompt if self.best_variant else None,
            "best_metrics": self.best_variant.metrics if self.best_variant else {},
            "average_score": sum(v.score for v in self.variants) / len(self.variants),
        }
