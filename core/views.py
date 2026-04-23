from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import UserProfile

def home(request):
    return render(request, 'index.html')

def login_view(request):
    if request.method == 'POST':
        u = request.POST.get('username', '').strip()
        p = request.POST.get('password', '')
        
        user = authenticate(request, username=u, password=p)
        
        if user is None:
            # Fallback: search by case-insensitive email, username, or even first_name (since the signup form uses Full Name)
            user_obj = User.objects.filter(Q(email__iexact=u) | Q(username__iexact=u) | Q(first_name__iexact=u)).first()
            if user_obj and user_obj.check_password(p):
                user = authenticate(request, username=user_obj.username, password=p)
                # If still None (e.g. backend issue), we can manually set the backend and use the user_obj
                if user is None:
                    user_obj.backend = 'django.contrib.auth.backends.ModelBackend'
                    user = user_obj

        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}!")
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid username or password.")
    return redirect('home')

def signup_view(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        
        if User.objects.filter(Q(username__iexact=email) | Q(email__iexact=email)).exists():
            messages.error(request, "Account with this email already exists.")
            return redirect('home')
        
        user = User.objects.create_user(username=email.lower(), email=email.lower(), password=password, first_name=name)
        
        # Ensure profile exists just in case the signal is delayed or fails
        UserProfile.objects.get_or_create(user=user)
        
        login(request, user)
        messages.success(request, f"Account created! Welcome, {name}!")
        return redirect('dashboard')
    
    return redirect('home')

from .models import Lesson, UserLessonProgress

@login_required
def dashboard(request):
    profile = request.user.userprofile
    enrollments = request.user.enrollments.all()
    user_badges = request.user.badges.all()
    
    # Gather up to 4 uncompleted lessons across all enrolled courses to show in the calendar
    completed_lesson_ids = UserLessonProgress.objects.filter(
        user=request.user, is_completed=True
    ).values_list('lesson_id', flat=True)
    
    enrolled_courses = [e.course for e in enrollments]
    upcoming_lessons = Lesson.objects.filter(
        course__in=enrolled_courses
    ).exclude(id__in=completed_lesson_ids).order_by('course__id', 'order')[:4]
    
    context = {
        'profile': profile,
        'enrollments': enrollments,
        'user_badges': user_badges,
        'upcoming_lessons': upcoming_lessons,
    }
    return render(request, 'dashboard.html', context)

from .models import Course, Category, Enrollment

def course_list(request):
    category_name = request.GET.get('category')
    if category_name:
        courses = Course.objects.filter(category__name__iexact=category_name)
    else:
        courses = Course.objects.all()
    categories = Category.objects.all()
    return render(request, 'course_list.html', {'courses': courses, 'categories': categories, 'selected_category': category_name})

def course_detail(request, course_id):
    course = Course.objects.get(id=course_id)
    is_enrolled = False
    if request.user.is_authenticated:
        is_enrolled = Enrollment.objects.filter(user=request.user, course=course).exists()
    return render(request, 'course_detail.html', {'course': course, 'is_enrolled': is_enrolled})

@login_required
def enroll(request, course_id):
    course = Course.objects.get(id=course_id)
    Enrollment.objects.get_or_create(user=request.user, course=course)
    messages.success(request, f"Successfully enrolled in {course.title}!")
    return redirect('course_detail', course_id=course.id)

from .models import Lesson, UserLessonProgress, Badge, UserBadge
from django.shortcuts import get_object_or_404

@login_required
def lesson_detail(request, course_id, lesson_id):
    course = get_object_or_404(Course, id=course_id)
    lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
    
    is_enrolled = Enrollment.objects.filter(user=request.user, course=course).exists()
    is_completed = UserLessonProgress.objects.filter(user=request.user, lesson=lesson, is_completed=True).exists()
    
    return render(request, 'lesson_detail.html', {
        'course': course, 'lesson': lesson, 
        'is_enrolled': is_enrolled, 'is_completed': is_completed
    })

@login_required
def mark_lesson_complete(request, course_id, lesson_id):
    if request.method == 'POST':
        lesson = get_object_or_404(Lesson, id=lesson_id, course_id=course_id)
        
        if not Enrollment.objects.filter(user=request.user, course=lesson.course).exists():
            messages.error(request, "You must be enrolled to complete lessons.")
            return redirect('course_detail', course_id=course_id)
            
        progress, created = UserLessonProgress.objects.get_or_create(user=request.user, lesson=lesson)
        if not progress.is_completed:
            progress.is_completed = True
            progress.save()
            
            profile = request.user.userprofile
            profile.xp += 50
            if profile.xp >= (profile.level * 100):
                profile.level += 1
                messages.success(request, f"🎉 Level Up! You are now Level {profile.level}!")
            profile.save()
            
            # Simple badge logic
            if profile.xp == 50:
                first_badge, _ = Badge.objects.get_or_create(name="First Steps", defaults={'description': 'Completed your first lesson!', 'icon': 'bi-star-fill'})
                UserBadge.objects.get_or_create(user=request.user, badge=first_badge)
                messages.success(request, "🏅 Badge Earned: First Steps!")
            else:
                messages.success(request, "Lesson completed! +50 XP earned.")
                
    return redirect('lesson_detail', course_id=course_id, lesson_id=lesson_id)

def leaderboard(request):
    top_users = UserProfile.objects.order_by('-xp', '-level')[:50]
    return render(request, 'leaderboard.html', {'top_users': top_users})
