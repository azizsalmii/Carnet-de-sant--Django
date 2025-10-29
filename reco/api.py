"""
Django REST Framework API for HEALTH TRACK recommendations.
"""
from rest_framework import serializers, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated, AllowAny
from rest_framework.authentication import SessionAuthentication

from .models import DailyMetrics, Recommendation, Profile
from .services import compute_features_for_user, generate_recommendations_for_user


class ProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profiles."""
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Profile
        fields = ['id', 'username', 'sex', 'birth_date', 'height_cm', 'weight_kg']
        read_only_fields = ['id']


class DailyMetricsSerializer(serializers.ModelSerializer):
    """Serializer for daily health metrics."""
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = DailyMetrics
        fields = [
            'id', 'username', 'date', 'steps', 'sleep_hours',
            'systolic_bp', 'diastolic_bp'
        ]
        read_only_fields = ['id', 'username']


class RecommendationSerializer(serializers.ModelSerializer):
    """Serializer for recommendations."""
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Recommendation
        fields = [
            'id', 'username', 'created_at', 'category',
            'text', 'rationale', 'source', 'score',
            'viewed', 'viewed_at', 'helpful', 'feedback_at', 'acted_upon',
            'model_version', 'experiment_group'
        ]
        read_only_fields = ['id', 'username', 'created_at']


class ProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user profiles.
    Users can only access their own profile.
    """
    serializer_class = ProfileSerializer
    # Uses global permission: IsAuthenticatedOrReadOnly
    
    def get_queryset(self):
        # If authenticated, show only their profile
        if self.request.user.is_authenticated:
            return Profile.objects.filter(user=self.request.user)
        # If not authenticated (browsing), show empty queryset
        return Profile.objects.none()
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DailyMetricsViewSet(viewsets.ModelViewSet):
    """
    ViewSet for daily health metrics.
    Users can only access their own metrics.
    """
    serializer_class = DailyMetricsSerializer
    # Uses global permission: IsAuthenticatedOrReadOnly
    
    def get_queryset(self):
        # If authenticated, show only their metrics
        if self.request.user.is_authenticated:
            return DailyMetrics.objects.filter(user=self.request.user)
        # If not authenticated (browsing), show empty queryset
        return DailyMetrics.objects.none()
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['post'])
    def run_recommendations(self, request):
        """
        Custom action to generate recommendations based on user's metrics.
        
        POST /api/metrics/run_recommendations/
        
        Returns:
            {
                "generated": <number of recommendations created>,
                "features": {<computed features dict>}
            }
        """
        user = request.user
        
        # Compute features
        features = compute_features_for_user(user.id)
        
        # Generate recommendations
        generated_count = generate_recommendations_for_user(user.id, features)
        
        return Response({
            'generated': generated_count,
            'features': features,
        }, status=status.HTTP_201_CREATED)


class RecommendationViewSet(viewsets.ModelViewSet):
    queryset = Recommendation.objects.all()
    serializer_class = RecommendationSerializer
    authentication_classes = [SessionAuthentication]          # <- session Django
    permission_classes = [IsAuthenticatedOrReadOnly]          # lecture publique, écriture = login

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Recommendation.objects.filter(user=self.request.user)
        return Recommendation.objects.none()
    
    @action(detail=True, methods=['post'])
    def mark_viewed(self, request, pk=None):
        """
        Mark a recommendation as viewed.
        
        POST /api/recommendations/{id}/mark_viewed/
        """
        from django.utils import timezone
        
        recommendation = self.get_object()
        recommendation.viewed = True
        recommendation.viewed_at = timezone.now()
        recommendation.save(update_fields=['viewed', 'viewed_at'])
        
        return Response({
            'status': 'viewed',
            'viewed_at': recommendation.viewed_at,
        })
    
    # reco/api.py (remplace entièrement l’action provide_feedback)
    @action(detail=True, methods=['post'])
    def provide_feedback(self, request, pk=None):
        """
       
        """
        from django.utils import timezone
        import logging
        from .feedback_learning import get_personalized_confidence  # ✅

        logger = logging.getLogger(__name__)
        recommendation = self.get_object()

        helpful = request.data.get('helpful')
        acted_upon = request.data.get('acted_upon', False)

        if helpful is None:
            return Response(
                {'error': 'helpful field is required (true/false)'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 1) Sauver le feedback sur CETTE reco
        recommendation.helpful = bool(helpful)
        recommendation.acted_upon = bool(acted_upon)
        recommendation.feedback_at = timezone.now()
        recommendation.viewed = True
        recommendation.viewed_at = recommendation.viewed_at or timezone.now()
        recommendation.save(update_fields=['helpful','acted_upon','feedback_at','viewed','viewed_at'])

        # 2) Recalculer la confiance personnalisée pour cette catégorie/user
        #    et propager sur les autres reco (même user + category)
        user = request.user
        category = recommendation.category
        base_confidence = 0.43  # si tu as un score “ML brut”, mets-le ici
        new_conf = get_personalized_confidence(user, category, base_confidence=base_confidence)

        # On stocke dans .score (champ float 0-1) — les templates peuvent l’afficher * 100
        from .models import Recommendation as RecoModel
        RecoModel.objects.filter(user=user, category=category).update(score=new_conf)

        # 3) Message adapté
        if helpful and acted_upon:
            message = "🎉 Merci ! Votre retour améliore l’IA et a été pris en compte."
        elif helpful:
            message = "👍 Merci ! Cette recommandation semble utile."
        else:
            message = "📝 Merci pour votre retour. Nous allons améliorer nos recommandations."

        return Response({
            'status': 'feedback_recorded',
            'helpful': bool(helpful),
            'acted_upon': bool(acted_upon),
            'feedback_at': recommendation.feedback_at,
            'new_confidence': new_conf,           # 0.0–1.0
            'new_confidence_pct': round(new_conf*100, 1),  # %
            'category': category,
            'message': message,
        }, status=status.HTTP_200_OK)

    
    @action(detail=False, methods=['get'])
    def personalized(self, request):
        """
        Get personalized recommendations with ML explanations.
        
        GET /api/recommendations/personalized/
        
        Returns:
        - Recommendations ranked by ML confidence
        - Personalized explanations for each recommendation
        - ML confidence scores
        """
        from .ml_service import get_personalization_service
        
        # Get user's recommendations
        recommendations = self.get_queryset().all()[:10]  # Top 10
        
        if not recommendations:
            return Response({
                'message': 'No recommendations available. Add daily metrics first.',
                'count': 0,
                'recommendations': []
            })
        
        # Get ML service
        ml_service = get_personalization_service()
        
        # Add ML insights to each recommendation
        personalized_recos = []
        for reco in recommendations:
            _, confidence, explanation = ml_service.predict_helpfulness(
                request.user,
                reco.category
            )
            
            personalized_recos.append({
                'id': reco.id,
                'category': reco.category,
                'text': reco.text,
                'score': reco.score,
                'ml_confidence': confidence,
                'explanation': explanation,
                'source': reco.source,
                'model_version': reco.model_version,
                'created_at': reco.created_at,
                'viewed': reco.viewed,
                'helpful': reco.helpful,
            })
        
        return Response({
            'count': len(personalized_recos),
            'model_version': ml_service.model_version or 'rule-only',
            'recommendations': personalized_recos
        })
