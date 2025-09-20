"""
Tests for Birth Chart Generator

Unit tests for the birth chart generation functionality.
"""

import pytest
import numpy as np
import os
import tempfile
from PIL import Image
from unittest.mock import patch, MagicMock

# Import the modules to test
from birth_chart.calculator import BirthChartCalculator
from birth_chart.renderer import BirthChartRenderer
from birth_chart.service import generate_birth_chart, _validate_inputs, _generate_output_path

class TestBirthChartCalculator:
    """Test the birth chart calculator."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.calculator = BirthChartCalculator()
    
    def test_convert_local_to_utc(self):
        """Test local to UTC conversion."""
        # Test with Geneva coordinates
        utc_time, method = self.calculator.convert_local_to_utc(
            "1986-11-09", "16:28", 46.2044, 6.1432
        )
        
        assert isinstance(utc_time, str)
        assert ":" in utc_time
        assert method in ["timezonefinder_automatic", "timezonefinder_corrected_israel"]
    
    def test_convert_local_to_utc_invalid_coordinates(self):
        """Test UTC conversion with invalid coordinates."""
        with pytest.raises(ValueError):
            self.calculator.convert_local_to_utc(
                "1986-11-09", "16:28", 999, 999
            )
    
    def test_longitude_to_sign(self):
        """Test longitude to sign conversion."""
        assert self.calculator._longitude_to_sign(0) == "ARIES"
        assert self.calculator._longitude_to_sign(30) == "TAURUS"
        assert self.calculator._longitude_to_sign(60) == "GEMINI"
        assert self.calculator._longitude_to_sign(330) == "PISCES"
    
    def test_major_aspects_calculation(self):
        """Test major aspects calculation."""
        # Create mock planet positions
        planet_positions = {
            "Sun": {"longitude": 0.0},
            "Moon": {"longitude": 90.0},  # Square aspect
            "Mercury": {"longitude": 60.0}  # Sextile aspect
        }
        
        aspects = self.calculator._calculate_major_aspects(planet_positions)
        
        # Should find square aspect between Sun and Moon
        square_aspects = [a for a in aspects if a["aspect"] == "square"]
        assert len(square_aspects) > 0
        
        # Should find sextile aspect between Sun and Mercury
        sextile_aspects = [a for a in aspects if a["aspect"] == "sextile"]
        assert len(sextile_aspects) > 0

class TestBirthChartRenderer:
    """Test the birth chart renderer."""
    
    def setup_method(self):
        """Setup test fixtures."""
        self.renderer = BirthChartRenderer("icons")
    
    def test_longitude_to_angle(self):
        """Test longitude to angle conversion."""
        # 0° should be at top (90° in matplotlib)
        angle = self.renderer._longitude_to_angle(0)
        assert abs(angle - np.pi/2) < 0.01
        
        # 90° should be at left (0° in matplotlib)
        angle = self.renderer._longitude_to_angle(90)
        assert abs(angle) < 0.01
        
        # 180° should be at bottom (-90° in matplotlib)
        angle = self.renderer._longitude_to_angle(180)
        assert abs(angle + np.pi/2) < 0.01
    
    def test_angle_to_position(self):
        """Test angle to position conversion."""
        # Test at 0° (top)
        x, y = self.renderer._angle_to_position(np.pi/2, 1.0)
        assert abs(x) < 0.01
        assert abs(y - 1.0) < 0.01
        
        # Test at 90° (left)
        x, y = self.renderer._angle_to_position(0, 1.0)
        assert abs(x - 1.0) < 0.01
        assert abs(y) < 0.01
    
    def test_icon_loading(self):
        """Test icon loading functionality."""
        # Test loading a known icon
        icon = self.renderer._load_icon("Sun", 48)
        if icon is not None:
            assert isinstance(icon, np.ndarray)
            assert len(icon.shape) == 3  # RGBA image
            assert icon.shape[2] == 4  # Alpha channel present
    
    def test_render_birth_chart_alpha_channel(self):
        """Test that rendered chart has transparent background."""
        # Create mock chart data
        chart_data = {
            "birth_data": {
                "date": "1986-11-09",
                "time": "16:28",
                "utc_time": "15:28",
                "lat": 46.2044,
                "lon": 6.1432
            },
            "planet_positions": {
                "Sun": {"longitude": 0.0, "sign": "ARIES", "sign_degrees": 0.0, "house": 1},
                "Moon": {"longitude": 90.0, "sign": "CANCER", "sign_degrees": 0.0, "house": 4}
            },
            "house_cusps": [
                {"house_number": 1, "longitude": 0.0, "sign": "ARIES", "sign_degrees": 0.0}
            ],
            "angles": {
                "Ascendant": {"longitude": 0.0, "sign": "ARIES", "sign_degrees": 0.0},
                "MC": {"longitude": 90.0, "sign": "CANCER", "sign_degrees": 0.0}
            },
            "aspects": [],
            "chart_metadata": {"house_system": "placidus", "zodiac": "tropical", "node_type": "mean"}
        }
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp:
            temp_path = tmp.name
        
        try:
            # Render chart
            result_path = self.renderer.render_birth_chart(chart_data, temp_path)
            
            # Check that file was created
            assert os.path.exists(result_path)
            
            # Check that it's a valid PNG with alpha channel
            img = Image.open(result_path)
            assert img.mode in ['RGBA', 'LA']  # Has alpha channel
            assert img.size == (1500, 1500)  # Correct size
            
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)

class TestBirthChartService:
    """Test the birth chart service."""
    
    def test_validate_inputs_valid(self):
        """Test input validation with valid inputs."""
        # Should not raise any exception
        _validate_inputs("1986-11-09", "16:28", 46.2044, 6.1432, "placidus", "tropical")
    
    def test_validate_inputs_invalid_date(self):
        """Test input validation with invalid date."""
        with pytest.raises(ValueError, match="Invalid date format"):
            _validate_inputs("1986/11/09", "16:28", 46.2044, 6.1432, "placidus", "tropical")
    
    def test_validate_inputs_invalid_time(self):
        """Test input validation with invalid time."""
        with pytest.raises(ValueError, match="Invalid time format"):
            _validate_inputs("1986-11-09", "4:28 PM", 46.2044, 6.1432, "placidus", "tropical")
    
    def test_validate_inputs_invalid_latitude(self):
        """Test input validation with invalid latitude."""
        with pytest.raises(ValueError, match="Latitude must be between"):
            _validate_inputs("1986-11-09", "16:28", 91.0, 6.1432, "placidus", "tropical")
    
    def test_validate_inputs_invalid_longitude(self):
        """Test input validation with invalid longitude."""
        with pytest.raises(ValueError, match="Longitude must be between"):
            _validate_inputs("1986-11-09", "16:28", 46.2044, 181.0, "placidus", "tropical")
    
    def test_validate_inputs_invalid_house_system(self):
        """Test input validation with invalid house system."""
        with pytest.raises(ValueError, match="House system must be"):
            _validate_inputs("1986-11-09", "16:28", 46.2044, 6.1432, "koch", "tropical")
    
    def test_generate_output_path(self):
        """Test output path generation."""
        path = _generate_output_path("1986-11-09", "16:28", 46.2044, 6.1432)
        
        assert path.startswith("outputs/")
        assert path.endswith(".png")
        assert "19861109" in path
        assert "1628" in path
        assert "462044N" in path
        assert "61432E" in path
    
    @patch('birth_chart.service.BirthChartCalculator')
    @patch('birth_chart.service.BirthChartRenderer')
    def test_generate_birth_chart_integration(self, mock_renderer, mock_calculator):
        """Test the complete birth chart generation process."""
        # Setup mocks
        mock_calc_instance = MagicMock()
        mock_calculator.return_value = mock_calc_instance
        
        mock_renderer_instance = MagicMock()
        mock_renderer.return_value = mock_renderer_instance
        
        # Mock chart data
        mock_chart_data = {
            "birth_data": {"date": "1986-11-09", "time": "16:28"},
            "planet_positions": {},
            "house_cusps": [],
            "angles": {},
            "aspects": [],
            "chart_metadata": {}
        }
        mock_calc_instance.calculate_birth_chart.return_value = mock_chart_data
        mock_renderer_instance.render_birth_chart.return_value = "test_output.png"
        
        # Test the service
        result = generate_birth_chart(
            date="1986-11-09",
            time="16:28",
            lat=46.2044,
            lon=6.1432
        )
        
        # Verify calls
        mock_calculator.assert_called_once()
        mock_renderer.assert_called_once_with("icons")
        mock_calc_instance.calculate_birth_chart.assert_called_once()
        mock_renderer_instance.render_birth_chart.assert_called_once()
        
        assert result == "test_output.png"

if __name__ == "__main__":
    pytest.main([__file__])
