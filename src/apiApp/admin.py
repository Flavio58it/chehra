from django.contrib import admin
from .models import (
    Teacher,
    Student,
    Department,
    Course
)


# Register your models here.
class TeacherAdminModel(admin.ModelAdmin):
    # to display columns
    list_display = ["teacher_id", "user"]


class StudentAdminModel(admin.ModelAdmin):
    list_display = ["student_id", "user", "uid", "dept_id"]


class DepartmentAdminModel(admin.ModelAdmin):
    list_display = ["dept_id", "name"]


class CourseAdminModel(admin.ModelAdmin):
    list_display = ["course_id", "dept_id", "teacher_id",
                    "name", "description", "academic_yr", "year",
                    "updated", "created"]

    list_display_links = ["dept_id", "teacher_id"]


admin.site.register(Teacher, TeacherAdminModel)
admin.site.register(Student, StudentAdminModel)
admin.site.register(Department, DepartmentAdminModel)
admin.site.register(Course, CourseAdminModel)