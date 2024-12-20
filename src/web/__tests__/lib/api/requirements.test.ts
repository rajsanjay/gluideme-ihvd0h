import { describe, expect, it, beforeEach, afterEach, jest } from '@jest/globals'; // ^29.0.0
import MockAdapter from 'axios-mock-adapter'; // ^1.21.0
import {
  getRequirements,
  getRequirementById,
  createRequirement,
  updateRequirement,
  deleteRequirement,
  validateCourses
} from '../../../lib/api/requirements';
import type { 
  TransferRequirement,
  RequirementValidationResult,
  RequirementRules,
  RequirementStatus,
} from '../../../types/requirements';
import type { PaginatedResponse } from '../../../types/api';
import apiClient from '../../../config/api';

// Mock requirement data
const mockRequirement: TransferRequirement = {
  id: 'test-id',
  sourceInstitutionId: 'source-id',
  targetInstitutionId: 'target-id',
  majorCode: 'CS',
  title: 'Test Requirement',
  description: 'Test description',
  type: 'major',
  rules: {
    courses: [],
    rules: [],
    totalCredits: 120,
    minimumGPA: 2.0
  },
  metadata: {},
  status: 'published',
  effectiveDate: '2023-01-01T00:00:00Z',
  expirationDate: null,
  version: {
    versionNumber: 1,
    changes: [],
    publishedBy: 'user-id',
    publishedAt: '2023-01-01T00:00:00Z',
    createdAt: '2023-01-01T00:00:00Z',
    updatedAt: '2023-01-01T00:00:00Z'
  },
  audit: {
    createdBy: 'user-id',
    lastModifiedBy: 'user-id',
    changeHistory: [],
    comments: []
  },
  workflow: {
    currentStage: 'published',
    approvers: [],
    approvalStatus: {},
    dueDate: null
  },
  createdAt: '2023-01-01T00:00:00Z',
  updatedAt: '2023-01-01T00:00:00Z'
};

// Setup mock axios instance
let mockAxios: MockAdapter;

beforeEach(() => {
  mockAxios = new MockAdapter(apiClient);
});

afterEach(() => {
  mockAxios.reset();
  jest.clearAllMocks();
});

describe('getRequirements', () => {
  const mockPaginatedResponse: PaginatedResponse<TransferRequirement> = {
    data: [mockRequirement],
    total: 1,
    page: 1,
    pageSize: 10,
    totalPages: 1
  };

  it('should fetch paginated requirements successfully', async () => {
    mockAxios.onGet('/api/v1/requirements/').reply(200, mockPaginatedResponse);

    const response = await getRequirements({});
    expect(response.data).toEqual(mockPaginatedResponse);
    expect(response.status).toBe(200);
  });

  it('should handle filter parameters correctly', async () => {
    const filters = {
      institutionId: 'test-inst',
      majorCode: 'CS',
      status: 'published' as RequirementStatus
    };

    mockAxios.onGet('/api/v1/requirements/', { params: { ...filters, page: 1, limit: 10 } })
      .reply(200, mockPaginatedResponse);

    const response = await getRequirements({ filters });
    expect(response.data).toEqual(mockPaginatedResponse);
  });

  it('should handle network errors with retry', async () => {
    mockAxios
      .onGet('/api/v1/requirements/')
      .replyOnce(503)
      .onGet('/api/v1/requirements/')
      .reply(200, mockPaginatedResponse);

    const response = await getRequirements({});
    expect(response.data).toEqual(mockPaginatedResponse);
  });
});

describe('getRequirementById', () => {
  it('should fetch a single requirement successfully', async () => {
    mockAxios.onGet(`/api/v1/requirements/${mockRequirement.id}/`).reply(200, mockRequirement);

    const response = await getRequirementById(mockRequirement.id);
    expect(response.data).toEqual(mockRequirement);
  });

  it('should handle 404 errors correctly', async () => {
    mockAxios.onGet('/api/v1/requirements/non-existent/').reply(404, {
      code: 'NOT_FOUND',
      message: 'Requirement not found',
      errors: []
    });

    await expect(getRequirementById('non-existent')).rejects.toMatchObject({
      code: 'NOT_FOUND'
    });
  });

  it('should include versions and metadata when requested', async () => {
    mockAxios.onGet(`/api/v1/requirements/${mockRequirement.id}/`, {
      params: { include_versions: true, include_metadata: true }
    }).reply(200, mockRequirement);

    const response = await getRequirementById(mockRequirement.id, {
      includeVersions: true,
      includeMetadata: true
    });
    expect(response.data).toEqual(mockRequirement);
  });
});

