# Standard Library
import re
import logging
import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

# Third-Party Libraries

# Local Imports
from backend.core.error_handlers import SecurityError, get_error_handler

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class SanitizationResult:
    """
    Result of prompt sanitization with security metadata.

    Attributes:
        is_safe: Whether the input is safe to use
        sanitized_text: The sanitized text
        detected_threats: List of detected threat types
        threat_score: Security risk score (0-10)
        original_length: Original text length
        sanitized_length: Sanitized text length
    """

    is_safe: bool
    sanitized_text: str
    detected_threats: List[str]
    threat_score: float
    original_length: int
    sanitized_length: int


class PromptSanitizer:
    """
    LLM Prompt Injection Prevention System.

    Protects against:
    - Prompt injection attacks
    - Personally Identifiable Information (PII) leakage
    - Malicious instructions
    - Role manipulation
    - Context pollution
    - Output manipulation

    Features:
    - Multi-layer sanitization pipeline
    - PII detection and redaction
    - Injection pattern detection
    - Context-aware validation
    - Threat scoring system
    - Comprehensive logging
    """

    def __init__(self):
        self.error_handler = get_error_handler()

        # Injection patterns database
        self.injection_patterns = self._load_injection_patterns()

        # PII patterns for detection
        self.pii_patterns = self._load_pii_patterns()

        # Safe character sets
        self.safe_chars = set(" ,.!?'-_")

    def _load_injection_patterns(self) -> Dict[str, List[str]]:
        """Load known prompt injection patterns."""
        return {
            # Direct instruction injection
            "direct_injection": [
                r"\b(ignore|forget|disregard)\s+(?:(?:all|previous|prior)\s+){0,2}(instructions|commands|rules)\b",
                r"\b(ignore|forget|disregard)\s+(previous|prior|all)\s+(instructions|commands|rules)\b",
                r"\b(override|bypass|skip)\s+(safety|security|restrictions|guidelines)\b",
                r"\bact\s+as\s+if\s+you\s+are\s+.*\b",
                r"\bpretend\s+you\s+are\s+.*\b",
                r"\bimagine\s+you\s+are\s+.*\b",
                r"\bfrom\s+now\s+on\s+.*\b",
                r"\byour\s+new\s+role\s+is\s+.*\b",
                r"\byou\s+are\s+now\s+.*\b",
            ],
            # Role manipulation
            "role_manipulation": [
                r"\b(assume|take|adopt)\s+the\s+role\s+of\s+.*\b",
                r"\b(behave|respond|act)\s+as\s+.*\b",
                r"\b(impersonate|mimic|emulate)\s+.*\b",
                r"\b(you|your)\s+are\s+(now|currently)\s+.*\b",
            ],
            # Context pollution
            "context_pollution": [
                r"\b(remember|recall|note)\s+that\s+.*\b",
                r"\b(keep|maintain|retain)\s+this\s+.*\b",
                r"\b(forget|dismiss|ignore)\s+everything\s+.*\b",
                r"\b(clear|reset|erase)\s+(memory|context|history)\b",
            ],
            # Output manipulation
            "output_manipulation": [
                r"\b(output|print|display|show)\s+.*\b",
                r"\b(return|provide|give)\s+.*\b",
                r"\b(format|structure|organize)\s+.*\b",
                r"\b(write|create|generate)\s+.*\b",
            ],
            # System command injection
            "system_commands": [
                r"\b(execute|run|launch|start)\s+.*\b",
                r"\b(system|os|command|shell|terminal)\s+.*\b",
                r"\b(import|require|include)\s+.*\b",
                r"\b(eval|exec|compile)\s+.*\b",
            ],
            # Privacy violations
            "privacy_violations": [
                r"\b(reveal|disclose|expose|leak)\s+.*\b",
                r"\b(share|send|transmit|forward)\s+.*\b",
                r"\b(access|retrieve|obtain)\s+.*\b",
                r"\b(extract|copy|duplicate)\s+.*\b",
            ],
            # Malicious instructions
            "malicious_instructions": [
                r"\b(hack|crack|exploit|bypass|circumvent)\s+.*\b",
                r"\b(phish|scam|deceive|trick)\s+.*\b",
                r"\b(malware|virus|trojan|worm|spyware)\s+.*\b",
                r"\b(attack|breach|compromise|infiltrate)\s+.*\b",
            ],
        }

    def _load_pii_patterns(self) -> Dict[str, List[str]]:
        """Load PII detection patterns."""
        return {
            "emails": [r"\b[\w\.-]+@[\w\.-]+\.\w{2,}\b"],
            "phone_numbers": [
                r"\b\+?\d{1,3}[- .]?\(?\d{2,3}\)?[- .]?\d{2,4}[- .]?\d{2,4}\b",
                r"\b\d{3}[- .]?\d{3}[- .]?\d{4}\b",
            ],
            "credit_cards": [
                r"\b\d{4}[- .]?\d{4}[- .]?\d{4}[- .]?\d{4}\b",
                r"\b\d{16}\b",
            ],
            "ssn": [r"\b\d{3}[- .]?\d{2}[- .]?\d{4}\b"],
            "ip_addresses": [
                r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b",
                r"\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b",
            ],
            "physical_addresses": [
                r"\b\d{1,5}\s+[\w\s]{3,}\s+(street|st|avenue|ave|road|rd|boulevard|blvd|lane|ln|drive|dr)\b"
            ],
            "api_keys": [
                r"\b(sk-|sk_|key-|key_|api-|api_|token-|token_)[a-zA-Z0-9]{10,}\b",
                r"\b[A-Za-z0-9]{32,}\b",
            ],
            "passwords": [
                r"\b(password|passwd|pwd)\s*[=:]\s*[^\s]+\b",
                r"\b(secret|token|key)\s*[=:]\s*[^\s]+\b",
            ],
        }

    def sanitize_user_input(
        self, user_input: str, context: Optional[str] = None, max_length: int = 1000
    ) -> SanitizationResult:
        """
        Sanitize user input to prevent prompt injection and PII leakage.

        Args:
            user_input: Raw user input text
            context: Optional context for validation
            max_length: Maximum allowed length

        Returns:
            SanitizationResult with safety assessment and sanitized text

        Raises:
            HTTPException: If input is unsafe and cannot be sanitized
        """
        if user_input is None:
            raise ValueError("user_input must not be None")
        if isinstance(user_input, list):
            user_input = " ".join(str(item) for item in user_input)
        if not isinstance(user_input, str):
            raise ValueError("user_input must be a string or list of values")
        if not user_input:
            return SanitizationResult(
                is_safe=True,
                sanitized_text="",
                detected_threats=[],
                threat_score=0.0,
                original_length=0,
                sanitized_length=0,
            )

        original_text = user_input.strip()
        detected_threats = []
        threat_score = 0.0

        # Check length
        if len(original_text) > max_length:
            detected_threats.append("input_too_long")
            threat_score += 2.0
            original_text = original_text[:max_length]

        # Check for injection patterns
        for threat_type, patterns in self.injection_patterns.items():
            for pattern in patterns:
                if re.search(pattern, original_text, re.IGNORECASE):
                    detected_threats.append(threat_type)
                    threat_score += 3.0
                    break  # Only count each threat type once

        # Check for PII
        pii_detected = self._detect_pii(original_text)
        if pii_detected:
            detected_threats.extend(pii_detected)
            threat_score += 4.0

        injection_threats = set(detected_threats).intersection(self.injection_patterns)
        is_safe = not injection_threats

        if not is_safe:
            # Log security event
            logger.warning(
                f"Prompt injection attempt detected. "
                f"Threats: {detected_threats}. "
                f"Threat score: {threat_score}. "
                f"Context: {context}"
            )
            logger.error("Rejected unsafe prompt input")

            # Create security error
            security_error = self.error_handler.create_security_error(
                "invalid_input",
                details=f"Prompt injection detected: {detected_threats}",
            )
            raise security_error

        # Basic sanitization (remove potentially harmful characters)
        sanitized_text = self._basic_sanitization(original_text)
        logger.info("Prompt input sanitized successfully")

        return SanitizationResult(
            is_safe=is_safe,
            sanitized_text=sanitized_text,
            detected_threats=detected_threats,
            threat_score=threat_score,
            original_length=len(user_input),
            sanitized_length=len(sanitized_text),
        )

    def _detect_pii(self, text: str) -> List[str]:
        """Detect personally identifiable information in text."""
        detected_pii = []

        for pii_type, patterns in self.pii_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    detected_pii.append(pii_type)
                    break  # Only count each PII type once

        return detected_pii

    def _basic_sanitization(self, text: str) -> str:
        """Basic text sanitization to remove harmful characters."""
        text = re.sub(r"<(script|style)\b[^>]*>.*?</\1\s*>", " ", text, flags=re.IGNORECASE | re.DOTALL)
        # Remove potentially harmful characters while preserving international text.
        sanitized = []
        for char in text:
            if char.isalnum() or char in self.safe_chars or char.isspace():
                sanitized.append(char)
            else:
                # Replace with space to maintain word boundaries
                sanitized.append(" ")

        # Clean up multiple spaces
        result = " ".join("".join(sanitized).split())
        return result

    def validate_output(self, llm_output: Any, expected_format: Optional[str] = None) -> bool:
        """
        Validate LLM output for injection attempts and format compliance.

        Args:
            llm_output: Raw LLM output
            expected_format: Expected output format (json, text, etc.)

        Returns:
            True if output is safe, False if suspicious
        """
        if not llm_output:
            raise SecurityError(400, "VAL_003", "Invalid output format")

        try:
            output_text = llm_output if isinstance(llm_output, str) else json.dumps(llm_output)
        except (TypeError, ValueError) as exc:
            raise SecurityError(400, "VAL_003", "Invalid output format") from exc

        if len(output_text) > 10_000:
            raise SecurityError(400, "VAL_003", "Output exceeds maximum length")

        # Check for suspicious patterns in output
        suspicious_patterns = [
            r"\b(i\s+am\s+|i\'m\s+|my\s+name\s+is\s+).*\b",  # Role confusion
            r"\b(as\s+an?\s+ai|as\s+a\s+language\s+model).*\b",  # Role confusion
            r"\b(cannot|can\'t|unable\s+to).*\b",  # Refusal patterns
            r"\b(i\s+was\s+created|i\s+was\s+designed).*\b",  # Role confusion
            r"\b(my\s+purpose\s+is|i\s+am\s+here\s+to).*\b",  # Role confusion
            r"\b(sorry|apologize|regret).*\b",  # Apology patterns
            r"\b(error|warning|alert|danger).*\b",  # Error indicators
            r"\b(hack|exploit|vulnerability|breach).*\b",  # Security terms
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, output_text, re.IGNORECASE):
                logger.warning(f"Suspicious LLM output detected: {pattern}")
                raise SecurityError(400, "VAL_003", "Suspicious patterns detected in LLM output")

        for patterns in self.injection_patterns.values():
            if any(re.search(pattern, output_text, re.IGNORECASE) for pattern in patterns):
                raise SecurityError(400, "VAL_003", "Suspicious patterns detected in LLM output")

        # Validate format if specified
        if expected_format == "json":
            try:
                if isinstance(llm_output, str):
                    json.loads(llm_output)
                return True
            except (json.JSONDecodeError, ValueError) as exc:
                logger.warning("LLM output failed JSON validation")
                raise SecurityError(400, "VAL_003", "Invalid output format") from exc

        return True

    def create_prompt_template(
        self,
        system_instructions: str,
        user_input_placeholder: str = "{{user_input}}",
        context_placeholder: str = "{{context}}",
    ) -> str:
        """
        Create a secure prompt template that separates system instructions from user input.

        Args:
            system_instructions: Fixed system instructions
            user_input_placeholder: Placeholder for user input
            context_placeholder: Placeholder for additional context

        Returns:
            Secure prompt template
        """
        # Validate system instructions don't contain placeholders
        if user_input_placeholder in system_instructions:
            raise ValueError("System instructions cannot contain user input placeholder")

        if context_placeholder in system_instructions:
            raise ValueError("System instructions cannot contain context placeholder")

        # Create structured template
        template = f"""SYSTEM INSTRUCTIONS (DO NOT MODIFY):
{system_instructions}

USER CONTEXT (READ-ONLY):
{context_placeholder}

USER INPUT (SANITIZED):
{user_input_placeholder}

RESPONSE FORMAT: JSON only, no explanations or commentary."""

        return template

    def sanitize_and_template(
        self, user_input: str, system_instructions: str, context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Complete sanitization and templating workflow.

        Args:
            user_input: Raw user input
            system_instructions: Fixed system instructions
            context: Additional context

        Returns:
            Dictionary with sanitized input and secure template

        Raises:
            HTTPException: If input is unsafe
        """
        # Sanitize user input
        sanitization_result = self.sanitize_user_input(user_input, "prompt_injection")

        # Create secure template
        template = self.create_prompt_template(system_instructions)

        # Fill template with sanitized input
        sanitized_context = context or "No additional context provided."

        secure_prompt = template.replace("{{user_input}}", sanitization_result.sanitized_text)
        secure_prompt = secure_prompt.replace("{{context}}", sanitized_context)

        return {
            "sanitization_result": sanitization_result,
            "secure_prompt": secure_prompt,
            "is_safe": sanitization_result.is_safe,
            "threat_score": sanitization_result.threat_score,
        }


# Global prompt sanitizer instance
prompt_sanitizer = PromptSanitizer()


def get_prompt_sanitizer() -> PromptSanitizer:
    """Get the global prompt sanitizer instance."""
    return prompt_sanitizer


def sanitize_user_input(user_input: str, context: Optional[str] = None, max_length: int = 1000) -> SanitizationResult:
    """Convenience function to sanitize user input."""
    return prompt_sanitizer.sanitize_user_input(user_input, context, max_length)
