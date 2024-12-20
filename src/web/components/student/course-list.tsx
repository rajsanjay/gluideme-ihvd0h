"use client";

import * as React from "react";
import { cn } from "class-variance-authority"; // v0.7.0
import { useVirtualizer } from "@tanstack/react-virtual"; // v3.0.0
import { DataTable } from "../common/data-table";
import type { PlannedCourse, CourseStatus } from "../../types/student";

// Style variants for status badges using class-variance-authority
const statusVariants = {
  planned: "bg-blue-100 text-blue-800 dark:bg-blue-800 dark:text-blue-100",
  in_progress: "bg-yellow-100 text-yellow-800 dark:bg-yellow-800 dark:text-yellow-100",
  completed: "bg-green-100 text-green-800 dark:bg-green-800 dark:text-green-100",
  failed: "bg-red-100 text-red-800 dark:bg-red-800 dark:text-red-100",
} as const;

// Props interface with comprehensive type definitions
interface CourseListProps {
  courses: PlannedCourse[];
  loading?: boolean;
  error?: string | null;
  onStatusChange: (courseId: string, status: CourseStatus) => Promise<void>;
  onGradeUpdate: (courseId: string, grade: string) => Promise<void>;
  className?: string;
  virtualizeRows?: boolean;
  accessibilityAnnouncements?: boolean;
  showProgress?: boolean;
}

// Progress metrics interface
interface ProgressMetrics {
  completedUnits: number;
  totalUnits: number;
  completionPercentage: number;
  gpa: number | null;
}

/**
 * CourseList Component
 * 
 * A comprehensive course list component that displays and manages student course information
 * with enhanced accessibility features and performance optimizations.
 */
const CourseList: React.FC<CourseListProps> = React.memo(({
  courses,
  loading = false,
  error = null,
  onStatusChange,
  onGradeUpdate,
  className,
  virtualizeRows = true,
  accessibilityAnnouncements = true,
  showProgress = true,
}) => {
  // Refs for virtualization and announcements
  const tableRef = React.useRef<HTMLDivElement>(null);
  const announcerRef = React.useRef<HTMLDivElement>(null);

  // Calculate progress metrics
  const progressMetrics = React.useMemo((): ProgressMetrics => {
    const completed = courses.filter(c => c.status === "completed");
    const totalUnits = courses.reduce((sum, course) => sum + course.units, 0);
    const completedUnits = completed.reduce((sum, course) => sum + course.units, 0);
    
    // Calculate GPA for completed courses
    const validGrades = completed.filter(c => c.grade !== null);
    const gpa = validGrades.length > 0
      ? validGrades.reduce((sum, course) => {
          const gradePoints = {
            'A': 4.0, 'A-': 3.7,
            'B+': 3.3, 'B': 3.0, 'B-': 2.7,
            'C+': 2.3, 'C': 2.0, 'C-': 1.7,
            'D+': 1.3, 'D': 1.0, 'F': 0.0
          }[course.grade || 'F'] || 0;
          return sum + (gradePoints * course.units);
        }, 0) / validGrades.reduce((sum, course) => sum + course.units, 0)
      : null;

    return {
      completedUnits,
      totalUnits,
      completionPercentage: (completedUnits / totalUnits) * 100,
      gpa
    };
  }, [courses]);

  // Status badge renderer with accessibility enhancements
  const getStatusBadge = React.useCallback((status: CourseStatus) => {
    const statusText = {
      planned: "Planned",
      in_progress: "In Progress",
      completed: "Completed",
      failed: "Failed"
    }[status];

    return (
      <span
        role="status"
        className={cn(
          "px-2 py-1 rounded-full text-sm font-medium",
          statusVariants[status]
        )}
        aria-label={`Course status: ${statusText}`}
      >
        {statusText}
      </span>
    );
  }, []);

  // Column definitions with accessibility and sorting support
  const columns = React.useMemo(() => [
    {
      accessorKey: "courseId",
      header: "Course",
      cell: (info: any) => (
        <span className="font-medium">{info.getValue()}</span>
      ),
    },
    {
      accessorKey: "status",
      header: "Status",
      cell: (info: any) => getStatusBadge(info.getValue()),
    },
    {
      accessorKey: "term",
      header: "Term",
    },
    {
      accessorKey: "grade",
      header: "Grade",
      cell: (info: any) => {
        const course = info.row.original;
        return course.status === "completed" ? (
          <select
            value={course.grade || ""}
            onChange={(e) => onGradeUpdate(course.courseId, e.target.value)}
            className="w-20 rounded-md border-gray-300 shadow-sm focus:border-primary-500 focus:ring-primary-500"
            aria-label={`Grade for course ${course.courseId}`}
          >
            <option value="">Select</option>
            {["A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "F"].map((grade) => (
              <option key={grade} value={grade}>{grade}</option>
            ))}
          </select>
        ) : null;
      },
    },
    {
      accessorKey: "units",
      header: "Units",
    },
  ], [getStatusBadge, onGradeUpdate]);

  // Accessibility announcer for status changes
  const announce = React.useCallback((message: string) => {
    if (accessibilityAnnouncements && announcerRef.current) {
      announcerRef.current.textContent = message;
    }
  }, [accessibilityAnnouncements]);

  // Status change handler with optimistic updates
  const handleStatusChange = React.useCallback(async (courseId: string, newStatus: CourseStatus) => {
    try {
      announce(`Updating status for course ${courseId} to ${newStatus}`);
      await onStatusChange(courseId, newStatus);
      announce(`Successfully updated course ${courseId} status to ${newStatus}`);
    } catch (error) {
      announce(`Failed to update status for course ${courseId}`);
      console.error("Status update failed:", error);
    }
  }, [onStatusChange, announce]);

  return (
    <div className={cn("space-y-4", className)}>
      {/* Progress Summary */}
      {showProgress && (
        <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
          <h2 className="text-lg font-semibold mb-2">Progress Summary</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <p className="text-sm text-gray-600">Completed Units</p>
              <p className="text-2xl font-bold">
                {progressMetrics.completedUnits} / {progressMetrics.totalUnits}
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Completion</p>
              <p className="text-2xl font-bold">
                {progressMetrics.completionPercentage.toFixed(1)}%
              </p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Current GPA</p>
              <p className="text-2xl font-bold">
                {progressMetrics.gpa?.toFixed(2) || 'N/A'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Course Table */}
      <DataTable
        data={courses}
        columns={columns}
        loading={loading}
        error={error}
        virtualScrolling={virtualizeRows}
        className="rounded-lg shadow-sm"
        customRenderers={{
          status: (value: CourseStatus) => getStatusBadge(value),
        }}
      />

      {/* Accessibility Announcer */}
      <div
        ref={announcerRef}
        role="status"
        aria-live="polite"
        className="sr-only"
      />
    </div>
  );
});

// Set display name for dev tools
CourseList.displayName = "CourseList";

export default CourseList;