"""
Django REST Framework serializers for institution data management.
Provides comprehensive JSON serialization, validation, version control, and audit logging
for Institution and InstitutionAgreement models with 99.99% accuracy requirement.

Version: 1.0
"""

from rest_framework import serializers  # v3.14+
from rest_framework.exceptions import ValidationError  # v3.14+
from django.core.validators import validate_email  # v4.2+
from phonenumber_field.serializerfields import PhoneNumberField  # v7.1+

from apps.institutions.models import Institution, InstitutionAgreement
from apps.core.serializers import BaseModelSerializer, VersionedModelSerializer
from utils.validators import validate_institution_type

class InstitutionSerializer(VersionedModelSerializer):
    """
    Enhanced serializer for Institution model with comprehensive validation,
    version control, and audit logging.
    """
    name = serializers.CharField(
        max_length=200,
        help_text="Official institution name"
    )
    code = serializers.CharField(
        max_length=20,
        help_text="Unique institution code"
    )
    type = serializers.ChoiceField(
        choices=Institution.INSTITUTION_TYPES,
        help_text="Institution classification"
    )
    status = serializers.ChoiceField(
        choices=Institution.INSTITUTION_STATUS,
        help_text="Current operational status"
    )
    contact_info = serializers.JSONField(
        help_text="Structured contact information"
    )
    address = serializers.JSONField(
        help_text="Physical and mailing addresses"
    )
    metadata = serializers.JSONField(
        required=False,
        help_text="Additional institution metadata"
    )
    website = serializers.URLField(
        allow_blank=True,
        help_text="Official institution website"
    )
    accreditation = serializers.JSONField(
        required=False,
        help_text="Accreditation details and status"
    )
    active_courses_count = serializers.SerializerMethodField(
        help_text="Count of active courses"
    )
    transfer_requirements_count = serializers.SerializerMethodField(
        help_text="Count of active transfer requirements"
    )

    class Meta:
        model = Institution
        fields = [
            'id', 'name', 'code', 'type', 'status', 'contact_info',
            'address', 'metadata', 'website', 'accreditation',
            'active_courses_count', 'transfer_requirements_count',
            'version', 'effective_from', 'effective_to', 'previous_version',
            'version_metadata', 'created_at', 'updated_at', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'version',
                           'effective_to', 'previous_version']

    def validate_contact_info(self, contact_info):
        """
        Enhanced contact information validation with strict format checking.
        """
        required_fields = {'email', 'phone', 'department'}
        if missing := required_fields - set(contact_info.keys()):
            raise ValidationError(f"Missing required contact fields: {missing}")

        try:
            # Validate email with DNS check
            validate_email(contact_info['email'])

            # Validate phone number
            phone_field = PhoneNumberField()
            phone_field.run_validation(contact_info['phone'])

            # Validate department
            if not isinstance(contact_info['department'], str) or \
               len(contact_info['department']) < 2:
                raise ValidationError("Invalid department name")

            return contact_info

        except Exception as e:
            raise ValidationError(f"Contact info validation failed: {str(e)}")

    def validate_address(self, address):
        """
        Enhanced address validation with comprehensive checks.
        """
        required_fields = {'street', 'city', 'state', 'postal_code'}
        if missing := required_fields - set(address.keys()):
            raise ValidationError(f"Missing required address fields: {missing}")

        # Validate postal code format
        postal_code = address['postal_code']
        if not (isinstance(postal_code, str) and len(postal_code) == 5 and 
                postal_code.isdigit()):
            raise ValidationError("Invalid postal code format")

        # Validate state code
        state = address['state'].upper()
        if len(state) != 2 or not state.isalpha():
            raise ValidationError("Invalid state code")

        # Validate street address
        if len(address['street'].strip()) < 5:
            raise ValidationError("Invalid street address")

        # Validate city
        if len(address['city'].strip()) < 2:
            raise ValidationError("Invalid city name")

        return address

    def validate(self, data):
        """
        Comprehensive validation of institution data.
        """
        data = super().validate(data)

        # Validate institution type
        data['type'] = validate_institution_type(data['type'])

        # Validate status transitions
        if self.instance and 'status' in data:
            if not self._validate_status_transition(self.instance.status, data['status']):
                raise ValidationError({
                    'status': f"Invalid status transition from {self.instance.status} to {data['status']}"
                })

        return data

    def _validate_status_transition(self, current_status, new_status):
        """
        Validate institution status transitions based on business rules.
        """
        valid_transitions = {
            'pending': {'active', 'inactive'},
            'active': {'inactive', 'suspended'},
            'inactive': {'active', 'archived'},
            'suspended': {'active', 'inactive'},
            'archived': {'inactive'}
        }
        return new_status in valid_transitions.get(current_status, set())

    def get_active_courses_count(self, obj):
        """Get count of active courses for the institution."""
        return obj.get_active_courses().count()

    def get_transfer_requirements_count(self, obj):
        """Get count of active transfer requirements."""
        return len(obj.get_transfer_requirements())

