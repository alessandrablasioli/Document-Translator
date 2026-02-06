"""
Validation Agent - Verifies translation quality and completeness.
Part of the multi-agent translation system.
"""
import os
import logging
from typing import Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

logger = logging.getLogger(__name__)
load_dotenv()


class ValidationAgent:
    """
    Agent specialized in validating translation quality.
    Checks completeness, accuracy, and formatting preservation.
    """
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY not set. Validation will be limited.")
            self.client = None
        else:
            self.client = OpenAI(api_key=api_key)
        
        self.agent_name = "ValidationAgent"
        self.model = "gpt-4o-mini"
    
    def validate(self, original_text: str, translated_text: str, target_language: str) -> Dict[str, Any]:
        """
        Validate translation quality and completeness.
        
        Args:
            original_text: Original text
            translated_text: Translated text
            target_language: Target language
            
        Returns:
            Dictionary with validation results
        """
        logger.info(f"[{self.agent_name}] Starting validation")
        
        validation_results = {
            "agent": self.agent_name,
            "validated": False,
            "issues": [],
            "quality_score": 0.0,
            "recommendations": []
        }
        
        try:
            # Basic checks
            basic_checks = self._basic_validation(original_text, translated_text)
            validation_results.update(basic_checks)
            
            # AI-powered quality check (if client available)
            if self.client:
                ai_validation = self._ai_quality_check(original_text, translated_text, target_language)
                validation_results.update(ai_validation)
            else:
                logger.warning(f"[{self.agent_name}] OpenAI client not available, skipping AI validation")
                validation_results["quality_score"] = 0.8  # Default score if no AI validation
                validation_results["validated"] = True
            
            validation_results["validated"] = True
            logger.info(f"[{self.agent_name}] Validation completed: score={validation_results['quality_score']:.2f}")
            
        except Exception as e:
            logger.error(f"[{self.agent_name}] Validation failed: {e}")
            validation_results["error"] = str(e)
            validation_results["validated"] = False
        
        return validation_results
    
    def _basic_validation(self, original_text: str, translated_text: str) -> Dict[str, Any]:
        """Perform basic validation checks"""
        issues = []
        
        # Check if translation is empty
        if not translated_text or not translated_text.strip():
            issues.append("Translated text is empty")
            return {
                "validated": False,
                "issues": issues,
                "quality_score": 0.0
            }
        
        # Check length ratio (translation shouldn't be drastically different)
        original_len = len(original_text)
        translated_len = len(translated_text)
        length_ratio = translated_len / original_len if original_len > 0 else 1.0
        
        if length_ratio < 0.3:
            issues.append(f"Translation is too short (ratio: {length_ratio:.2f})")
        elif length_ratio > 3.0:
            issues.append(f"Translation is too long (ratio: {length_ratio:.2f})")
        
        # Check for placeholder text or errors
        if "[ERROR]" in translated_text or "[TRANSLATION ERROR]" in translated_text:
            issues.append("Translation contains error markers")
        
        return {
            "issues": issues,
            "length_ratio": length_ratio,
            "basic_checks_passed": len(issues) == 0
        }
    
    def _ai_quality_check(self, original_text: str, translated_text: str, target_language: str) -> Dict[str, Any]:
        """Use AI to check translation quality"""
        try:
            prompt = f"""Evaluate the quality of this translation from the original text to {target_language}.

Original text (first 500 chars):
{original_text[:500]}

Translated text (first 500 chars):
{translated_text[:500]}

Please provide:
1. Quality score (0.0 to 1.0)
2. Any issues found (completeness, accuracy, formatting)
3. Recommendations for improvement

Format your response as:
SCORE: [0.0-1.0]
ISSUES: [list of issues or "None"]
RECOMMENDATIONS: [list of recommendations or "None"]"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a translation quality expert. Evaluate translations for accuracy, completeness, and formatting preservation."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Parse AI response
            quality_score = 0.8  # Default
            issues = []
            recommendations = []
            
            lines = result_text.split('\n')
            for line in lines:
                if line.startswith('SCORE:'):
                    try:
                        score_text = line.split(':')[1].strip()
                        quality_score = float(score_text)
                    except:
                        pass
                elif line.startswith('ISSUES:'):
                    issues_text = line.split(':', 1)[1].strip()
                    if issues_text.lower() != 'none':
                        issues.extend([i.strip() for i in issues_text.split(',')])
                elif line.startswith('RECOMMENDATIONS:'):
                    rec_text = line.split(':', 1)[1].strip()
                    if rec_text.lower() != 'none':
                        recommendations.extend([r.strip() for r in rec_text.split(',')])
            
            return {
                "quality_score": quality_score,
                "ai_issues": issues,
                "recommendations": recommendations,
                "ai_validation_performed": True
            }
            
        except Exception as e:
            logger.error(f"[{self.agent_name}] AI quality check failed: {e}")
            return {
                "quality_score": 0.7,  # Conservative default
                "ai_validation_performed": False,
                "ai_validation_error": str(e)
            }
    
    def should_retry_translation(self, validation_result: Dict[str, Any]) -> bool:
        """
        Determine if translation should be retried based on validation.
        
        Args:
            validation_result: Result from validate() method
            
        Returns:
            True if translation should be retried
        """
        if not validation_result.get("validated", False):
            return True
        
        quality_score = validation_result.get("quality_score", 0.0)
        critical_issues = validation_result.get("issues", [])
        
        # Retry if quality score is too low
        if quality_score < 0.5:
            return True
        
        # Retry if there are critical issues
        if any("empty" in issue.lower() or "error" in issue.lower() for issue in critical_issues):
            return True
        
        return False

