from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout, get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib import messages
from .models import Profile, DailyMetrics, Recommendation
from .ml_service import get_personalization_service
from datetime import timedelta
from django.utils import timezone
from django.db.models import Avg

User = get_user_model()


def home(request):
    """Homepage view"""
    return render(request, 'reco/home.html')


@login_required
def dashboard(request):
    """Dashboard view with user's health metrics"""
    user = request.user
    
    # Get recent metrics (last 7 days) - query without slicing first
    metrics_qs = DailyMetrics.objects.filter(user=user).order_by('-date')
    
    # Get profile
    profile, _ = Profile.objects.get_or_create(user=user)
    
    # Calculate stats
    metrics_count = DailyMetrics.objects.filter(user=user).count()
    recommendations_count = Recommendation.objects.filter(user=user).count()
    
    # Get metrics for calculations (need queryset for aggregate)
    metrics_7d = metrics_qs[:7]
    
    # Calculate 7-day averages
    if metrics_7d:
        # Convert to list for calculations
        metrics_list_calc = list(metrics_7d)
        
        sleep_values = [m.sleep_hours for m in metrics_list_calc if m.sleep_hours]
        steps_values = [m.steps for m in metrics_list_calc if m.steps]
        
        avg_sleep = sum(sleep_values) / len(sleep_values) if sleep_values else None
        avg_steps = sum(steps_values) / len(steps_values) if steps_values else None
        
        # Get latest BP (field names: systolic_bp / diastolic_bp)
        latest_metric = metrics_list_calc[0] if metrics_list_calc else None
        if latest_metric and latest_metric.systolic_bp and latest_metric.diastolic_bp:
            latest_bp = f"{int(latest_metric.systolic_bp)}/{int(latest_metric.diastolic_bp)}"
        else:
            latest_bp = None
    else:
        metrics_list_calc = []
        avg_sleep = None
        avg_steps = None
        latest_bp = None
    
    # Prepare chart data (chronological order)
    metrics_list = sorted(metrics_list_calc, key=lambda x: x.date)
    chart_labels = [m.date.strftime('%d/%m') for m in metrics_list]
    sleep_data = [float(m.sleep_hours) if m.sleep_hours else 0 for m in metrics_list]
    steps_data = [int(m.steps) if m.steps else 0 for m in metrics_list]
    
    # Get recent recommendations
    recent_recommendations = Recommendation.objects.filter(user=user).order_by('-created_at')[:5]
    
    context = {
        'profile': profile,
        'metrics': metrics_list_calc,  # Use the list, not the queryset
        'metrics_count': metrics_count,
        'recommendations_count': recommendations_count,
        'avg_sleep': avg_sleep,
        'avg_steps': avg_steps,
        'latest_bp': latest_bp,
        'chart_labels': chart_labels,
        'sleep_data': sleep_data,
        'steps_data': steps_data,
        'recent_recommendations': recent_recommendations,
    }
    
    return render(request, 'reco/dashboard.html', context)


@login_required
def recommendations_view(request):
    """Recommendations view with ML-powered recommendations and feedback learning"""
    user = request.user
    
    # Get personalized recommendations
    recommendations = Recommendation.objects.filter(user=user).order_by('-score', '-created_at')
    
    # Get ML service
    ml_service = get_personalization_service()
    
    # Get feedback learning insights
    from .feedback_learning import get_feedback_insights, get_personalized_confidence
    feedback_insights = get_feedback_insights(user)
    
    # Add ML confidence and explanation to each recommendation
    recommendations_data = []
    total_confidence = 0
    
    for reco in recommendations:
        # Get base ML confidence (already in 0.0-1.0 range)
        _, base_confidence, explanation = ml_service.predict_helpfulness(user, reco.category)
        
        # Apply feedback learning (base_confidence already 0.0-1.0)
        personalized_confidence = get_personalized_confidence(
            user=user,
            category=reco.category,
            base_confidence=base_confidence
        ) * 100  # Convert to percentage for display
        
        recommendations_data.append({
            'id': reco.id,
            'category': reco.category,
            'text': reco.text,
            'ml_confidence': personalized_confidence,  # Use personalized confidence
            'base_confidence': base_confidence,  # Keep base for comparison
            'explanation': explanation,
            'source': reco.source,
            'model_version': reco.model_version,
            'created_at': reco.created_at,
            'helpful': reco.helpful,
            'viewed': reco.viewed,
            'acted_upon': reco.acted_upon,
        })
        
        total_confidence += personalized_confidence
    
    # Calculate average confidence (personalized)
    avg_confidence = total_confidence / len(recommendations_data) if recommendations_data else 0
    
    context = {
        'recommendations': recommendations_data,
        'model_version': ml_service.model_version or 'rule-only',
        'avg_confidence': avg_confidence,
        'feedback_insights': feedback_insights,  # Add feedback insights
        'total_count': len(recommendations_data),
    }
    
    return render(request, 'reco/recommendations.html', context)