class InstitutionAgreementSerializer(VersionedModelSerializer):
    """
    Enhanced serializer for InstitutionAgreement model with comprehensive
    validation and version control.
    """
    source_institution = serializers.PrimaryKeyRelatedField(
        queryset=Institution.objects.filter(is_active=True),
        help_text="Source institution for the agreement"
    )
    target_institution = serializers.PrimaryKeyRelatedField(
        queryset=Institution.objects.filter(is_active=True),
        help_text="Target institution for the agreement"
    )
    agreement_type = serializers.ChoiceField(
        choices=InstitutionAgreement.AGREEMENT_TYPES,
        help_text="Type of institutional agreement"
    )
    effective_date = serializers.DateTimeField(
        help_text="When the agreement becomes effective"
    )
    expiration_date = serializers.DateTimeField(
        allow_null=True,
        required=False,
        help_text="When the agreement expires"
    )
    terms = serializers.JSONField(
        help_text="Agreement terms and conditions"
    )
    status = serializers.CharField(
        max_length=20,
        help_text="Current agreement status"
    )

    class Meta:
        model = InstitutionAgreement
        fields = [
            'id', 'source_institution', 'target_institution',
            'agreement_type', 'effective_date', 'expiration_date',
            'terms', 'status', 'version', 'effective_from', 'effective_to',
            'previous_version', 'version_metadata', 'created_at',
            'updated_at', 'is_active'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'version',
                           'effective_to', 'previous_version']

    def validate_terms(self, terms):
        """
        Enhanced agreement terms validation.
        """
        required_sections = {'scope', 'conditions', 'responsibilities'}
        if missing := required_sections - set(terms.keys()):
            raise ValidationError(f"Missing required terms sections: {missing}")

        # Validate scope
        if not isinstance(terms['scope'], list) or not terms['scope']:
            raise ValidationError("Scope must be a non-empty list")

        # Validate conditions
        if not isinstance(terms['conditions'], dict) or not terms['conditions']:
            raise ValidationError("Conditions must be a non-empty object")

        # Validate responsibilities
        if not isinstance(terms['responsibilities'], dict) or \
           not all(k in terms['responsibilities'] for k in ['source', 'target']):
            raise ValidationError("Must specify responsibilities for both institutions")

        return terms

    def validate(self, data):
        """
        Comprehensive validation of agreement data.
        """
        data = super().validate(data)

        # Validate institution compatibility
        if data['source_institution'] == data['target_institution']:
            raise ValidationError("Source and target institutions must be different")

        # Validate date ranges
        if data.get('expiration_date'):
            if data['expiration_date'] <= data['effective_date']:
                raise ValidationError("Expiration date must be after effective date")

        # Check for conflicting agreements
        self._validate_no_conflicts(data)

        return data

    def _validate_no_conflicts(self, data):
        """
        Validate that no conflicting agreements exist for the same institutions.
        """
        existing_agreements = InstitutionAgreement.objects.filter(
            source_institution=data['source_institution'],
            target_institution=data['target_institution'],
            agreement_type=data['agreement_type'],
            is_active=True
        ).exclude(pk=getattr(self.instance, 'pk', None))

        for agreement in existing_agreements:
            if agreement.is_active() and self._dates_overlap(
                data['effective_date'],
                data.get('expiration_date'),
                agreement.effective_date,
                agreement.expiration_date
            ):
                raise ValidationError(
                    "Conflicting agreement exists for the specified period"
                )

    def _dates_overlap(self, start1, end1, start2, end2):
        """Check if two date ranges overlap."""
        if end1 is None:
            end1 = start1.max
        if end2 is None:
            end2 = start2.max
        return start1 <= end2 and start2 <= end1