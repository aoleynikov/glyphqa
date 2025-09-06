"""
Constants used throughout the GlyphQA system.
Centralizes magic numbers and strings for better maintainability.
"""


class Constants:
    """System-wide constants."""
    
    # Hash and validation constants
    HASH_LENGTH = 64
    SHA256_LENGTH = 64
    
    # Debug and logging limits
    DEBUG_LOG_LIMIT = 500
    JSON_PARSE_LIMIT = 200
    JSON_PREVIEW_LIMIT = 200
    
    # Default values
    DEFAULT_URL = "http://localhost:3000"
    DEFAULT_TITLE = "React App"
    DEFAULT_PORT = 3000
    
    # File paths and extensions
    GLYPH_EXTENSION = ".glyph"
    GUIDE_EXTENSION = ".guide"
    SPEC_EXTENSION = ".spec.js"
    CONFIG_FILE = "glyph.config.yml"
    
    # Directory structure
    GLYPH_DIR = ".glyph"
    GUIDES_DIR = ".glyph/guides"
    TESTS_DIR = ".glyph/tests"
    
    # Template names
    INITIAL_SPEC_TEMPLATE = "initial_spec"
    ITERATION_SPEC_TEMPLATE = "iteration_spec"
    DEBUG_SPEC_TEMPLATE = "debug_spec"
    SUMMARIZE_TEMPLATE = "summarize"
    LIST_ACTIONS_TEMPLATE = "list_actions"
    
    # Version information
    GUIDE_VERSION = "1.0"
    SYSTEM_VERSION = "1.0"
    
    # Error messages
    CONFIG_NOT_FOUND = "Config file not found: {}"
    INVALID_YAML = "Invalid YAML in config file {}: {}"
    NOT_DICT_YAML = "Config file must contain a YAML dictionary: {}"
    UNKNOWN_TARGET = "Unknown target: {}"
    GUIDE_NOT_FOUND = "Guide file not found: {}"
    SCENARIO_NOT_FOUND = "Scenario '{}' not found in available scenarios"
    DEPENDENCY_NOT_FOUND = "Dependency '{}' not found in available scenarios"
    
    # Success messages
    CONFIG_LOADED = "Successfully loaded config from {}"
    GUIDE_LOADED = "Loaded guide: {}"
    SCENARIO_BUILT = "Successfully built: {}"
    ALL_SCENARIOS_BUILT = "Successfully built all {} scenarios in {} layers!"
    
    # Warning messages
    PARTIAL_BUILD = "Built {}/{} scenarios"
    DEBUG_SPEC_FAILED = "Debug spec execution failed ({}): {}"
    JSON_DECODE_ERROR = "JSON decode error for action '{}': {}"
    JSON_PARSE_FAILED = "Failed to parse JSON even after all cleanup strategies for action '{}'"
    
    # JSON structure templates
    MINIMAL_PAGE_STATE = {
        "url": DEFAULT_URL + "/",
        "title": DEFAULT_TITLE,
        "elements": [],
        "visibleElements": [],
        "navigationElements": [],
        "formElements": [],
        "forms": [],
        "interactionReport": {
            "buttons": [],
            "inputs": [],
            "selects": [],
            "links": [],
            "labels": []
        },
        "elementCounts": {
            "total": 0,
            "visible": 0,
            "forms": 0,
            "inputs": 0,
            "buttons": 0,
            "selects": 0,
            "links": 0,
            "labels": 0
        }
    }