@login_required
def profile_view(request):
    """User profile view"""
    profile, _ = Profile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Update user fields
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.email = request.POST.get('email', '')
        request.user.save()
        
        # Update profile fields
        # Note: age is computed from birth_date, so we calculate birth_date from age
        age_str = request.POST.get('age', '').strip()
        if age_str:
            try:
                from datetime import date
                age = int(age_str)
                current_year = date.today().year
                profile.birth_date = date(current_year - age, 1, 1)
            except (ValueError, TypeError):
                profile.birth_date = None
        
        profile.sex = request.POST.get('gender', '')
        profile.height_cm = float(request.POST.get('height')) if request.POST.get('height') else None
        profile.weight_kg = float(request.POST.get('weight')) if request.POST.get('weight') else None
        profile.activity_level = request.POST.get('activity_level', '')
        profile.health_goals = request.POST.get('health_goals', '')
        profile.medical_conditions = request.POST.get('medical_conditions', '')
        
        # Handle preferences - if it's a string, keep it as text
        prefs = request.POST.get('preferences', '')
        if prefs:
            profile.preferences = {'notes': prefs}  # Store as JSON dict
        
        profile.save()
        
        messages.success(request, 'Profil mis à jour avec succès !')
        return redirect('reco:profile')
    
    # Get stats for profile page
    metrics_count = DailyMetrics.objects.filter(user=request.user).count()
    recommendations_count = Recommendation.objects.filter(user=request.user).count()
    
    context = {
        'profile': profile,
        'metrics_count': metrics_count,
        'recommendations_count': recommendations_count,
    }
    
    return render(request, 'reco/profile.html', context)




