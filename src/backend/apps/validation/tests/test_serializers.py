"""
Unit tests for validation app serializers ensuring proper serialization, validation, 
and error handling for validation records and cache entries with comprehensive coverage.

Version: 1.0
"""

# Django imports - v4.2+
from django.test import TestCase
from django.utils import timezone

# DRF imports - v3.14+
from rest_framework.exceptions import ValidationError
from rest_framework import status

# Internal imports
from apps.validation.serializers import ValidationRecordSerializer, ValidationCacheSerializer
from apps.validation.models import ValidationRecord, ValidationCache
from apps.requirements.models import TransferRequirement
from apps.courses.models import Course
from apps.institutions.models import Institution

class ValidationRecordSerializerTests(TestCase):
    """
    Comprehensive test cases for validation record serialization and validation logic 
    with accuracy metrics.
    """

    def setUp(self):
        """Set up test data with comprehensive validation scenarios."""
        # Create test institutions
        self.source_institution = Institution.objects.create(
            name="Test Community College",
            code="TCC",
            type="community_college",
            status="active"
        )
        self.target_institution = Institution.objects.create(
            name="Test University",
            code="TU",
            type="university",
            status="active"
        )

        # Create test requirement
        self.requirement = TransferRequirement.objects.create(
            source_institution=self.source_institution,
            target_institution=self.target_institution,
            major_code="CS",
            title="Computer Science Requirements",
            type="major",
            rules={
                "courses": ["CS 101", "CS 102"],
                "min_credits": 6,
                "prerequisites": {}
            },
            status="published"
        )

        # Create test course
        self.course = Course.objects.create(
            institution=self.source_institution,
            code="CS 101",
            name="Introduction to Programming",
            credits=3.0,
            status="active"
        )

        # Create test validation record
        self.validation_record = ValidationRecord.objects.create(
            requirement=self.requirement,
            course=self.course,
            status="valid",
            results={
                "valid": True,
                "completion_percentage": 100.0,
                "validation_timestamp": timezone.now().isoformat()
            }
        )

        # Set up test data for serializer
        self.valid_data = {
            "requirement": self.requirement.id,
            "course": self.course.id,
            "status": "valid",
            "results": {
                "valid": True,
                "completion_percentage": 100.0,
                "validation_timestamp": timezone.now().isoformat()
            }
        }

        # Initialize serializer
        self.serializer = ValidationRecordSerializer(instance=self.validation_record)

    def test_valid_serialization(self):
        """Test successful serialization with accuracy metrics."""
        # Create serializer with valid data
        serializer = ValidationRecordSerializer(data=self.valid_data)
        
        # Verify serializer is valid
        self.assertTrue(serializer.is_valid())
        
        # Check all required fields are present
        self.assertIn('requirement', serializer.validated_data)
        self.assertIn('course', serializer.validated_data)
        self.assertIn('status', serializer.validated_data)
        self.assertIn('results', serializer.validated_data)
        
        # Verify read-only fields
        self.assertIn('validated_at', serializer.fields)
        self.assertIn('valid_until', serializer.fields)
        self.assertIn('accuracy_metrics', serializer.fields)
        
        # Test serialized data format
        data = serializer.data
        self.assertEqual(data['requirement'], str(self.requirement.id))
        self.assertEqual(data['course'], str(self.course.id))
        self.assertEqual(data['status'], 'valid')
        
        # Verify accuracy metrics
        self.assertIn('accuracy_metrics', data)
        self.assertIn('validation_history', data)
        self.assertIn('progress_metadata', data)

    def test_validation_with_invalid_data(self):
        """Test validation error handling with detailed scenarios."""
        # Test missing required fields
        invalid_data = {}
        serializer = ValidationRecordSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('requirement', serializer.errors)
        self.assertIn('course', serializer.errors)
        
        # Test invalid requirement reference
        invalid_data = self.valid_data.copy()
        invalid_data['requirement'] = "invalid-uuid"
        serializer = ValidationRecordSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('requirement', serializer.errors)
        
        # Test invalid status choice
        invalid_data = self.valid_data.copy()
        invalid_data['status'] = 'invalid_status'
        serializer = ValidationRecordSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('status', serializer.errors)
        
        # Test invalid results format
        invalid_data = self.valid_data.copy()
        invalid_data['results'] = "not_a_dict"
        serializer = ValidationRecordSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('results', serializer.errors)

    def test_bulk_validation(self):
        """Test bulk validation operations with performance metrics."""
        # Create multiple test courses
        course2 = Course.objects.create(
            institution=self.source_institution,
            code="CS 102",
            name="Data Structures",
            credits=3.0,
            status="active"
        )
        
        # Prepare bulk validation data
        bulk_data = [
            self.valid_data,
            {
                "requirement": self.requirement.id,
                "course": course2.id,
                "status": "valid",
                "results": {
                    "valid": True,
                    "completion_percentage": 100.0,
                    "validation_timestamp": timezone.now().isoformat()
                }
            }
        ]
        
        # Test bulk validation
        serializer = ValidationRecordSerializer()
        results = serializer.bulk_validate(bulk_data)
        
        # Verify bulk results
        self.assertEqual(len(results), 2)
        self.assertTrue(all(r['status'] == 'valid' for r in results))
        
        # Check accuracy metrics for each result
        for result in results:
            self.assertIn('accuracy_metrics', result)
            self.assertIn('validation_score', result['accuracy_metrics'])
            self.assertIn('confidence_level', result['accuracy_metrics'])

