"""
Django REST Framework serializers for course data management.
Implements comprehensive validation, serialization, and error handling for courses and equivalencies.

Version: 1.0
"""

from rest_framework import serializers  # v3.14+
from rest_framework.exceptions import ValidationError  # v3.14+
from django.core.cache import cache  # v4.2+
from django.utils import timezone
from apps.courses.models import Course, CourseEquivalency
from apps.institutions.models import Institution
from utils.validators import validate_course_code, validate_credits
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class CourseSerializer(serializers.ModelSerializer):
    """
    Enhanced serializer for Course model with comprehensive validation and caching.
    Implements field-level and object-level validation with error handling.
    """
    institution = serializers.PrimaryKeyRelatedField(
        queryset=Institution.objects.filter(status='active'),
        help_text="Institution offering the course"
    )
    prerequisites = serializers.PrimaryKeyRelatedField(
        many=True,
        required=False,
        queryset=Course.objects.filter(is_active=True),
        help_text="Required prerequisite courses"
    )
    metadata = serializers.JSONField(
        required=False,
        help_text="Additional course metadata"
    )
    version = serializers.CharField(read_only=True)
    validation_status = serializers.SerializerMethodField(
        help_text="Current validation status"
    )

    class Meta:
        model = Course
        fields = [
            'id', 'institution', 'code', 'name', 'description', 'credits',
            'prerequisites', 'metadata', 'status', 'valid_from', 'valid_to',
            'version', 'validation_status', 'last_validated', 'validation_errors'
        ]
        read_only_fields = ['id', 'version', 'last_validated', 'validation_errors']

    def get_validation_status(self, obj: Course) -> str:
        """
        Calculate current validation status based on validation errors.
        
        Args:
            obj: Course instance
            
        Returns:
            str: Current validation status
        """
        if not obj.validation_errors:
            return 'valid'
        return 'invalid'

    def validate_code(self, value: str) -> str:
        """
        Enhanced course code validation with duplicate checking.
        
        Args:
            value: Course code to validate
            
        Returns:
            str: Validated course code
            
        Raises:
            ValidationError: If code is invalid or duplicate
        """
        try:
            # Normalize and validate code format
            validated_code = validate_course_code(value)
            
            # Check for duplicates within institution
            institution = self.initial_data.get('institution')
            if institution and Course.objects.filter(
                institution=institution,
                code=validated_code
            ).exclude(pk=self.instance.pk if self.instance else None).exists():
                raise ValidationError("Course code already exists for this institution")
                
            return validated_code
            
        except Exception as e:
            logger.error(f"Course code validation failed: {str(e)}", exc_info=True)
            raise ValidationError(f"Invalid course code: {str(e)}")

    def validate_credits(self, value: Any) -> float:
        """
        Enhanced credit validation with institutional policy checks.
        
        Args:
            value: Credit value to validate
            
        Returns:
            float: Validated credits value
            
        Raises:
            ValidationError: If credits are invalid
        """
        try:
            validated_credits = validate_credits(value)
            
            # Check institutional credit policies
            institution = self.initial_data.get('institution')
            if institution:
                institution_obj = Institution.objects.get(pk=institution)
                max_credits = institution_obj.metadata.get('max_course_credits', 12.0)
                if validated_credits > max_credits:
                    raise ValidationError(f"Credits exceed institution maximum of {max_credits}")
                    
            return validated_credits
            
        except Exception as e:
            logger.error(f"Credit validation failed: {str(e)}", exc_info=True)
            raise ValidationError(f"Invalid credits: {str(e)}")

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive object-level validation with enhanced error handling.
        
        Args:
            data: Course data to validate
            
        Returns:
            Dict: Validated course data
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            # Validate temporal consistency
            if data.get('valid_to') and data.get('valid_from'):
                if data['valid_to'] <= data['valid_from']:
                    raise ValidationError({
                        'valid_to': "End date must be after start date"
                    })

            # Validate prerequisites
            if 'prerequisites' in data:
                self._validate_prerequisites_chain(data['prerequisites'])

            # Validate metadata schema
            if 'metadata' in data:
                self._validate_metadata_schema(data['metadata'])

            # Cache validation result
            cache_key = f"course_validation:{data.get('institution')}:{data.get('code')}"
            cache.set(cache_key, True, timeout=3600)  # Cache for 1 hour

            return data

        except Exception as e:
            logger.error(f"Course validation failed: {str(e)}", exc_info=True)
            raise ValidationError(f"Validation failed: {str(e)}")

    def _validate_prerequisites_chain(self, prerequisites: List[Course]) -> None:
        """
        Validate prerequisite chain for cycles and consistency.
        
        Args:
            prerequisites: List of prerequisite courses
            
        Raises:
            ValidationError: If prerequisite chain is invalid
        """
        visited = set()
        
        def check_cycle(course: Course, path: set) -> None:
            if course.id in path:
                raise ValidationError({
                    'prerequisites': f"Circular dependency detected in prerequisites"
                })
            path.add(course.id)
            for prereq in course.prerequisites.all():
                check_cycle(prereq, path.copy())

        for prereq in prerequisites:
            check_cycle(prereq, visited.copy())

    def _validate_metadata_schema(self, metadata: Dict[str, Any]) -> None:
        """
        Validate course metadata against required schema.
        
        Args:
            metadata: Metadata to validate
            
        Raises:
            ValidationError: If metadata schema is invalid
        """
        required_fields = {'delivery_mode', 'learning_outcomes'}
        missing_fields = required_fields - set(metadata.keys())
        
        if missing_fields:
            raise ValidationError({
                'metadata': f"Missing required fields: {', '.join(missing_fields)}"
            })

