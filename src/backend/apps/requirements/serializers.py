"""
Django REST Framework serializers for transfer requirements management.
Implements comprehensive validation, versioning, and audit logging for transfer requirements.

Version: 1.0
"""

# Django REST Framework v3.14+
from rest_framework import serializers
from django.utils import timezone
from django.core.cache import cache
from rest_framework.exceptions import ValidationError

# Internal imports
from apps.requirements.models import TransferRequirement, RequirementCourse
from apps.core.serializers import BaseModelSerializer, VersionedModelSerializer
from apps.institutions.models import Institution
from utils.validators import validate_requirement_rules
from typing import Dict, Any, List

# Cache TTL for validation results
VALIDATION_CACHE_TTL = 3600  # 1 hour

class RequirementCourseSerializer(BaseModelSerializer):
    """
    Enhanced serializer for course mappings with comprehensive validation.
    Implements detailed course relationship validation with caching.
    """
    source_course = serializers.PrimaryKeyRelatedField(
        queryset=Institution.objects.all(),
        help_text="Source course for mapping"
    )
    target_course = serializers.PrimaryKeyRelatedField(
        queryset=Institution.objects.all(),
        help_text="Target course for mapping"
    )
    metadata = serializers.JSONField(
        required=False,
        default=dict,
        help_text="Additional mapping metadata"
    )
    validation_status = serializers.CharField(read_only=True)
    last_validated = serializers.DateTimeField(read_only=True)

    class Meta:
        model = RequirementCourse
        fields = [
            'id', 'source_course', 'target_course', 'metadata',
            'validation_status', 'last_validated', 'created_at',
            'updated_at', 'is_active'
        ]
        read_only_fields = ['validation_status', 'last_validated']

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhanced validation of course mapping with comprehensive checks.
        
        Args:
            data: Course mapping data
            
        Returns:
            Dict: Validated data
        """
        try:
            # Validate course relationship
            if data['source_course'].institution == data['target_course'].institution:
                raise ValidationError({
                    'courses': "Source and target courses must be from different institutions"
                })

            # Validate course statuses
            for course_field in ['source_course', 'target_course']:
                course = data[course_field]
                if not course.is_active:
                    raise ValidationError({
                        course_field: f"Course {course.code} is not active"
                    })

            # Validate metadata schema
            if metadata := data.get('metadata'):
                required_fields = {'equivalency_type', 'approval_date', 'reviewer_id'}
                if not all(field in metadata for field in required_fields):
                    raise ValidationError({
                        'metadata': f"Missing required metadata fields: {required_fields}"
                    })

            # Cache validation result
            cache_key = f"course_mapping_validation:{data['source_course'].id}:{data['target_course'].id}"
            cache.set(cache_key, data, timeout=VALIDATION_CACHE_TTL)

            return data

        except Exception as e:
            raise ValidationError({
                'validation': f"Course mapping validation failed: {str(e)}"
            })

class TransferRequirementSerializer(VersionedModelSerializer):
    """
    Enhanced serializer for transfer requirements with comprehensive validation.
    Implements versioning, caching, and detailed validation rules.
    """
    source_institution = serializers.PrimaryKeyRelatedField(
        queryset=Institution.objects.all(),
        help_text="Source institution for requirement"
    )
    target_institution = serializers.PrimaryKeyRelatedField(
        queryset=Institution.objects.all(),
        help_text="Target institution for requirement"
    )
    courses = RequirementCourseSerializer(
        many=True,
        required=False,
        help_text="Associated course mappings"
    )
    major_code = serializers.CharField(
        max_length=20,
        help_text="Major code for requirement"
    )
    rules = serializers.JSONField(
        help_text="Structured validation rules"
    )
    metadata = serializers.JSONField(
        required=False,
        default=dict,
        help_text="Additional requirement metadata"
    )
    validation_accuracy = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        read_only=True,
        help_text="Calculated validation accuracy"
    )

    class Meta:
        model = TransferRequirement
        fields = [
            'id', 'source_institution', 'target_institution', 'major_code',
            'courses', 'rules', 'metadata', 'status', 'effective_date',
            'expiration_date', 'validation_accuracy', 'version', 'created_at',
            'updated_at', 'is_active'
        ]
        read_only_fields = [
            'validation_accuracy', 'version', 'created_at', 'updated_at'
        ]

    def validate_rules(self, rules: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhanced validation of requirement rules with caching.
        
        Args:
            rules: Requirement rules to validate
            
        Returns:
            Dict: Validated rules
        """
        try:
            # Check cache for validated rules
            cache_key = f"requirement_rules:{hash(str(rules))}"
            cached_rules = cache.get(cache_key)
            if cached_rules:
                return cached_rules

            # Validate rule structure
            validate_requirement_rules(rules)

            # Validate credit requirements
            if 'min_credits' not in rules:
                raise ValidationError({
                    'rules': "Missing minimum credit requirement"
                })

            # Validate course prerequisites
            if prerequisites := rules.get('prerequisites'):
                self._validate_prerequisites(prerequisites)

            # Cache validated rules
            cache.set(cache_key, rules, timeout=VALIDATION_CACHE_TTL)
            return rules

        except Exception as e:
            raise ValidationError({
                'rules': f"Rule validation failed: {str(e)}"
            })

    def _validate_prerequisites(self, prerequisites: Dict[str, List[str]]) -> None:
        """
        Validate prerequisite relationships for cycles and consistency.
        
        Args:
            prerequisites: Prerequisite course mappings
        """
        visited = set()
        
        def check_cycle(course_code: str, path: List[str]) -> None:
            if course_code in path:
                raise ValidationError({
                    'prerequisites': f"Circular dependency detected: {' -> '.join(path)}"
                })
            
            path.append(course_code)
            for prereq in prerequisites.get(course_code, []):
                check_cycle(prereq, path.copy())

        for course_code in prerequisites:
            check_cycle(course_code, [])

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive validation with enhanced error handling.
        
        Args:
            data: Requirement data to validate
            
        Returns:
            Dict: Validated data
        """
        try:
            # Validate institution relationship
            if data['source_institution'] == data['target_institution']:
                raise ValidationError({
                    'institutions': "Source and target institutions must be different"
                })

            # Validate institution statuses
            for inst_field in ['source_institution', 'target_institution']:
                institution = data[inst_field]
                if institution.status != 'active':
                    raise ValidationError({
                        inst_field: f"Institution {institution.name} is not active"
                    })

            # Validate date ranges
            if data.get('expiration_date') and data['effective_date'] >= data['expiration_date']:
                raise ValidationError({
                    'expiration_date': "Expiration date must be after effective date"
                })

            # Validate metadata
            if metadata := data.get('metadata'):
                required_fields = {'version_notes', 'reviewer_id', 'approval_date'}
                if not all(field in metadata for field in required_fields):
                    raise ValidationError({
                        'metadata': f"Missing required metadata fields: {required_fields}"
                    })

            # Validate version transition if updating
            if self.instance:
                self.validate_version_transition(data)

            return data

        except Exception as e:
            raise ValidationError({
                'validation': f"Requirement validation failed: {str(e)}"
            })