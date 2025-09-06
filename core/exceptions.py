"""
Custom exception classes for GlyphQA system.
Provides specific exception types for different error scenarios.
"""


class GlyphQAError(Exception):
    """Base exception for all GlyphQA errors."""
    pass


class ConfigurationError(GlyphQAError):
    """Raised when there are configuration issues."""
    pass


class FileSystemError(GlyphQAError):
    """Raised when there are file system related errors."""
    pass


class ScenarioError(GlyphQAError):
    """Raised when there are scenario-related errors."""
    pass


class GuideError(GlyphQAError):
    """Raised when there are guide-related errors."""
    pass


class LLMError(GlyphQAError):
    """Raised when there are LLM-related errors."""
    pass


class BuildError(GlyphQAError):
    """Raised when there are build process errors."""
    pass


class ValidationError(GlyphQAError):
    """Raised when validation fails."""
    pass


class DependencyError(GlyphQAError):
    """Raised when there are dependency-related errors."""
    pass


class TemplateError(GlyphQAError):
    """Raised when there are template-related errors."""
    pass


class TargetError(GlyphQAError):
    """Raised when there are target-related errors."""
    pass