def login_view(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('reco:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Bienvenue {user.username} !')
            # Redirect to 'next' parameter or dashboard
            next_url = request.GET.get('next', 'reco:dashboard')
            return redirect(next_url)
        else:
            messages.error(request, 'Nom d\'utilisateur ou mot de passe incorrect.')
    
    return render(request, 'reco/login.html')


def register(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('reco:dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password1 = request.POST.get('password1')
        password2 = request.POST.get('password2')
        
        # Validation
        errors = []
        if not username or not email or not password1 or not password2:
            errors.append('Tous les champs sont requis.')
        elif password1 != password2:
            errors.append('Les mots de passe ne correspondent pas.')
        elif len(password1) < 8:
            errors.append('Le mot de passe doit contenir au moins 8 caractères.')
        elif User.objects.filter(username=username).exists():
            errors.append('Ce nom d\'utilisateur existe déjà.')
        elif User.objects.filter(email=email).exists():
            errors.append('Cet email est déjà utilisé.')
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return render(request, 'reco/register.html', {
                'username': username,
                'email': email
            })
        
        # Create user
        try:
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password1
            )
            # Auto-login after registration
            login(request, user)
            messages.success(request, f'Bienvenue {user.username} ! Votre compte a été créé.')
            return redirect('reco:profile')
        except Exception as e:
            messages.error(request, f'Erreur lors de la création du compte: {str(e)}')
            return render(request, 'reco/register.html', {
                'username': username,
                'email': email
            })
    
    return render(request, 'reco/register.html')


def logout_view(request):
    """Custom logout view that handles both GET and POST requests"""
    logout(request)
    messages.success(request, 'Vous avez été déconnecté avec succès.')
    return redirect('home')


@login_required
def ai_progress_view(request):
    """View to show AI learning progress and confidence by category"""
    user = request.user
    
    # Get feedback learning insights
    from .feedback_learning import get_feedback_insights, get_personalized_confidence, calculate_category_confidence
    
    feedback_insights = get_feedback_insights(user)
    
    # Calculate confidence for each category
    categories = ['sleep', 'activity', 'nutrition', 'lifestyle']
    category_stats = []
    
    # Get ML service for real base confidence
    ml_service = get_personalization_service()
    
    total_personalized_confidence = 0
    
    for category in categories:
        # Get REAL base ML confidence from calibrated model
        _, base_ml_confidence, _ = ml_service.predict_helpfulness(user, category)
        # base_ml_confidence is already in 0.0-1.0 range (e.g., 0.70 for 70%)
        
        # Get personalized confidence with cumulative boost
        personalized = get_personalized_confidence(user, category, base_ml_confidence)
        
        # Calculate boost
        boost = (personalized - base_ml_confidence) * 100
        
        # Get feedback count for this category
        feedback_count = Recommendation.objects.filter(
            user=user,
            category=category,
            feedback_at__isnull=False
        ).count()
        
        # Get helpful rate for this category
        helpful_count = Recommendation.objects.filter(
            user=user,
            category=category,
            helpful=True
        ).count()
        helpful_rate = (helpful_count / feedback_count * 100) if feedback_count > 0 else 0
        
        category_stats.append({
            'category': category,
            'base_confidence': base_ml_confidence * 100,
            'confidence': personalized * 100,
            'boost': boost,
            'feedback_count': feedback_count,
            'helpful_rate': helpful_rate,
        })
        
        total_personalized_confidence += personalized
    
    # Calculate average confidence
    avg_confidence = (total_personalized_confidence / len(categories)) * 100 if categories else 0
    
    # Calculate boost potential (if user gives more positive feedback)
    max_possible = 90.0  # Maximum achievable confidence
    boost_potential = max_possible - avg_confidence
    
    context = {
        'category_stats': category_stats,
        'avg_confidence': avg_confidence,
        'total_feedback': feedback_insights['total_feedback'],
        'helpful_rate': feedback_insights['helpful_rate'],
        'boost_potential': max(0, boost_potential),
        'feedback_insights': feedback_insights,
    }
    
    return render(request, 'reco/ai_progress.html', context)


@login_required
def add_metrics(request):
    """User-friendly view to add daily health metrics"""
    if request.method == 'POST':
        try:
            date_str = request.POST.get('date')
            steps = request.POST.get('steps')
            sleep_hours = request.POST.get('sleep_hours')
            systolic_bp = request.POST.get('systolic_bp')
            diastolic_bp = request.POST.get('diastolic_bp')
            
            # Validate date
            from datetime import datetime
            metric_date = datetime.strptime(date_str, '%Y-%m-%d').date() if date_str else timezone.now().date()
            
            # Check if metrics already exist for this date
            existing_metric = DailyMetrics.objects.filter(user=request.user, date=metric_date).first()
            
            if existing_metric:
                # Update existing
                if steps:
                    existing_metric.steps = int(steps)
                if sleep_hours:
                    existing_metric.sleep_hours = float(sleep_hours)
                if systolic_bp:
                    existing_metric.systolic_bp = int(systolic_bp)
                if diastolic_bp:
                    existing_metric.diastolic_bp = int(diastolic_bp)
                existing_metric.save()
                messages.success(request, f'Métriques mises à jour pour le {metric_date.strftime("%d/%m/%Y")} !')
            else:
                # Create new
                DailyMetrics.objects.create(
                    user=request.user,
                    date=metric_date,
                    steps=int(steps) if steps else None,
                    sleep_hours=float(sleep_hours) if sleep_hours else None,
                    systolic_bp=int(systolic_bp) if systolic_bp else None,
                    diastolic_bp=int(diastolic_bp) if diastolic_bp else None,
                )
                messages.success(request, f'Métriques ajoutées pour le {metric_date.strftime("%d/%m/%Y")} !')
            
            # Redirect to dashboard
            return redirect('dashboard')
            
        except Exception as e:
            messages.error(request, f'Erreur lors de l\'enregistrement : {str(e)}')
    
    # Get today's date for default
    today = timezone.now().date()
    
    # Check if metrics already exist for today
    today_metrics = DailyMetrics.objects.filter(user=request.user, date=today).first()
    
    context = {
        'today': today,
        'today_metrics': today_metrics,
    }
    
    return render(request, 'reco/add_metrics.html', context)
