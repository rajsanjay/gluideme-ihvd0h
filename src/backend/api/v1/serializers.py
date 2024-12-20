"""
Django REST Framework serializers for the Transfer Requirements Management System API v1.
Implements comprehensive validation logic, version control, and real-time validation
with 99.99% accuracy target.

Version: 1.0
"""

from rest_framework import serializers  # v3.14+
from rest_framework.exceptions import ValidationError  # v3.14+
from django.core.cache import cache  # v4.2+
from django.utils import timezone
from django.db import transaction
from apps.courses.models import Course
from apps.requirements.models import TransferRequirement
from apps.institutions.models import Institution
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

# Cache TTL settings
VALIDATION_CACHE_TTL = 3600  # 1 hour
METADATA_CACHE_TTL = 1800  # 30 minutes

class InstitutionSerializer(serializers.ModelSerializer):
    """
    Serializer for Institution model with enhanced validation and caching.
    """
    class Meta:
        model = Institution
        fields = [
            'id', 'name', 'code', 'type', 'status', 'contact_info',
            'address', 'metadata', 'website', 'accreditation',
            'last_verified', 'version'
        ]
        read_only_fields = ['last_verified']

    def validate_contact_info(self, value: Dict) -> Dict:
        """Validate contact information structure."""
        required_fields = {'email', 'phone', 'department'}
        missing_fields = required_fields - set(value.keys())
        
        if missing_fields:
            raise ValidationError(
                f"Missing required contact fields: {', '.join(missing_fields)}"
            )
        return value

    def validate_address(self, value: Dict) -> Dict:
        """Validate address components."""
        required_fields = {'street', 'city', 'state', 'postal_code'}
        missing_fields = required_fields - set(value.keys())
        
        if missing_fields:
            raise ValidationError(
                f"Missing required address fields: {', '.join(missing_fields)}"
            )
        return value

class CourseSerializer(serializers.ModelSerializer):
    """
    Serializer for Course model with enhanced validation logic and caching.
    Implements comprehensive validation for credits, prerequisites, and metadata.
    """
    prerequisites = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Course.objects.all(),
        required=False
    )

    class Meta:
        model = Course
        fields = [
            'id', 'institution', 'code', 'name', 'description',
            'credits', 'prerequisites', 'metadata', 'status',
            'valid_from', 'valid_to', 'last_validated',
            'validation_errors', 'version'
        ]
        read_only_fields = ['last_validated', 'validation_errors']

    def validate_credits(self, value: float) -> float:
        """
        Validate course credits with enhanced accuracy checks.
        Implements caching for validation results.
        """
        cache_key = f"course_credits_validation:{value}"
        cached_result = cache.get(cache_key)
        
        if cached_result is not None:
            if isinstance(cached_result, Exception):
                raise cached_result
            return cached_result

        try:
            if value <= 0:
                raise ValidationError("Credits must be greater than 0")
            
            if value > 12:
                raise ValidationError("Credits cannot exceed 12")
            
            # Validate credit increments (0.25)
            if round(value * 4) != value * 4:
                raise ValidationError("Credits must be in increments of 0.25")
            
            cache.set(cache_key, value, VALIDATION_CACHE_TTL)
            return value
            
        except ValidationError as e:
            cache.set(cache_key, e, VALIDATION_CACHE_TTL)
            raise

    def validate_prerequisites(self, value: List[Course]) -> List[Course]:
        """
        Validate course prerequisites with circular dependency detection.
        Implements caching for validation results.
        """
        cache_key = f"course_prereq_validation:{':'.join(str(c.id) for c in value)}"
        cached_result = cache.get(cache_key)
        
        if cached_result is not None:
            if isinstance(cached_result, Exception):
                raise cached_result
            return cached_result

        try:
            # Build prerequisite graph
            prereq_graph = {course: set() for course in value}
            for course in value:
                for prereq in course.prerequisites.all():
                    prereq_graph[course].add(prereq)
            
            # Check for cycles
            def has_cycle(course: Course, visited: set, path: set) -> bool:
                visited.add(course)
                path.add(course)
                
                for prereq in prereq_graph[course]:
                    if prereq not in visited:
                        if has_cycle(prereq, visited, path):
                            return True
                    elif prereq in path:
                        return True
                
                path.remove(course)
                return False

            visited = set()
            for course in value:
                if course not in visited:
                    if has_cycle(course, visited, set()):
                        raise ValidationError("Circular prerequisite dependency detected")
            
            cache.set(cache_key, value, VALIDATION_CACHE_TTL)
            return value
            
        except ValidationError as e:
            cache.set(cache_key, e, VALIDATION_CACHE_TTL)
            raise

