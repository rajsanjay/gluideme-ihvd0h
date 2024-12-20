"""
Comprehensive unit tests for Institution and InstitutionAgreement models.
Focuses on validation, versioning, and data integrity with 99.99% accuracy target.

Version: 1.0
"""

import pytest  # v7.0+
from freezegun import freeze_time  # v1.2+
from django.core.exceptions import ValidationError  # v4.2+
from django.utils import timezone  # v4.2+
from django.core.cache import cache  # v4.2+
from apps.institutions.models import Institution, InstitutionAgreement
from datetime import timedelta
import uuid

@pytest.fixture
def institution_factory(db):
    """
    Fixture providing a factory for creating test institutions with comprehensive defaults.
    """
    def create_institution(**overrides):
        default_data = {
            'name': 'Test University',
            'code': f'TU{uuid.uuid4().hex[:6].upper()}',
            'type': 'university',
            'status': 'active',
            'contact_info': {
                'email': 'contact@test.edu',
                'phone': '555-0123',
                'department': 'Admissions'
            },
            'address': {
                'street': '123 University Ave',
                'city': 'Test City',
                'state': 'CA',
                'postal_code': '94000'
            },
            'metadata': {
                'founded': 1950,
                'accreditation_status': 'full'
            },
            'website': 'https://test.edu',
            'accreditation': {
                'body': 'Test Accreditation Board',
                'status': 'active',
                'expiration_date': '2025-12-31'
            }
        }
        default_data.update(overrides)
        return Institution.objects.create(**default_data)
    return create_institution

@pytest.fixture
def agreement_factory(db, institution_factory):
    """
    Fixture providing a factory for creating test institution agreements.
    """
    def create_agreement(**overrides):
        source_inst = institution_factory()
        target_inst = institution_factory()
        
        default_data = {
            'source_institution': source_inst,
            'target_institution': target_inst,
            'agreement_type': 'articulation',
            'effective_from': timezone.now(),
            'effective_to': timezone.now() + timedelta(days=365),
            'metadata': {
                'renewal_terms': 'Annual review required',
                'contact_person': 'John Doe'
            },
            'status': 'active'
        }
        default_data.update(overrides)
        return InstitutionAgreement.objects.create(**default_data)
    return create_agreement

@pytest.mark.django_db
class TestInstitution:
    """
    Comprehensive test suite for Institution model covering validation,
    versioning, and caching functionality.
    """
    
    def test_create_institution_success(self, institution_factory):
        """Test successful institution creation with valid data."""
        institution = institution_factory()
        assert institution.pk is not None
        assert institution.version == 1
        assert institution.is_active is True
        
        # Verify cache update
        cached_inst = cache.get(f"institution:{institution.pk}")
        assert cached_inst is not None

    def test_institution_validation(self, institution_factory):
        """Test comprehensive validation rules for institution data."""
        # Test invalid contact info
        with pytest.raises(ValidationError) as exc:
            institution_factory(contact_info={})
        assert 'contact_info' in str(exc.value)
        
        # Test invalid address
        with pytest.raises(ValidationError) as exc:
            institution_factory(address={'street': '123'})
        assert 'address' in str(exc.value)
        
        # Test invalid institution type
        with pytest.raises(ValidationError) as exc:
            institution_factory(type='invalid_type')
        assert 'type' in str(exc.value)
        
        # Test invalid accreditation
        with pytest.raises(ValidationError) as exc:
            institution_factory(accreditation={'status': 'active'})
        assert 'accreditation' in str(exc.value)

    @freeze_time('2023-01-01')
    def test_institution_versioning(self, institution_factory):
        """Test temporal versioning functionality."""
        institution = institution_factory()
        
        # Create new version
        updated_data = {
            'name': 'Updated University',
            'metadata': {'updated': True}
        }
        new_version = institution.create_new_version(
            data=updated_data,
            reason='Name update',
            effective_date=timezone.now() + timedelta(days=30)
        )
        
        # Verify version chain
        assert new_version.version == 2
        assert new_version.previous_version == institution.pk
        assert institution.effective_to == new_version.effective_from
        
        # Test version retrieval
        past_version = institution.get_version_at(timezone.now())
        assert past_version.name == 'Test University'
        
        future_version = institution.get_version_at(
            timezone.now() + timedelta(days=31)
        )
        assert future_version.name == 'Updated University'

    def test_active_courses_retrieval(self, institution_factory):
        """Test course retrieval with caching."""
        institution = institution_factory()
        
        # Test with filters
        filters = {'department': 'CS'}
        courses = institution.get_active_courses(filters=filters)
        
        # Verify cache
        cache_key = f"institution:{institution.pk}:courses:{hash(str(filters))}"
        assert cache.get(cache_key) == courses

    def test_transfer_requirements_retrieval(self, institution_factory):
        """Test transfer requirement retrieval with caching."""
        institution = institution_factory()
        
        # Test with major filter
        major_code = 'CS'
        requirements = institution.get_transfer_requirements(major_code=major_code)
        
        # Verify cache
        cache_key = f"institution:{institution.pk}:requirements:{major_code}"
        assert cache.get(cache_key) == requirements

@pytest.mark.django_db
class TestInstitutionAgreement:
    """
    Test suite for InstitutionAgreement model focusing on lifecycle
    and validation.
    """
    
    def test_agreement_lifecycle(self, agreement_factory):
        """Test complete agreement lifecycle including temporal validation."""
        now = timezone.now()
        
        # Create future agreement
        agreement = agreement_factory(
            effective_from=now + timedelta(days=30),
            effective_to=now + timedelta(days=395)
        )
        
        # Test pre-activation state
        assert not agreement.is_active(now)
        
        # Test active state
        future_date = now + timedelta(days=31)
        assert agreement.is_active(future_date)
        
        # Test expiration
        expired_date = now + timedelta(days=396)
        assert not agreement.is_active(expired_date)

    def test_agreement_validation(self, agreement_factory):
        """Test comprehensive agreement validation rules."""
        now = timezone.now()
        
        # Test invalid date range
        with pytest.raises(ValidationError) as exc:
            agreement_factory(
                effective_from=now,
                effective_to=now - timedelta(days=1)
            )
        assert 'effective_to' in str(exc.value)
        
        # Test same institution agreement
        with pytest.raises(ValidationError) as exc:
            inst = Institution.objects.create(
                name='Test Institution',
                code='TEST',
                type='university'
            )
            agreement_factory(
                source_institution=inst,
                target_institution=inst
            )
        assert 'institutions' in str(exc.value)
        
        # Test overlapping agreements
        agreement1 = agreement_factory()
        with pytest.raises(ValidationError) as exc:
            agreement_factory(
                source_institution=agreement1.source_institution,
                target_institution=agreement1.target_institution,
                effective_from=agreement1.effective_from
            )
        assert 'overlapping' in str(exc.value)