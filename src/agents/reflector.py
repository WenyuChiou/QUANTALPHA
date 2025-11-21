"""Reflector Agent - analyzes failures and generates improvement suggestions."""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    print("Warning: google-generativeai not installed. Using mock mode.")

from ..memory.schemas import AgentResult, AgentContent, AgentArtifact
from ..memory.policy_manager import PolicyManager


class ReflectorAgent:
    """Agent that analyzes failures and generates lessons."""
    
    def __init__(
        self,
        model_name: str = "gemini-1.5-pro",
        api_key: Optional[str] = None
    ):
        """Initialize reflector agent.
        
        Args:
            model_name: Gemini model name
            api_key: Google API key (or set GOOGLE_API_KEY env var)
        """
        self.model_name = model_name
        self.policy_manager = PolicyManager()
        
        if GEMINI_AVAILABLE:
            if api_key:
                genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(model_name)
        else:
            self.model = None
    
    def analyze(
        self,
        alpha_id: str,
        metrics: Dict[str, Any],
        compliance: Dict[str, Any],
        signals_meta: Dict[str, Any],
        factor_yaml: Optional[str] = None,
        past_lessons: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Analyze a failed/conditional alpha and generate lessons.
        
        Args:
            alpha_id: Alpha identifier (e.g., 'alpha_001')
            metrics: Performance metrics
            compliance: Compliance report from CriticAgent
            signals_meta: Signal metadata
            factor_yaml: Factor YAML specification
            past_lessons: Previous lessons learned
        
        Returns:
            Lessons dictionary
        """
        # Get applicable policy rules
        applicable_rules = self.policy_manager.get_applicable_rules(metrics)
        
        # Check constraints
        meets_constraints, violations = self.policy_manager.check_constraints(metrics)
        
        # Determine verdict
        verdict = "PASS" if meets_constraints else "FAIL"
        if compliance.get('verdict') == 'CONDITIONAL':
            verdict = "CONDITIONAL"
        
        # Analyze root causes
        root_causes = self._analyze_root_causes(
            metrics, compliance, signals_meta, applicable_rules, violations
        )
        
        # Generate improvement suggestions
        improvements = self._generate_improvements(
            root_causes, metrics, past_lessons
        )
        
        # Create lessons
        lessons = {
            "iteration": int(alpha_id.split('_')[1]) if '_' in alpha_id else 1,
            "alpha_id": alpha_id,
            "verdict": verdict,
            "root_causes": root_causes,
            "improvement_suggestions": improvements,
            "applicable_rules": [r['rule_id'] for r in applicable_rules],
            "constraint_violations": violations,
            "lesson_id": self._generate_lesson_id(),
            "created_at": datetime.now().isoformat()
        }
        
        return lessons
    
    def analyze_failure(
        self,
        alpha_id: str,
        metrics: Dict[str, Any],
        compliance: Dict[str, Any],
        signals_meta: Optional[Dict[str, Any]] = None,
        factor_yaml: Optional[str] = None,
        past_lessons: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Analyze a failed alpha (alias for analyze method).
        
        Args:
            alpha_id: Alpha identifier
            metrics: Performance metrics
            compliance: Compliance report
            signals_meta: Signal metadata (optional)
            factor_yaml: Factor YAML (optional)
            past_lessons: Previous lessons (optional)
        
        Returns:
            Lessons dictionary
        """
        # Use empty dict if signals_meta not provided
        if signals_meta is None:
            signals_meta = {}
        
        return self.analyze(
            alpha_id=alpha_id,
            metrics=metrics,
            compliance=compliance,
            signals_meta=signals_meta,
            factor_yaml=factor_yaml,
            past_lessons=past_lessons
        )
    

    def _analyze_root_causes(
        self,
        metrics: Dict[str, Any],
        compliance: Dict[str, Any],
        signals_meta: Dict[str, Any],
        applicable_rules: List[Dict[str, Any]],
        violations: List[str]
    ) -> List[Dict[str, Any]]:
        """Analyze root causes of failure.
        
        Returns:
            List of root cause dictionaries
        """
        causes = []
        
        # Check Sharpe ratio
        if metrics.get('sharpe', 0) < 1.0:
            causes.append({
                "issue": "low_sharpe",
                "detail": f"Sharpe ratio {metrics.get('sharpe', 0):.2f} is below target 1.0",
                "analysis": self._analyze_sharpe(metrics, signals_meta),
                "recommendation": "Improve signal quality, add regime filters, or use volatility normalization"
            })
        
        # Check max drawdown
        if metrics.get('maxdd', 0) < -0.20:
            causes.append({
                "issue": "high_drawdown",
                "detail": f"Max drawdown {metrics.get('maxdd', 0):.2%} exceeds -20%",
                "analysis": "Factor experiences large losses during adverse periods",
                "recommendation": "Implement position sizing, stop-loss, or volatility targeting"
            })
        
        # Check turnover
        if metrics.get('turnover_monthly', 0) > 100:
            causes.append({
                "issue": "high_turnover",
                "detail": f"Monthly turnover {metrics.get('turnover_monthly', 0):.1f}% exceeds 100%",
                "analysis": "Excessive trading will erode returns due to transaction costs",
                "recommendation": "Reduce rebalance frequency or add holding period constraint"
            })
        
        # Check IC
        if metrics.get('avg_ic', 0) < 0.05:
            causes.append({
                "issue": "low_ic",
                "detail": f"Average IC {metrics.get('avg_ic', 0):.3f} is below 0.05",
                "analysis": "Signal has weak predictive power for future returns",
                "recommendation": "Add more signals, improve signal construction, or combine multiple primitives"
            })
        
        # Check stability
        if metrics.get('split_sharpe_std', 0) > 1.5:
            causes.append({
                "issue": "unstable_performance",
                "detail": f"Split Sharpe std {metrics.get('split_sharpe_std', 0):.2f} > 1.5",
                "analysis": "Performance varies significantly across time periods",
                "recommendation": "Add regime awareness or reduce lookback window"
            })
        
        # Add compliance issues
        for issue in compliance.get('issues', []):
            if issue.get('severity') in ['critical', 'error']:
                causes.append({
                    "issue": issue.get('type', 'unknown'),
                    "detail": issue.get('detail', ''),
                    "analysis": issue.get('detail', ''),
                    "recommendation": issue.get('recommendation', '')
                })
        
        return causes
    
    def _analyze_sharpe(self, metrics: Dict[str, Any], signals_meta: Dict[str, Any]) -> str:
        """Analyze why Sharpe is low.
        
        Returns:
            Analysis string
        """
        reasons = []
        
        # Check IC
        if metrics.get('avg_ic', 0) < 0.05:
            reasons.append(f"Low IC ({metrics.get('avg_ic', 0):.3f}) indicates weak signal")
        
        # Check volatility
        if metrics.get('ann_vol', 0) > 0.15:
            reasons.append(f"High volatility ({metrics.get('ann_vol', 0):.2%}) reduces Sharpe")
        
        # Check hit rate
        if metrics.get('hit_rate', 0.5) < 0.52:
            reasons.append(f"Low hit rate ({metrics.get('hit_rate', 0.5):.2%}) suggests poor signal quality")
        
        # Check signal coverage
        if signals_meta.get('coverage', 1.0) < 0.90:
            reasons.append(f"Low coverage ({signals_meta.get('coverage', 1.0):.2%}) limits opportunities")
        
        return "; ".join(reasons) if reasons else "Multiple factors contributing to low Sharpe"
    
    def _generate_improvements(
        self,
        root_causes: List[Dict[str, Any]],
        metrics: Dict[str, Any],
        past_lessons: Optional[List[Dict[str, Any]]] = None
    ) -> List[Dict[str, Any]]:
        """Generate improvement suggestions using Gemini.
        
        Returns:
            List of improvement suggestion dictionaries with priority
        """
        # Collect all recommendations from root causes
        suggestions = []
        for cause in root_causes:
            rec = cause.get('recommendation', '')
            if rec:
                suggestions.append({
                    'suggestion': rec,
                    'priority': 'normal',
                    'source': 'root_cause'
                })
        
        # Detect repeated errors
        if past_lessons and len(past_lessons) >= 2:
            repeated_issues = self._detect_repeated_issues(past_lessons, root_causes)
            
            if repeated_issues:
                print(f"\n  ⚠️ REPEATED ERRORS DETECTED: {len(repeated_issues)} issues")
                for issue in repeated_issues:
                    print(f"     - {issue['issue']} (seen {issue['count']} times)")
                
                # Add high-priority suggestions for repeated issues
                suggestions.append({
                    'suggestion': f"⚠️ CRITICAL: {len(repeated_issues)} repeated errors detected. Consider a fundamentally different approach.",
                    'priority': 'critical',
                    'source': 'repeated_error_detection'
                })
                
                # Suggest alternative factor families
                if any('sharpe' in issue['issue'].lower() or 'ic' in issue['issue'].lower() for issue in repeated_issues):
                    suggestions.append({
                        'suggestion': "Try a completely different factor family (e.g., if using momentum, switch to value or quality)",
                        'priority': 'high',
                        'source': 'repeated_error_detection'
                    })
        
        # Add context-specific suggestions
        if metrics.get('sharpe', 0) < 0.5:
            suggestions.append({
                'suggestion': "Consider a completely different factor family (e.g., value, quality, low volatility)",
                'priority': 'high',
                'source': 'low_sharpe'
            })
        
        if metrics.get('avg_ic', 0) < 0.03:
            suggestions.append({
                'suggestion': "Current signal has very weak predictive power - try combining with other signals or use ensemble approach",
                'priority': 'high',
                'source': 'low_ic'
            })
        
        if metrics.get('turnover_monthly', 0) > 150:
            suggestions.append({
                'suggestion': "Change rebalance frequency from daily to weekly or monthly to reduce turnover",
                'priority': 'normal',
                'source': 'high_turnover'
            })
        
        # Use Gemini for advanced suggestions (if available)
        if self.model and GEMINI_AVAILABLE:
            try:
                prompt = self._create_improvement_prompt(root_causes, metrics, past_lessons)
                response = self.model.generate_content(prompt)
                
                # Parse Gemini suggestions
                gemini_suggestions = self._parse_gemini_response(response.text)
                for sug in gemini_suggestions:
                    suggestions.append({
                        'suggestion': sug,
                        'priority': 'normal',
                        'source': 'gemini'
                    })
            except Exception as e:
                print(f"Warning: Gemini API call failed: {e}")
        
        # Sort by priority and return top 5
        priority_order = {'critical': 0, 'high': 1, 'normal': 2}
        suggestions.sort(key=lambda x: priority_order.get(x.get('priority', 'normal'), 2))
        
        return suggestions[:5]  # Return top 5 suggestions
    
    def _detect_repeated_issues(
        self,
        past_lessons: List[Dict[str, Any]],
        current_causes: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Detect issues that have appeared multiple times.
        
        Args:
            past_lessons: Previous lessons learned
            current_causes: Current root causes
        
        Returns:
            List of repeated issues with count
        """
        # Track issue occurrences
        issue_counts = {}
        
        # Count issues from past lessons
        for lesson in past_lessons[-5:]:  # Look at last 5 lessons
            for cause in lesson.get('root_causes', []):
                issue = cause.get('issue', 'unknown')
                issue_counts[issue] = issue_counts.get(issue, 0) + 1
        
        # Check current causes against past
        repeated = []
        for cause in current_causes:
            issue = cause.get('issue', 'unknown')
            if issue in issue_counts and issue_counts[issue] >= 2:
                repeated.append({
                    'issue': issue,
                    'count': issue_counts[issue] + 1,  # +1 for current occurrence
                    'detail': cause.get('detail', '')
                })
        
        return repeated
    
    def _create_improvement_prompt(
        self,
        root_causes: List[Dict[str, Any]],
        metrics: Dict[str, Any],
        past_lessons: Optional[List[Dict[str, Any]]]
    ) -> str:
        """Create prompt for Gemini to generate improvements.
        
        Returns:
            Prompt string
        """
        prompt = f"""You are a quantitative research expert analyzing a failed alpha factor.

## Performance Metrics
- Sharpe: {metrics.get('sharpe', 0):.2f}
- Annual Return: {metrics.get('ann_ret', 0):.2%}
- Max Drawdown: {metrics.get('maxdd', 0):.2%}
- Average IC: {metrics.get('avg_ic', 0):.3f}
- Turnover (monthly): {metrics.get('turnover_monthly', 0):.1f}%

## Identified Issues
"""
        for cause in root_causes:
            prompt += f"- {cause['issue']}: {cause['detail']}\n"
        
        if past_lessons:
            prompt += f"\n## Past Lessons (from {len(past_lessons)} previous iterations)\n"
            for lesson in past_lessons[-3:]:  # Last 3 lessons
                prompt += f"- {lesson.get('alpha_id', 'unknown')}: {', '.join([c['issue'] for c in lesson.get('root_causes', [])])}\n"
        
        prompt += """
## Task
Generate 3-5 specific, actionable improvements for the next iteration. Focus on:
1. Signal construction improvements
2. Risk management enhancements
3. Parameter optimization
4. Regime awareness

Format your response as a numbered list of concrete suggestions.
"""
        return prompt
    
    def _parse_gemini_response(self, response_text: str) -> List[str]:
        """Parse Gemini response into suggestions.
        
        Returns:
            List of suggestions
        """
        suggestions = []
        lines = response_text.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            # Look for numbered items
            if line and (line[0].isdigit() or line.startswith('-') or line.startswith('*')):
                # Remove numbering
                suggestion = line.lstrip('0123456789.-* ').strip()
                if suggestion:
                    suggestions.append(suggestion)
        
        return suggestions
    
    def _generate_lesson_id(self) -> int:
        """Generate a unique lesson ID.
        
        Returns:
            Lesson ID
        """
        # Simple incrementing ID (in production, use database)
        import random
        return random.randint(1000, 9999)
    
    def to_agent_result(self, lessons: Dict[str, Any]) -> AgentResult:
        """Convert lessons to AgentResult format.
        
        Args:
            lessons: Lessons dictionary
        
        Returns:
            AgentResult
        """
        # Create summary
        summary = f"Analyzed {lessons['alpha_id']}: {lessons['verdict']}"
        if lessons['root_causes']:
            summary += f" - {len(lessons['root_causes'])} issues identified"
        
        # Create artifacts
        artifacts = [
            AgentArtifact(
                name="lessons.json",
                path=f"lessons_{lessons['alpha_id']}.json",
                artifact_type="json",
                size_bytes=len(json.dumps(lessons))
            )
        ]
        
        return AgentResult(
            agent_name="ReflectorAgent",
            status="completed",
            summary=summary,
            content=AgentContent(
                text=json.dumps(lessons, indent=2),
                format="json"
            ),
            artifacts=artifacts,
            metadata={
                "verdict": lessons['verdict'],
                "num_issues": len(lessons['root_causes']),
                "num_suggestions": len(lessons['improvement_suggestions'])
            }
        )
