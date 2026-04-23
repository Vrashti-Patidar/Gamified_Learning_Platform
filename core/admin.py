from django.contrib import admin
from .models import UserProfile, Category, Course, Lesson, Enrollment, UserLessonProgress, Badge, UserBadge

admin.site.register(UserProfile)
admin.site.register(Category)
admin.site.register(Course)
admin.site.register(Lesson)
admin.site.register(Enrollment)
admin.site.register(UserLessonProgress)
admin.site.register(Badge)
admin.site.register(UserBadge)