class CourseEquivalencySerializer(serializers.ModelSerializer):
    """
    Enhanced serializer for CourseEquivalency with comprehensive validation.
    Implements audit logging and temporal validation.
    """
    source_course = CourseSerializer(read_only=True)
    target_course = CourseSerializer(read_only=True)
    source_course_id = serializers.PrimaryKeyRelatedField(
        queryset=Course.objects.filter(is_active=True),
        write_only=True,
        source='source_course'
    )
    target_course_id = serializers.PrimaryKeyRelatedField(
        queryset=Course.objects.filter(is_active=True),
        write_only=True,
        source='target_course'
    )
    metadata = serializers.JSONField(required=False)
    audit_log = serializers.JSONField(read_only=True)

    class Meta:
        model = CourseEquivalency
        fields = [
            'id', 'source_course', 'target_course', 'source_course_id',
            'target_course_id', 'effective_date', 'expiration_date', 'metadata',
            'notes', 'validation_status', 'last_reviewed', 'reviewed_by',
            'audit_log'
        ]
        read_only_fields = ['id', 'last_reviewed', 'audit_log']

    def validate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive equivalency validation with audit logging.
        
        Args:
            data: Equivalency data to validate
            
        Returns:
            Dict: Validated equivalency data
            
        Raises:
            ValidationError: If validation fails
        """
        try:
            # Validate institutional relationship
            if data['source_course'].institution == data['target_course'].institution:
                raise ValidationError(
                    "Source and target courses must be from different institutions"
                )

            # Validate temporal consistency
            if data.get('expiration_date') and data.get('effective_date'):
                if data['expiration_date'] <= data['effective_date']:
                    raise ValidationError({
                        'expiration_date': "Expiration date must be after effective date"
                    })

            # Validate course compatibility
            self._validate_course_compatibility(
                data['source_course'],
                data['target_course']
            )

            # Update audit log
            data['audit_log'] = self._update_audit_log(data)

            return data

        except Exception as e:
            logger.error(f"Equivalency validation failed: {str(e)}", exc_info=True)
            raise ValidationError(f"Validation failed: {str(e)}")

    def _validate_course_compatibility(self, source: Course, target: Course) -> None:
        """
        Validate compatibility between source and target courses.
        
        Args:
            source: Source course
            target: Target course
            
        Raises:
            ValidationError: If courses are incompatible
        """
        # Validate credit compatibility
        credit_difference = abs(source.credits - target.credits)
        if credit_difference > 1.0:  # Allow 1 credit difference
            raise ValidationError(
                "Credit difference between courses exceeds maximum allowed"
            )

        # Validate course levels
        source_level = int(''.join(filter(str.isdigit, source.code[:3])))
        target_level = int(''.join(filter(str.isdigit, target.code[:3])))
        if abs(source_level - target_level) > 100:  # Allow one level difference
            raise ValidationError(
                "Course level difference exceeds maximum allowed"
            )

    def _update_audit_log(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Update audit log with current changes.
        
        Args:
            data: Current equivalency data
            
        Returns:
            List: Updated audit log entries
        """
        audit_entry = {
            'timestamp': timezone.now().isoformat(),
            'action': 'update' if self.instance else 'create',
            'changes': {
                field: value for field, value in data.items()
                if self.instance is None or getattr(self.instance, field) != value
            },
            'user': str(self.context['request'].user.id)
        }

        existing_log = self.instance.audit_log if self.instance else []
        return existing_log + [audit_entry]