class TransferRequirementSerializer(serializers.ModelSerializer):
    """
    Serializer for TransferRequirement model with version control and real-time validation.
    Implements comprehensive validation for transfer rules and requirements.
    """
    validation_summary = serializers.SerializerMethodField()

    class Meta:
        model = TransferRequirement
        fields = [
            'id', 'source_institution', 'target_institution',
            'major_code', 'title', 'description', 'type',
            'rules', 'metadata', 'status', 'effective_date',
            'expiration_date', 'validation_accuracy',
            'validation_summary', 'version'
        ]
        read_only_fields = ['validation_accuracy', 'validation_summary']

    def get_validation_summary(self, obj: TransferRequirement) -> Dict[str, Any]:
        """Get cached validation summary or compute if needed."""
        cache_key = f"requirement_validation_summary:{obj.id}"
        cached_summary = cache.get(cache_key)
        
        if cached_summary is not None:
            return cached_summary

        summary = {
            'total_validations': obj.metadata.get('validation_count', 0),
            'accuracy_percentage': obj.validation_accuracy,
            'last_validation': obj.metadata.get('last_validation'),
            'status': 'valid' if obj.validation_accuracy >= 99.99 else 'needs_review'
        }
        
        cache.set(cache_key, summary, METADATA_CACHE_TTL)
        return summary

    @transaction.atomic
    def validate_rules(self, value: Dict) -> Dict:
        """
        Validate requirement rules with schema validation and conflict detection.
        Implements caching for validation results.
        """
        cache_key = f"requirement_rules_validation:{hash(str(value))}"
        cached_result = cache.get(cache_key)
        
        if cached_result is not None:
            if isinstance(cached_result, Exception):
                raise cached_result
            return cached_result

        try:
            # Validate required rule components
            required_components = {'courses', 'min_credits', 'prerequisites'}
            missing_components = required_components - set(value.keys())
            if missing_components:
                raise ValidationError(
                    f"Missing required rule components: {', '.join(missing_components)}"
                )

            # Validate course rules
            courses = value.get('courses', [])
            if not courses:
                raise ValidationError("At least one course must be specified")

            # Validate minimum credits
            min_credits = value.get('min_credits', 0)
            if min_credits <= 0:
                raise ValidationError("Minimum credits must be greater than 0")

            # Validate prerequisites structure
            prerequisites = value.get('prerequisites', {})
            for course_code, prereq_list in prerequisites.items():
                if not isinstance(prereq_list, list):
                    raise ValidationError(
                        f"Prerequisites for {course_code} must be a list"
                    )

            # Check for prerequisite conflicts
            self._validate_prerequisite_conflicts(prerequisites)
            
            cache.set(cache_key, value, VALIDATION_CACHE_TTL)
            return value
            
        except ValidationError as e:
            cache.set(cache_key, e, VALIDATION_CACHE_TTL)
            raise

    def _validate_prerequisite_conflicts(self, prerequisites: Dict) -> None:
        """Helper method to detect prerequisite conflicts."""
        def check_conflicts(course: str, chain: List[str]) -> None:
            if course in chain:
                raise ValidationError(
                    f"Circular prerequisite chain detected: {' -> '.join(chain + [course])}"
                )
            
            prereqs = prerequisites.get(course, [])
            for prereq in prereqs:
                check_conflicts(prereq, chain + [course])

        for course in prerequisites:
            check_conflicts(course, [])

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive validation of the entire requirement.
        Implements additional cross-field validations.
        """
        # Validate institutional relationship
        source = data.get('source_institution')
        target = data.get('target_institution')
        if source and target and source.id == target.id:
            raise ValidationError(
                "Source and target institutions must be different"
            )

        # Validate date ranges
        effective_date = data.get('effective_date', timezone.now())
        expiration_date = data.get('expiration_date')
        if expiration_date and effective_date >= expiration_date:
            raise ValidationError(
                "Expiration date must be after effective date"
            )

        # Validate status transitions
        if self.instance:
            old_status = self.instance.status
            new_status = data.get('status', old_status)
            valid_transitions = {
                'draft': {'published', 'archived'},
                'published': {'archived'},
                'archived': set()
            }
            if new_status != old_status and new_status not in valid_transitions.get(old_status, set()):
                raise ValidationError(
                    f"Invalid status transition from {old_status} to {new_status}"
                )

        return data