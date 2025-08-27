#!/usr/bin/env python3

import pytest
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
from core.hash_caching import HashCachingSystem, calculate_glyph_hash


class TestHashCaching:
    """Test hash-based caching for scenario building."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.scenarios_dir = Path(self.temp_dir) / "scenarios"
        self.glyph_dir = Path(self.temp_dir) / ".glyph"
        self.guides_dir = self.glyph_dir / "guides"
        
        # Create directories
        self.scenarios_dir.mkdir(parents=True)
        self.glyph_dir.mkdir(parents=True)
        self.guides_dir.mkdir(parents=True)
        
        # Create test scenario file
        self.scenario_file = self.scenarios_dir / "test_scenario.glyph"
        self.scenario_content = "log in as admin\ngo to users and click \"Create New User\"\nfill in the fields\nsubmit the form"
        self.scenario_file.write_text(self.scenario_content)
        
        # Initialize caching system
        self.caching_system = HashCachingSystem(self.glyph_dir)
    
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_calculate_glyph_hash(self):
        """Test hash calculation for glyph files."""
        hash1 = calculate_glyph_hash(str(self.scenario_file))
        hash2 = calculate_glyph_hash(str(self.scenario_file))
        
        # Same content should produce same hash
        assert hash1 == hash2
        assert len(hash1) == 64  # SHA256 hex length
        
        # Different content should produce different hash
        self.scenario_file.write_text("different content")
        hash3 = calculate_glyph_hash(str(self.scenario_file))
        assert hash3 != hash1
    
    def test_should_rebuild_no_guide_exists(self):
        """Test that rebuild is required when no guide exists."""
        should_rebuild = self.caching_system.should_rebuild_guide(
            "test_scenario", 
            str(self.scenario_file), 
            force=False
        )
        assert should_rebuild is True
    
    def test_should_rebuild_force_flag(self):
        """Test that force flag bypasses hash checking."""
        # Create an existing guide
        guide_data = {
            "scenario_name": "test_scenario",
            "actions": ["action1", "action2"],
            "glyph_hash": calculate_glyph_hash(str(self.scenario_file)),
            "built_at": "2025-01-27T10:30:00"
        }
        guide_file = self.guides_dir / "test_scenario.guide"
        guide_file.write_text(json.dumps(guide_data))
        
        # Force rebuild should return True even with matching hash
        should_rebuild = self.caching_system.should_rebuild_guide(
            "test_scenario", 
            str(self.scenario_file), 
            force=True
        )
        assert should_rebuild is True
    
    def test_should_rebuild_hash_mismatch(self):
        """Test that rebuild is required when hash doesn't match."""
        # Create guide with old hash
        old_hash = "old_hash_value"
        guide_data = {
            "scenario_name": "test_scenario",
            "actions": ["action1", "action2"],
            "glyph_hash": old_hash,
            "built_at": "2025-01-27T10:30:00"
        }
        guide_file = self.guides_dir / "test_scenario.guide"
        guide_file.write_text(json.dumps(guide_data))
        
        # Current hash should be different
        current_hash = calculate_glyph_hash(str(self.scenario_file))
        assert current_hash != old_hash
        
        should_rebuild = self.caching_system.should_rebuild_guide(
            "test_scenario", 
            str(self.scenario_file), 
            force=False
        )
        assert should_rebuild is True
    
    def test_should_rebuild_hash_match(self):
        """Test that rebuild is skipped when hash matches."""
        # Create guide with current hash
        current_hash = calculate_glyph_hash(str(self.scenario_file))
        guide_data = {
            "scenario_name": "test_scenario",
            "actions": ["action1", "action2"],
            "glyph_hash": current_hash,
            "built_at": "2025-01-27T10:30:00"
        }
        guide_file = self.guides_dir / "test_scenario.guide"
        guide_file.write_text(json.dumps(guide_data))
        
        should_rebuild = self.caching_system.should_rebuild_guide(
            "test_scenario", 
            str(self.scenario_file), 
            force=False
        )
        assert should_rebuild is False
    
    def test_save_and_load_guide(self):
        """Test saving and loading guides with hash."""
        # Create a mock guide
        mock_guide = Mock()
        mock_guide.scenario_name = "test_scenario"
        mock_guide.actions = ["action1", "action2", "action3"]
        mock_guide.glyph_hash = calculate_glyph_hash(str(self.scenario_file))
        mock_guide.built_at = "2025-01-27T10:30:00"
        mock_guide.dependencies = []
        
        # Save guide
        self.caching_system.save_guide(mock_guide)
        
        # Verify guide file exists
        guide_file = self.guides_dir / "test_scenario.guide"
        assert guide_file.exists()
        
        # Load guide
        loaded_guide = self.caching_system.load_guide("test_scenario")
        
        # Verify loaded data matches
        assert loaded_guide.scenario_name == mock_guide.scenario_name
        assert loaded_guide.actions == mock_guide.actions
        assert loaded_guide.glyph_hash == mock_guide.glyph_hash
        assert loaded_guide.built_at == mock_guide.built_at
    
    def test_build_scenario_with_caching(self):
        """Test the complete build scenario with caching behavior."""
        # Mock the internal methods of the caching system
        mock_build_guide = Mock(return_value=Mock())
        mock_build_test_function = Mock(return_value="test_function_code")
        mock_run_and_learn = Mock()
        mock_load_existing_test_function = Mock(return_value="cached_test_function_code")
        
        # Create a proper mock guide for the first build
        mock_guide = Mock()
        mock_guide.scenario_name = "test_scenario"
        mock_guide.actions = ["action1", "action2"]
        mock_guide.glyph_hash = calculate_glyph_hash(str(self.scenario_file))
        mock_guide.built_at = "2025-01-27T10:30:00"
        mock_guide.dependencies = []
        
        # First build - should build everything
        with patch.object(self.caching_system, '_build_guide', mock_build_guide), \
             patch.object(self.caching_system, '_build_test_function', mock_build_test_function), \
             patch.object(self.caching_system, '_run_and_learn', mock_run_and_learn):
            
            # Make _build_guide return our proper mock guide
            mock_build_guide.return_value = mock_guide
            
            result = self.caching_system.build_scenario_with_caching(
                "test_scenario",
                str(self.scenario_file),
                force=False
            )
            
            # Should have called build functions
            mock_build_guide.assert_called_once()
            mock_build_test_function.assert_called_once()
            mock_run_and_learn.assert_called_once()
            assert result == "test_function_code"
        
        # Reset mocks
        mock_build_guide.reset_mock()
        mock_build_test_function.reset_mock()
        mock_run_and_learn.reset_mock()
        
        # Second build with same content - should use cache
        with patch.object(self.caching_system, '_build_guide', mock_build_guide), \
             patch.object(self.caching_system, '_build_test_function', mock_build_test_function), \
             patch.object(self.caching_system, '_run_and_learn', mock_run_and_learn), \
             patch.object(self.caching_system, '_load_existing_test_function', mock_load_existing_test_function):
            
            result = self.caching_system.build_scenario_with_caching(
                "test_scenario",
                str(self.scenario_file),
                force=False
            )
            
            # Should NOT have called build functions (using cache)
            mock_build_guide.assert_not_called()
            mock_build_test_function.assert_not_called()
            mock_run_and_learn.assert_not_called()
            assert result == "cached_test_function_code"
        
        # Third build with force - should rebuild
        with patch.object(self.caching_system, '_build_guide', mock_build_guide), \
             patch.object(self.caching_system, '_build_test_function', mock_build_test_function), \
             patch.object(self.caching_system, '_run_and_learn', mock_run_and_learn):
            
            # Make _build_guide return our proper mock guide again
            mock_build_guide.return_value = mock_guide
            
            result = self.caching_system.build_scenario_with_caching(
                "test_scenario",
                str(self.scenario_file),
                force=True
            )
            
            # Should have called build functions again
            mock_build_guide.assert_called_once()
            mock_build_test_function.assert_called_once()
            mock_run_and_learn.assert_called_once()
            assert result == "test_function_code"
    
    def test_purge_cached_knowledge(self):
        """Test that purge removes all cached knowledge."""
        # Create some test guides
        guide_data1 = {
            "scenario_name": "test_scenario1",
            "actions": ["action1"],
            "glyph_hash": "hash1",
            "built_at": "2025-01-27T10:30:00"
        }
        guide_data2 = {
            "scenario_name": "test_scenario2", 
            "actions": ["action2"],
            "glyph_hash": "hash2",
            "built_at": "2025-01-27T10:30:00"
        }
        
        guide_file1 = self.guides_dir / "test_scenario1.guide"
        guide_file2 = self.guides_dir / "test_scenario2.guide"
        glyph_md_file = self.glyph_dir / "glyph.md"
        
        # Create test files
        guide_file1.write_text(json.dumps(guide_data1))
        guide_file2.write_text(json.dumps(guide_data2))
        glyph_md_file.write_text("# Test glyph.md content")
        
        # Verify files exist
        assert guide_file1.exists()
        assert guide_file2.exists()
        assert glyph_md_file.exists()
        
        # Perform purge
        self.caching_system.purge_cached_knowledge()
        
        # Verify all files are removed
        assert not guide_file1.exists()
        assert not guide_file2.exists()
        
        # Verify glyph.md is recreated with initial structure
        assert glyph_md_file.exists()
        content = glyph_md_file.read_text()
        assert "# GlyphQA System Catalog" in content
        assert "## System Insights" in content
        assert "## Pages Discovered" in content


if __name__ == "__main__":
    pytest.main([__file__])