describe('createRequirement', () => {
  const newRequirement = { ...mockRequirement };
  delete (newRequirement as any).id;

  it('should create a requirement successfully', async () => {
    mockAxios.onPost('/api/v1/requirements/').reply(201, mockRequirement);

    const response = await createRequirement(newRequirement);
    expect(response.data).toEqual(mockRequirement);
    expect(response.status).toBe(201);
  });

  it('should handle validation errors', async () => {
    const invalidRequirement = { ...newRequirement, majorCode: '' };
    mockAxios.onPost('/api/v1/requirements/').reply(400, {
      code: 'BAD_REQUEST',
      message: 'Validation failed',
      errors: [{ field: 'majorCode', message: 'Major code is required', code: 'REQUIRED' }]
    });

    await expect(createRequirement(invalidRequirement)).rejects.toMatchObject({
      code: 'BAD_REQUEST',
      errors: expect.arrayContaining([
        expect.objectContaining({ field: 'majorCode' })
      ])
    });
  });
});

describe('updateRequirement', () => {
  const updates = {
    title: 'Updated Title',
    description: 'Updated description'
  };

  it('should update a requirement successfully', async () => {
    const updatedRequirement = { ...mockRequirement, ...updates };
    mockAxios.onPut(`/api/v1/requirements/${mockRequirement.id}/`).reply(200, updatedRequirement);

    const response = await updateRequirement(mockRequirement.id, updates);
    expect(response.data).toEqual(updatedRequirement);
  });

  it('should handle version conflicts', async () => {
    mockAxios.onPut(`/api/v1/requirements/${mockRequirement.id}/`).reply(409, {
      code: 'BAD_REQUEST',
      message: 'Version conflict',
      errors: [{ field: 'version', message: 'Requirement has been modified', code: 'VERSION_CONFLICT' }]
    });

    await expect(updateRequirement(mockRequirement.id, updates)).rejects.toMatchObject({
      code: 'BAD_REQUEST',
      message: 'Version conflict'
    });
  });
});

describe('deleteRequirement', () => {
  it('should delete a requirement successfully', async () => {
    mockAxios.onDelete(`/api/v1/requirements/${mockRequirement.id}/`).reply(204);

    const response = await deleteRequirement(mockRequirement.id);
    expect(response.status).toBe(204);
  });

  it('should handle non-existent requirement deletion', async () => {
    mockAxios.onDelete('/api/v1/requirements/non-existent/').reply(404, {
      code: 'NOT_FOUND',
      message: 'Requirement not found',
      errors: []
    });

    await expect(deleteRequirement('non-existent')).rejects.toMatchObject({
      code: 'NOT_FOUND'
    });
  });
});

describe('validateCourses', () => {
  const mockValidationResult: RequirementValidationResult = {
    isValid: true,
    errors: [],
    warnings: [],
    details: {},
    validationDate: '2023-01-01T00:00:00Z',
    validatedBy: 'system',
    metadata: {
      validationRules: ['course-match', 'gpa-check'],
      timestamp: '2023-01-01T00:00:00Z'
    }
  };

  it('should validate courses successfully', async () => {
    mockAxios.onPost(`/api/v1/requirements/${mockRequirement.id}/validate-courses/`)
      .reply(200, mockValidationResult);

    const response = await validateCourses(mockRequirement.id, ['CS101', 'CS102']);
    expect(response.data).toEqual(mockValidationResult);
  });

  it('should handle validation failures', async () => {
    const failedValidation = {
      ...mockValidationResult,
      isValid: false,
      errors: [{
        code: 'MISSING_PREREQUISITE',
        message: 'Missing prerequisite CS101',
        field: 'courses',
        severity: 'error'
      }]
    };

    mockAxios.onPost(`/api/v1/requirements/${mockRequirement.id}/validate-courses/`)
      .reply(200, failedValidation);

    const response = await validateCourses(mockRequirement.id, ['CS102']);
    expect(response.data.isValid).toBe(false);
    expect(response.data.errors).toHaveLength(1);
  });
});