class ValidationCacheSerializerTests(TestCase):
    """Test cases for validation cache serialization with expiration handling."""

    def setUp(self):
        """Set up cache test scenarios."""
        # Create test data
        self.requirement = TransferRequirement.objects.create(
            source_institution=Institution.objects.create(
                name="Test College",
                code="TC",
                type="community_college"
            ),
            target_institution=Institution.objects.create(
                name="Test University",
                code="TU",
                type="university"
            ),
            major_code="CS",
            title="Computer Science Cache Test",
            type="major",
            status="published"
        )
        
        self.course = Course.objects.create(
            institution=self.requirement.source_institution,
            code="CS 101",
            name="Programming Cache Test",
            credits=3.0,
            status="active"
        )
        
        # Create test cache entry
        self.cache_entry = ValidationCache.objects.create(
            requirement=self.requirement,
            course=self.course,
            cache_key=f"validation:{self.requirement.id}:{self.course.id}",
            results={
                "valid": True,
                "cached_at": timezone.now().isoformat()
            },
            expires_at=timezone.now() + timezone.timedelta(days=1)
        )
        
        # Set up serializer
        self.serializer = ValidationCacheSerializer(instance=self.cache_entry)

    def test_cache_validation(self):
        """Test cache validation with expiration scenarios."""
        # Test valid cache data
        valid_data = {
            "requirement": self.requirement.id,
            "course": self.course.id
        }
        serializer = ValidationCacheSerializer(data=valid_data)
        self.assertTrue(serializer.is_valid())
        
        # Verify cache key generation
        validated_data = serializer.validated_data
        self.assertIn('cache_key', validated_data)
        self.assertTrue(validated_data['cache_key'].startswith('validation:'))
        
        # Test cache metadata
        data = serializer.data
        self.assertIn('cache_metadata', data)
        self.assertIn('performance_metrics', data)
        self.assertIn('hit_count', data)

    def test_cache_invalidation(self):
        """Test cache invalidation and refresh logic."""
        # Test expired cache
        self.cache_entry.expires_at = timezone.now() - timezone.timedelta(hours=1)
        self.cache_entry.save()
        
        serializer = ValidationCacheSerializer(instance=self.cache_entry)
        data = serializer.data
        
        # Verify cache status
        self.assertEqual(data['cache_metadata']['cache_status'], 'miss')
        
        # Test cache refresh
        new_results = {
            "valid": True,
            "cached_at": timezone.now().isoformat()
        }
        self.cache_entry.refresh(new_results)
        
        # Verify refreshed cache
        updated_serializer = ValidationCacheSerializer(instance=self.cache_entry)
        updated_data = updated_serializer.data
        self.assertEqual(updated_data['results'], new_results)
        self.assertTrue(updated_data['expires_at'] > timezone.now().isoformat())