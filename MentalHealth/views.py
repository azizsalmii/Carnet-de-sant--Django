import os
import re
import os
import logging
import random
from datetime import datetime, timedelta
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
import uuid
from django.http import JsonResponse
from django.conf import settings
from django.core.cache import cache
from textblob import TextBlob
import joblib
from transformers import pipeline
from sklearn.exceptions import NotFittedError


# ===============================
# 🎯 CONFIGURATION & LOGGING
# ===============================
logger = logging.getLogger(__name__)

# Enable Hugging Face pipelines only when explicitly allowed (heavy to load on low-memory hosts)
ENABLE_HF_MODELS = os.getenv("ENABLE_HF_MODELS", "1").lower() in {"1", "true", "yes", "on"}

# Configuration des modèles
MODEL_CONFIG = {
    'emotion_model': "mrm8488/t5-base-finetuned-emotion",
    'generator_model': "google/flan-t5-base",
    'max_length': 512,
    'temperature': 0.7
}

# ===============================
# 🧠 MODELS MANAGER OPTIMISÉ
# ===============================
class ModelManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.models = {}
        self.fallback_mode = False
        self.load_all_models()
        self._initialized = True
    
    def load_all_models(self):
        """Charge tous les modèles de manière optimisée"""
        try:
            # 1. Modèles ML traditionnels
            self.load_ml_models()
            
            # 2. Modèles Hugging Face (optionnels)
            if ENABLE_HF_MODELS:
                self.load_huggingface_models()
            else:
                logger.info("Skipping Hugging Face model loading because ENABLE_HF_MODELS is disabled")
                self.models['emotion_pipeline'] = None
                self.models['generator'] = None
            
            logger.info("✅ Tous les modèles chargés avec succès")
            
        except Exception as e:
            logger.error(f"❌ Erreur lors du chargement des modèles: {e}")
            self.setup_fallback_mode()
    
    def load_ml_models(self):
        """Charge les modèles ML locaux"""
        try:
            BASE_DIR = settings.BASE_DIR
            models_dir = os.path.join(BASE_DIR, 'MentalHealth', 'ml_models')
            
            self.models['classifier'] = joblib.load(os.path.join(models_dir, 'mental_health_model.pkl'))
            self.models['vectorizer'] = joblib.load(os.path.join(models_dir, 'vectorizer.pkl'))
            self.models['label_encoder'] = joblib.load(os.path.join(models_dir, 'label_encoder.pkl'))
            
        except Exception as e:
            logger.error(f"❌ Erreur chargement modèles ML: {e}")
            raise
    
    def load_huggingface_models(self):
        """Charge les modèles HF avec optimisations"""
        try:
            # Emotion detection
            self.models['emotion_pipeline'] = pipeline(
                "text2text-generation",
                model=MODEL_CONFIG['emotion_model'],
                do_sample=True,
                temperature=0.5,
                max_length=50
            )
        except Exception as e:
            logger.warning(f"⚠️ Emotion model fallback: {e}")
            self.models['emotion_pipeline'] = None
        
        try:
            # Generative model optimisé
            self.models['generator'] = pipeline(
                "text2text-generation",
                model=MODEL_CONFIG['generator_model'],
                do_sample=True,
                temperature=MODEL_CONFIG['temperature'],
                top_p=0.9,
                max_length=MODEL_CONFIG['max_length']
            )
        except Exception as e:
            logger.warning(f"⚠️ Generator model fallback: {e}")
            self.models['generator'] = None
    
    def setup_fallback_mode(self):
        """Mode fallback basique"""
        self.fallback_mode = True
        logger.info("🔄 Mode fallback activé")

# Initialisation du manager de modèles
model_manager = ModelManager()

# ===============================
# 🤖 CHATBOT THÉRAPEUTIQUE INTELLIGENT
# ===============================
class TherapeuticChatbot:
    def __init__(self):
        self.conversation_history = []
        self.user_context = {
            'current_emotion': 'neutral',
            'main_concerns': [],
            'coping_strategies_mentioned': [],
            'session_start': datetime.now()
        }
        self.techniques = {
            'cbt': {
                'name': 'Cognitive Behavioral Therapy',
                'questions': [
                    "What evidence supports this thought?",
                    "What's a more balanced way to view this situation?",
                    "How would you advise a friend in this situation?",
                    "What's the worst that could happen, and how would you cope?",
                    "What small step could you take right now?"
                ],
                'responses': {
                    'stress': [
                        "I notice you're feeling stressed about {topic}. Let's examine what's within your control.",
                        "Stress often comes from feeling overwhelmed. What's one small thing you could tackle first?",
                        "Your body might be signaling it needs a break. What self-care could you practice today?"
                    ],
                    'anxiety': [
                        "Anxiety often magnifies our worries. What's the actual probability of your fear happening?",
                        "Let's ground ourselves in the present. What's happening right now, in this moment?",
                        "Your anxiety is trying to protect you. How can we thank it while also creating space?"
                    ],
                    'sadness': [
                        "It takes courage to sit with sadness. What does this feeling need from you right now?",
                        "Sadness often points to what we value. What's important to you in this situation?",
                        "Let's be gentle with this sadness. What small comfort can we offer it?"
                    ],
                    'anger': [
                        "Anger often protects deeper hurts. What might be underneath this frustration?",
                        "Your anger is valid. How can we express it in a way that honors your needs?",
                        "What boundary might need strengthening here?"
                    ]
                }
            },
            'mindfulness': {
                'name': 'Mindfulness & Grounding',
                'exercises': [
                    "Let's do a 5-4-3-2-1 grounding exercise. Notice 5 things you can see, 4 things you can touch, 3 things you can hear, 2 things you can smell, and 1 thing you can taste.",
                    "Take three deep breaths with me. Inhale for 4 counts, hold for 4, exhale for 6.",
                    "Notice your body sensations without judgment. What do you feel right now?",
                    "Imagine placing your thoughts on clouds and watching them drift by."
                ],
                'responses': {
                    'stress': [
                        "Let's anchor in the present. Notice your breath - no need to change it, just observe.",
                        "Where do you feel the stress in your body? Let's send some gentle awareness there.",
                        "Imagine placing each worry in a bubble and watching it float away."
                    ],
                    'anxiety': [
                        "Let's return to our senses. What's one thing you can see right now?",
                        "Notice the space around you. You're safe in this moment.",
                        "Let the thoughts come and go like passing cars - no need to chase them."
                    ],
                    'sadness': [
                        "Let's create space for this sadness without getting lost in it.",
                        "Notice where you feel supported right now - your chair, the floor, your own presence.",
                        "Imagine your breath as a gentle wave, washing through the sadness."
                    ]
                }
            },
            'solution_focused': {
                'name': 'Solution-Focused Therapy',
                'questions': [
                    "What would be different if this problem was solved?",
                    "What's already working well in this situation?",
                    "On a scale of 1-10, where are you now and what would one step higher look like?",
                    "What strengths have helped you cope so far?"
                ],
                'responses': {
                    'stress': [
                        "When you've managed stress well before, what was different?",
                        "What small sign would tell you things are moving in the right direction?",
                        "Imagine it's one month from now and things are better - what changed?"
                    ],
                    'anxiety': [
                        "What moments of calm have you experienced recently, however brief?",
                        "If your anxiety were 10% less intense, what would be different?",
                        "What personal qualities help you face uncertainty?"
                    ],
                    'sadness': [
                        "What still brings you moments of comfort, even small ones?",
                        "If hope were to whisper to you, what might it say?",
                        "What has helped you through difficult times before?"
                    ]
                }
            },
            'validation': {
                'name': 'Emotional Validation',
                'responses': {
                    'stress': [
                        "It makes complete sense you'd feel stressed given what you're facing.",
                        "Your stress is a natural response to real challenges.",
                        "I hear how overwhelming this feels right now."
                    ],
                    'anxiety': [
                        "Your anxiety is trying to protect you - it comes from a place of care.",
                        "It's understandable to feel anxious when facing uncertainty.",
                        "Your nervous system is doing its job, even if it feels uncomfortable."
                    ],
                    'sadness': [
                        "Your sadness honors what matters to you.",
                        "It takes strength to sit with these feelings.",
                        "This sadness makes sense given what you're experiencing."
                    ],
                    'anger': [
                        "Your anger points to important values and boundaries.",
                        "This frustration makes sense - you deserve to be heard.",
                        "Your anger is telling you something needs attention."
                    ],
                    'joy': [
                        "It's beautiful to witness your joy!",
                        "Your positive energy is contagious!",
                        "This happiness honors the good in your life."
                    ]
                }
            }
        }
    
    def extract_key_topics(self, user_message):
        """Extrait les sujets principaux du message utilisateur"""
        topics = []
        message_lower = user_message.lower()
        
        topic_keywords = {
            'work': ['work', 'job', 'career', 'boss', 'colleague', 'deadline', 'meeting'],
            'relationships': ['friend', 'partner', 'family', 'relationship', 'boyfriend', 'girlfriend', 'spouse'],
            'health': ['health', 'sick', 'pain', 'doctor', 'hospital', 'medical'],
            'finance': ['money', 'financial', 'bill', 'debt', 'expensive', 'cost'],
            'future': ['future', 'tomorrow', 'next week', 'next month', 'plan'],
            'past': ['yesterday', 'last week', 'before', 'used to', 'remember'],
            'sleep': ['sleep', 'tired', 'exhausted', 'insomnia', 'rest'],
            'social': ['alone', 'lonely', 'isolated', 'people', 'crowd', 'party']
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in message_lower for keyword in keywords):
                topics.append(topic)
        
        return topics
    
    def generate_response(self, user_message, user_emotion, conversation_context):
        """Génère une réponse thérapeutique personnalisée et contextuelle"""
        
        # Mettre à jour le contexte utilisateur
        self.user_context['current_emotion'] = user_emotion
        topics = self.extract_key_topics(user_message)
        
        # Analyser le sentiment et l'urgence
        sentiment = TextBlob(user_message).sentiment.polarity
        urgency_keywords = [
            'help', 'emergency', 'urgent', 'crisis', 'cant take', 'overwhelming',
            # Include panic/breathing keywords as urgent
            'panic', 'panic attack', "can't breathe", 'cant breathe', 'hyperventilating'
        ]
        urgent = any(keyword in user_message.lower() for keyword in urgency_keywords)
        
        # Sélectionner la technique appropriée
        technique = self._select_technique(user_emotion, sentiment, urgent, len(self.conversation_history))

        # If the input signals a panic or breathing emergency, return an immediate safety-focused response
        # rather than continuing with normal flows. This provides faster, clearer guidance in crises.
        if urgent:
            # Provide an immediate grounding/breathing instruction plus safety guidance
            safety_msg = (
                "I can hear how intense this is and I'm really sorry you're feeling so overwhelmed. "
                "If you are in immediate danger, please call your local emergency number now. "
                "For immediate relief from panic, try this grounding/breathing: sit down, place one hand on your belly and take 4 slow breaths in through your nose for 4 counts, hold for 4, then exhale slowly for 6 counts. Repeat until you feel calmer. "
                "Would you like to try this together or should I suggest other coping steps?"
            )
            # Update conversation history and return
            self.conversation_history.append({
                'timestamp': datetime.now(),
                'user': user_message,
                'bot': safety_msg,
                'technique': 'urgent_support',
                'emotion': user_emotion,
                'topics': topics
            })
            self.conversation_history = self.conversation_history[-50:]
            return safety_msg
        
        # Générer une réponse personnalisée
        if technique == 'cbt':
            response = self._generate_cbt_response(user_message, user_emotion, topics)
        elif technique == 'mindfulness':
            response = self._generate_mindfulness_response(user_emotion, urgent, topics)
        elif technique == 'solution_focused':
            response = self._generate_solution_focused_response(user_message, user_emotion, topics)
        elif technique == 'validation':
            response = self._generate_validation_response(user_emotion, topics)
        else:
            response = self._generate_empathic_response(user_message, user_emotion, topics)
        
        # Mettre à jour l'historique
        self.conversation_history.append({
            'timestamp': datetime.now(),
            'user': user_message,
            'bot': response,
            'technique': technique,
            'emotion': user_emotion,
            'topics': topics
        })
        
        # Limiter l'historique
        self.conversation_history = self.conversation_history[-50:]
        
        return response
    
    def _select_technique(self, emotion, sentiment, urgent, conversation_length):
        """Sélectionne la technique thérapeutique appropriée"""
        if urgent:
            return 'mindfulness'
        
        # Adapter la technique selon la longueur de la conversation
        if conversation_length < 2:
            return 'validation'  # Commencer par valider
        
        technique_weights = {
            'anxiety': {'cbt': 0.3, 'mindfulness': 0.4, 'solution_focused': 0.2, 'validation': 0.1},
            'stress': {'cbt': 0.25, 'mindfulness': 0.35, 'solution_focused': 0.3, 'validation': 0.1},
            'sadness': {'cbt': 0.3, 'mindfulness': 0.2, 'solution_focused': 0.3, 'validation': 0.2},
            'anger': {'cbt': 0.35, 'mindfulness': 0.25, 'solution_focused': 0.25, 'validation': 0.15},
            'fear': {'cbt': 0.25, 'mindfulness': 0.4, 'solution_focused': 0.2, 'validation': 0.15},
            'joy': {'cbt': 0.1, 'mindfulness': 0.3, 'solution_focused': 0.4, 'validation': 0.2}
        }
        
        weights = technique_weights.get(emotion, {'cbt': 0.25, 'mindfulness': 0.3, 'solution_focused': 0.3, 'validation': 0.15})
        return random.choices(list(weights.keys()), weights=list(weights.values()))[0]
    
    def _generate_cbt_response(self, user_message, emotion, topics):
        """Génère une réponse CBT personnalisée"""
        if emotion in self.techniques['cbt']['responses']:
            response_template = random.choice(self.techniques['cbt']['responses'][emotion])
            
            # Personnaliser avec les topics
            if topics and 'work' in topics:
                response = response_template.format(topic="work pressures")
            elif topics and 'relationships' in topics:
                response = response_template.format(topic="relationship dynamics")
            elif topics and 'health' in topics:
                response = response_template.format(topic="health concerns")
            else:
                response = response_template.format(topic="this situation")
            
            # Ajouter une question CBT pertinente
            cbt_question = random.choice(self.techniques['cbt']['questions'])
            response += f" {cbt_question}"
            
        else:
            cbt_question = random.choice(self.techniques['cbt']['questions'])
            response = f"I want to understand your perspective better. {cbt_question}"
        
        return response
    
    def _generate_mindfulness_response(self, emotion, urgent, topics):
        """Génère une réponse de pleine conscience personnalisée"""
        if urgent:
            exercise = self.techniques['mindfulness']['exercises'][0]  # Grounding exercise
            return f"I can sense this feels intense right now. {exercise}"
        
        if emotion in self.techniques['mindfulness']['responses']:
            response = random.choice(self.techniques['mindfulness']['responses'][emotion])
            
            # Ajouter un exercice adapté
            if emotion == 'anxiety':
                exercise = self.techniques['mindfulness']['exercises'][1]  # Breathing
            elif emotion == 'stress':
                exercise = self.techniques['mindfulness']['exercises'][2]  # Body scan
            else:
                exercise = random.choice(self.techniques['mindfulness']['exercises'])
            
            response += f" {exercise}"
        else:
            response = random.choice(self.techniques['mindfulness']['exercises'])
        
        return response
    
    def _generate_solution_focused_response(self, user_message, emotion, topics):
        """Génère une réponse orientée solutions personnalisée"""
        if emotion in self.techniques['solution_focused']['responses']:
            response = random.choice(self.techniques['solution_focused']['responses'][emotion])
            
            # Adapter selon les topics
            if topics and 'work' in topics:
                response += " How could you bring even a small part of that solution to your work?"
            elif topics and 'relationships' in topics:
                response += " What would better connection look like in your relationships?"
            
        else:
            question = random.choice(self.techniques['solution_focused']['questions'])
            response = f"Let's focus on possibilities. {question}"
        
        return response
    
    def _generate_validation_response(self, emotion, topics):
        """Génère une réponse de validation émotionnelle"""
        if emotion in self.techniques['validation']['responses']:
            response = random.choice(self.techniques['validation']['responses'][emotion])
            
            # Personnaliser selon les topics
            if topics:
                primary_topic = topics[0]
                if primary_topic == 'work':
                    response += " Work challenges can really weigh on us."
                elif primary_topic == 'relationships':
                    response += " Relationships touch the deepest parts of who we are."
                elif primary_topic == 'health':
                    response += " Health concerns understandably bring up many emotions."
            
            # Transition vers une question d'exploration
            follow_ups = [
                "What's this experience been like for you?",
                "How has this been affecting your daily life?",
                "What would help you feel heard right now?"
            ]
            response += f" {random.choice(follow_ups)}"
            
        else:
            response = "Thank you for sharing that with me. Your experience matters. What would you like me to understand about what you're going through?"
        
        return response
    def _generate_empathic_response(self, user_message, emotion, topics):
        """Génère une réponse empathique avancée et personnalisée"""

        # Analyser le contenu spécifique du message
        message_lower = user_message.lower()

        # Détection de patterns spécifiques
        if "nothing seems to bring me joy" in message_lower or "anhedonia" in message_lower:
            responses = [
                "I hear how deeply this lack of joy is affecting you. When pleasure fades, it can feel like losing color from the world. This is often a sign that your emotional system needs extra care right now.",
                "The loss of joy you're describing sounds profoundly difficult. Our capacity for pleasure can sometimes go dormant when we're carrying heavy emotions. What small moments, however brief, have felt slightly less heavy recently?",
                "When joy disappears, it often leaves an important emptiness asking to be heard. What might this absence of pleasure be trying to tell us about what you need?"
            ]

        elif "struggling to get out of bed" in message_lower or "can't get up" in message_lower:
            responses = [
                "The difficulty getting out of bed tells me this emotional weight feels physical too. Your body might be asking for rest while also carrying the sadness. What would make getting up feel 10% easier tomorrow?",
                "When the bed becomes both refuge and prison, it shows how overwhelming things have become. The morning struggle is real - what tiny step could make that first movement feel more possible?",
                "I hear how much energy it's taking just to face the day. That morning heaviness is your system's honest response to carrying a lot. What kind of support would help lift some of that weight?"
            ]

        elif "down lately" in message_lower or "feeling low" in message_lower:
            responses = [
                "This period of feeling down seems to be sitting heavily with you. Low moods often have important things to teach us about our needs and boundaries. What's been the most challenging part of this low period?",
                "I sense the weight of this down period. These emotional valleys, while difficult, often prepare us for important growth. What has this low mood made you more aware of in your life?",
                "The 'down' feeling you describe sounds like it's been persistent. Sometimes our emotions need to go underground to process what's happening. What would feeling even slightly lifted look like for you?"
            ]

        else:
            # Réponses empathiques générales par émotion
            empathic_responses = {
                'sadness': [
                    "I hear the depth of what you're carrying. Sadness has its own wisdom about what matters deeply to us.",
                    "Your sadness makes space for important truths to emerge. What is it asking you to pay attention to?",
                    "I'm sitting with you in this heavy feeling. What needs the most compassion right now?"
                ],
                'anxiety': [
                    "I sense the whirlwind of concerns. Anxiety often arrives when we care deeply about something.",
                    "Your nervous system is working hard to protect you. Let's find some stillness within the storm.",
                    "The uncertainty feels overwhelming. What would help you feel more anchored in this moment?"
                ]
            }
            responses = empathic_responses.get(emotion, [
                "Thank you for trusting me with this. What feels most important for me to understand about your experience?",
                "I'm listening carefully to what this is like for you. What aspect feels most pressing right now?",
                "Your perspective matters deeply. What would be most helpful to explore together?"
            ])

        response = random.choice(responses)

        # Ajouter une question de suivi contextuelle
        follow_up = self._get_contextual_follow_up(user_message, emotion, topics)
        response += f" {follow_up}"

        return response

    def _get_contextual_follow_up(self, user_message, emotion, topics):
        """Retourne une question de suivi contextuelle"""
        message_lower = user_message.lower()

        # Suivis spécifiques selon le contenu
        if "nothing seems to bring me joy" in message_lower:
            follow_ups = [
                "When you think back to times when things felt lighter, what was different then?",
                "What small activity, even if it doesn't bring joy, feels the least heavy to consider?",
                "If your joy could whisper one thing it needs to return, what might that be?"
            ]

        elif "struggling to get out of bed" in message_lower:
            follow_ups = [
                "What's the first thought that comes to mind when you wake up in the morning?",
                "If you could design a morning routine that felt 10% easier, what would it include?",
                "What small comfort helps make the beginning of the day feel more manageable?"
            ]

        elif "down lately" in message_lower:
            follow_ups = [
                "What has this down period taught you about what you need to feel supported?",
                "When you've come through low periods before, what helped you start moving upward?",
                "What would your best friend say you need most right now?"
            ]

        else:
            # Suivis généraux par émotion
            emotion_follow_ups = {
                'sadness': [
                    "What does this sadness need from you or others right now?",
                    "How has this experience changed what's important to you?",
                    "What would feeling supported look like in this sadness?"
                ],
                'anxiety': [
                    "What would help you feel 10% safer in this situation?",
                    "When you've faced uncertainty before, what inner strength helped you through?",
                    "What's one small anchor you can hold onto right now?"
                ],
                'stress': [
                    "What's within your control in this situation, however small?",
                    "What would your future self thank you for doing today?",
                    "Where can you find moments of pause amidst the pressure?"
                ]
            }
            follow_ups = emotion_follow_ups.get(emotion, [
                "What feels most important to explore right now?",
                "What would be most helpful for us to focus on together?",
                "What aspect of this situation needs the most attention?"
            ])

        return random.choice(follow_ups)

    def get_conversation_summary(self):
        """Génère un résumé intelligent de la conversation"""
        if not self.conversation_history:
            return "No conversation yet."

        emotions = [msg['emotion'] for msg in self.conversation_history if msg.get('emotion')]
        techniques = [msg['technique'] for msg in self.conversation_history if msg.get('technique')]
        all_topics = []
        for msg in self.conversation_history:
            if msg.get('topics'):
                all_topics.extend(msg['topics'])

        if emotions:
            dominant_emotion = max(set(emotions), key=emotions.count)
        else:
            dominant_emotion = "mixed"

        summary = {
            'total_messages': len(self.conversation_history),
            'dominant_emotion': dominant_emotion,
            'main_topics': list(set(all_topics))[:3],
            'techniques_used': list(set(techniques)),
            'session_duration': datetime.now() - self.user_context['session_start'],
            'current_focus': self.user_context.get('main_concerns', [])[:2]
        }

        return summary

# ===============================
# 🎯 TABLEAU DE BORD PERSONNEL
# ===============================
class PersonalDashboard:
    def __init__(self, history_entries):
        self.history = history_entries
    
    def get_weekly_trends(self):
        """Analyse les tendances hebdomadaires"""
        if not self.history:
            return {}
        
        # Grouper par semaine
        weekly_data = {}
        for entry in self.history:
            week = entry['created_at'].isocalendar()[1]  # Numéro de semaine
            if week not in weekly_data:
                weekly_data[week] = []
            weekly_data[week].append(entry['mood_score'])
        
        # Calculer les moyennes hebdomadaires
        weekly_trends = {}
        for week, scores in weekly_data.items():
            weekly_trends[week] = {
                'average_score': sum(scores) / len(scores),
                'min_score': min(scores),
                'max_score': max(scores),
                'entries_count': len(scores)
            }
        
        return weekly_trends
    
    def get_emotion_patterns(self):
        """Identifie les patterns émotionnels récurrents"""
        if not self.history:
            return {}
        
        emotion_count = {}
        hour_patterns = {}
        day_patterns = {}
        
        for entry in self.history:
            # Comptage des émotions
            emotion = entry.get('emotion', 'neutral')
            emotion_count[emotion] = emotion_count.get(emotion, 0) + 1
            
            # Patterns par heure
            hour = entry['created_at'].hour
            if hour not in hour_patterns:
                hour_patterns[hour] = []
            hour_patterns[hour].append(entry['mood_score'])
            
            # Patterns par jour
            day = entry['created_at'].strftime('%A')
            if day not in day_patterns:
                day_patterns[day] = []
            day_patterns[day].append(entry['mood_score'])
        
        # Analyser les patterns
        patterns = {
            'dominant_emotion': max(emotion_count, key=emotion_count.get) if emotion_count else 'neutral',
            'best_time_of_day': max(hour_patterns, key=lambda h: sum(hour_patterns[h])/len(hour_patterns[h])) if hour_patterns else None,
            'best_day_of_week': max(day_patterns, key=lambda d: sum(day_patterns[d])/len(day_patterns[d])) if day_patterns else None,
            'emotion_distribution': emotion_count
        }
        
        return patterns
    
    def get_wellness_score(self):
        """Calcule un score de bien-être global"""
        if not self.history:
            return 0
        
        recent_entries = self.history[:7]  # Dernière semaine
        if not recent_entries:
            return 0
        
        # Score basé sur la moyenne récente et la stabilité
        scores = [entry['mood_score'] for entry in recent_entries]
        average_score = sum(scores) / len(scores)
        
        # Pénalité pour l'instabilité
        stability = 1 - (max(scores) - min(scores)) / 10
        wellness_score = average_score * stability
        
        return round(wellness_score, 2)

# ===============================
# 🎯 PROGRAMME DE DÉFI QUOTIDIEN
# ===============================
class DailyChallengeGenerator:
    def __init__(self):
        self.challenges = {
            'mindfulness': [
                "Practice 5 minutes of mindful breathing",
                "Do a body scan meditation",
                "Practice mindful eating for one meal",
                "Take a mindful walk without distractions"
            ],
            'gratitude': [
                "Write down 3 things you're grateful for",
                "Send a thank you message to someone",
                "Notice and appreciate one small beauty today",
                "Create a gratitude jar entry"
            ],
            'self_care': [
                "Do one thing purely for enjoyment",
                "Take a technology-free break",
                "Prepare a healthy meal mindfully",
                "Get 7-8 hours of quality sleep"
            ],
            'social': [
                "Reach out to a friend or family member",
                "Give someone a genuine compliment",
                "Practice active listening in a conversation",
                "Share something positive with others"
            ],
            'physical': [
                "Take a 10-minute walk outside",
                "Do 5 minutes of stretching",
                "Try a new physical activity",
                "Practice deep breathing exercises"
            ]
        }
    
    def generate_daily_challenge(self, user_mood, user_emotion):
        """Génère un défi personnalisé selon l'humeur"""
        
        # Sélection de la catégorie selon l'humeur
        if user_mood < 4:
            category = 'self_care'
        elif user_mood < 7:
            category = 'mindfulness'
        else:
            category = 'social'
        
        # Ajustement selon l'émotion
        emotion_mapping = {
            'stress': 'mindfulness',
            'anxiety': 'physical',
            'sadness': 'gratitude',
            'anger': 'physical',
            'joy': 'social'
        }
        
        category = emotion_mapping.get(user_emotion, category)
        challenge = random.choice(self.challenges[category])
        
        return {
            'challenge': challenge,
            'category': category,
            'estimated_time': "5-10 minutes",
            'benefit': self._get_challenge_benefit(category)
        }
    
    def _get_challenge_benefit(self, category):
        """Retourne les bénéfices du défi"""
        benefits = {
            'mindfulness': "Reduces stress and increases present-moment awareness",
            'gratitude': "Improves mood and shifts perspective positively",
            'self_care': "Recharges your energy and prevents burnout",
            'social': "Strengthens connections and reduces loneliness",
            'physical': "Boosts energy and improves mental clarity"
        }
        return benefits.get(category, "Improves overall well-being")

# ===============================
# 🧹 TEXT PROCESSING INTELLIGENT
# ===============================
class TextProcessor:
    @staticmethod
    def clean_text(text):
        """Nettoie le texte en conservant le contexte émotionnel"""
        text = str(text).lower().strip()
        text = re.sub(r'[^\w\s\.\!\?]', '', text)
        return text
    
    @staticmethod
    def extract_emotional_context(text):
        """Extrait le contexte émotionnel du texte"""
        emotional_indicators = {
            'stress': ['stress', 'pressure', 'overwhelmed', 'burnout', 'anxious'],
            'depression': ['sad', 'hopeless', 'empty', 'numb', 'nothing matters'],
            'anxiety': ['worry', 'nervous', 'panic', 'fear', 'scared'],
            'anger': ['angry', 'frustrated', 'irritated', 'mad', 'furious'],
            'joy': ['happy', 'joy', 'excited', 'good', 'great', 'wonderful'],
            'calm': ['calm', 'peaceful', 'relaxed', 'serene', 'content']
        }
        
        context = {}
        text_lower = text.lower()
        
        for category, indicators in emotional_indicators.items():
            matches = [indicator for indicator in indicators if indicator in text_lower]
            if matches:
                context[category] = len(matches)
        
        return context

# ===============================
# 💬 EMOTION DETECTION
# ===============================
class EmotionDetector:
    @staticmethod
    def detect_emotion(text):
        """Détecte l'émotion principale du texte"""
        if not text or len(text.strip()) < 3:
            return "neutral"
        
        # Utilisation du modèle HF
        if model_manager.models.get('emotion_pipeline'):
            try:
                result = model_manager.models['emotion_pipeline'](
                    text, 
                    max_length=20
                )[0]['generated_text']
                emotion = result.strip().lower()
                return emotion if emotion else "neutral"
            except Exception as e:
                logger.warning(f"Emotion detection failed: {e}")
        
        # Fallback par analyse de mots-clés
        return EmotionDetector.fallback_emotion_detection(text)
    
    @staticmethod
    def fallback_emotion_detection(text):
        """Détection d'émotion par mots-clés"""
        text_lower = text.lower()
        
        emotion_keywords = {
            'joy': ['happy', 'good', 'great', 'wonderful', 'excited', 'joy'],
            'sadness': ['sad', 'depressed', 'unhappy', 'miserable', 'hopeless'],
            'anger': ['angry', 'mad', 'furious', 'annoyed', 'frustrated'],
            # broaden fear/anxiety keywords to capture panic and breathing-related phrases
            'fear': ['scared', 'afraid', 'anxious', 'nervous', 'worried', 'panic', 'panic attack', "can't breathe", 'cant breathe', 'breathless', 'hyperventilating', 'closing in'],
            'stress': ['stressed', 'overwhelmed', 'pressure', 'burnout'],
            'love': ['love', 'care', 'affection', 'compassion']
        }
        
        for emotion, keywords in emotion_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                return emotion
        
        # Analyse de sentiment comme dernier recours
        sentiment = TextBlob(text).sentiment.polarity
        if sentiment > 0.1:
            return "joy"
        elif sentiment < -0.1:
            return "sadness"
        
        return "neutral"

# ===============================
# 🧩 QUIZ GENERATOR INTELLIGENT
# ===============================
class QuizGenerator:
    @staticmethod
    def generate_contextual_quiz(emotion, user_text, emotional_context):
        """Génère un quiz contextuel basé sur l'émotion détectée"""
        
        # Quiz templates par émotion
        quiz_templates = {
            'stress': [
                {
                    "question": "What is the main source of your current stress?",
                    "options": ["Work/studies", "Personal relationships", "Health issues", "Future uncertainty"]
                },
                {
                    "question": "How do you usually manage stress?",
                    "options": ["Talk to someone", "Exercise", "Isolate myself", "Procrastinate"]
                },
                {
                    "question": "Your current energy level is:",
                    "options": ["Very low", "Low", "Moderate", "High"]
                }
            ],
            'sadness': [
                {
                    "question": "How long have you been feeling this way?",
                    "options": ["A few days", "A few weeks", "A few months", "More than a year"]
                },
                {
                    "question": "What brings you comfort right now?",
                    "options": ["Nothing really", "Close relationships", "Hobbies", "Nature"]
                },
                {
                    "question": "Your appetite and sleep are:",
                    "options": ["Normal", "Disturbed", "Very affected", "Variable"]
                }
            ],
            'fear': [
                {
                    "question": "Your worries are mainly about:",
                    "options": ["The future", "Health", "Relationships", "Work"]
                },
                {
                    "question": "How does your anxiety manifest physically?",
                    "options": ["Heart palpitations", "Muscle tension", "Digestive issues", "Insomnia"]
                },
                {
                    "question": "Your ability to concentrate is:",
                    "options": ["Normal", "Slightly affected", "Very affected", "Intermittent"]
                }
            ],
            'anger': [
                {
                    "question": "What is the main cause of your anger?",
                    "options": ["Injustice", "Personal frustration", "Relationship conflict", "Accumulated stress"]
                },
                {
                    "question": "How do you express your anger?",
                    "options": ["Internalize it", "Isolate myself", "Express calmly", "Explode"]
                },
                {
                    "question": "Your current frustration level is:",
                    "options": ["Manageable", "High but controlled", "Very high", "Uncontrollable"]
                }
            ],
            'joy': [
                {
                    "question": "What is bringing you the most joy currently?",
                    "options": ["Personal achievements", "Social connections", "Simple pleasures", "Future prospects"]
                },
                {
                    "question": "How are you sharing your positive energy?",
                    "options": ["With friends/family", "Through creative projects", "Helping others", "Keeping it to myself"]
                },
                {
                    "question": "Your motivation level is:",
                    "options": ["Very high", "High", "Moderate", "Variable"]
                }
            ]
        }
        
        # Sélection du quiz selon l'émotion
        quiz = quiz_templates.get(emotion, [
            {
                "question": "How would you describe your current emotional state?",
                "options": ["Calm and balanced", "A bit agitated", "Very emotional", "Unstable"]
            },
            {
                "question": "What support would be most helpful to you right now?",
                "options": ["Listening and understanding", "Practical advice", "Personal space", "Professional support"]
            },
            {
                "question": "Your current motivation level is:",
                "options": ["High", "Medium", "Low", "Very low"]
            }
        ])
        
        return quiz

# ===============================
# 🧠 ANALYSE ET CONCLUSION INTELLIGENTE
# ===============================
class MentalHealthAnalyst:
    @staticmethod
    def calculate_mood_score(emotion, text, emotional_context):
        """Calcule un score d'humeur complet"""
        emotion_scores = {
            'joy': 8, 'love': 9, 'calm': 7, 'neutral': 5,
            'sadness': 3, 'anger': 2, 'fear': 3, 'stress': 4, 'anxiety': 3
        }
        
        base_score = emotion_scores.get(emotion, 5)
        
        # Analyse de sentiment
        sentiment = TextBlob(text).sentiment
        sentiment_adjustment = sentiment.polarity * 3
        
        # Ajustement selon le contexte émotionnel
        context_adjustment = 0
        if 'stress' in emotional_context:
            context_adjustment -= emotional_context['stress'] * 0.5
        if 'joy' in emotional_context:
            context_adjustment += emotional_context['joy'] * 0.5
        
        final_score = base_score + sentiment_adjustment + context_adjustment
        final_score = max(1, min(10, round(final_score, 2)))
        
        score_percent = (final_score / 10) * 100
        
        return final_score, score_percent, round(sentiment.polarity, 2)
    
    @staticmethod
    def generate_personalized_conclusion(emotion, mood_score, user_text, emotional_context):
        """Génère une conclusion personnalisée basée sur l'analyse complète"""
        
        conclusions = {
            'high': {
                'stress': "Despite high stress levels, you seem aware of your emotions. This self-awareness is a significant strength for managing challenges.",
                'sadness': "Your sadness is understandable. Sharing your feelings is already an important step toward well-being.",
                'fear': "Your anxiety seems related to real concerns. Identifying these sources is crucial for managing them.",
                'anger': "Your anger indicates unmet needs. Expressing it constructively can be liberating.",
                'default': "You're going through an emotionally intense period. Your ability to self-reflect is remarkable."
            },
            'medium': {
                'stress': "You're managing daily stress well, but some tension persists. Regular breaks could help maintain balance.",
                'sadness': "Your mood seems fluctuating. Cultivating simple joyful moments could rebalance your emotional state.",
                'fear': "Your anxiety is present but manageable. Breathing techniques could strengthen your sense of control.",
                'anger': "Your frustration is understandable. Finding healthy channels for expression could prevent accumulation.",
                'default': "Your emotional state shows resilience. Continue listening to your needs."
            },
            'low': {
                'stress': "You seem generally serene facing challenges. This attitude benefits your overall well-being.",
                'sadness': "Your mood is rather stable and positive. This emotional balance is valuable to maintain.",
                'fear': "You handle uncertainty well. This ability is an important asset in daily life.",
                'anger': "Your inner calm is apparent. This serenity helps you navigate difficult situations.",
                'default': "Your emotional state seems balanced. This stability is a solid foundation for your well-being."
            }
        }
        
        # Détermination du niveau
        if mood_score >= 7:
            level = 'low'
        elif mood_score >= 4:
            level = 'medium'
        else:
            level = 'high'
        
        # Sélection de la conclusion
        emotion_conclusions = conclusions[level]
        conclusion = emotion_conclusions.get(emotion, emotion_conclusions['default'])
        
        # Personnalisation supplémentaire basée sur le texte utilisateur
        if "alone" in user_text.lower() or "lonely" in user_text.lower():
            conclusion += " The loneliness you express is important to acknowledge. Social connections, even small ones, can bring comfort."
        
        if "tired" in user_text.lower() or "exhausted" in user_text.lower():
            conclusion += " Your mentioned fatigue deserves attention. Quality rest is essential for emotional health."
        
        if "work" in user_text.lower() or "job" in user_text.lower():
            conclusion += " Work-related concerns are common. Setting healthy boundaries can help maintain work-life balance."
        
        return conclusion
    
    @staticmethod
    def generate_recommendations(emotion, mood_score, conclusion):
        """Génère des recommandations personnalisées"""
        
        base_recommendations = {
            'stress': [
                "Practice the 4-7-8 breathing technique (inhale 4s, hold 7s, exhale 8s)",
                "Break large tasks into small achievable steps",
                "Establish clear boundaries between work and personal life"
            ],
            'sadness': [
                "Create a daily gratitude ritual (3 positive things per day)",
                "Reach out to a friend or loved one to share a moment",
                "Try a creative activity like drawing or writing"
            ],
            'fear': [
                "Practice mindfulness meditation for 10 minutes daily",
                "Write down your worries in a journal then challenge them",
                "Limit your exposure to anxiety-provoking news"
            ],
            'anger': [
                "Use physical activity to channel anger energy",
                "Express your needs clearly using 'I' statements",
                "Practice reflective pausing before responding in anger"
            ],
            'joy': [
                "Share your positive energy with others through acts of kindness",
                "Document this positive period in a joy journal",
                "Use this energy to start a project you've been postponing"
            ]
        }
        
        recommendations = base_recommendations.get(emotion, [
            "Practice self-compassion by speaking to yourself as you would to a friend",
            "Maintain a stable routine with moments of pleasure",
            "Listen to your fundamental needs (sleep, nutrition, movement)"
        ])
        
        # Ajustements selon le score
        if mood_score < 4:
            recommendations.insert(0, "Consider consulting a mental health professional for additional support")
        elif mood_score > 7:
            recommendations.insert(0, "Your positive energy is contagious! Consider sharing it with others")
        
        return recommendations

# ===============================
# 🌟 APPLICATION PRINCIPALE
# ===============================
class MentalHealthAssistant:
    def __init__(self):
        self.text_processor = TextProcessor()
        self.emotion_detector = EmotionDetector()
        self.quiz_generator = QuizGenerator()
        self.analyst = MentalHealthAnalyst()
        self.chatbot = TherapeuticChatbot()
        self.challenge_generator = DailyChallengeGenerator()
        self.history_entries = []
        self.max_history = 10

    def process_user_input(self, user_text, quiz_responses=None):
        """Traite l'entrée utilisateur et génère une analyse complète"""

        # Nettoyage et analyse du texte
        cleaned_text = self.text_processor.clean_text(user_text)
        emotional_context = self.text_processor.extract_emotional_context(user_text)

        # Détection d'émotion (robuste, avec fallback déjà géré dans EmotionDetector)
        emotion = self.emotion_detector.detect_emotion(user_text)

        # =========================
        # Prédiction ML (robuste)
        # =========================
        prediction = "unknown"
        try:
            vec = model_manager.models.get('vectorizer')
            clf = model_manager.models.get('classifier')
            le = model_manager.models.get('label_encoder')

            if vec is None or clf is None or le is None:
                raise RuntimeError("ML models not loaded")

            X = vec.transform([cleaned_text])  # peut lever NotFittedError
            y_hat = clf.predict(X)
            prediction = le.inverse_transform(y_hat)[0]
        except NotFittedError as e:
            logger.warning(f"Vectorizer not fitted, fallback prediction used: {e}")
            # Fallback simple et déterministe : utiliser l'émotion détectée
            prediction = emotion
        except Exception as e:
            logger.warning(f"ML prediction failed, fallback used: {e}")
            prediction = emotion

        # Calcul du score d'humeur
        mood_score, score_percent, sentiment_score = self.analyst.calculate_mood_score(
            emotion, user_text, emotional_context
        )

        # Génération du quiz contextuel
        quiz = self.quiz_generator.generate_contextual_quiz(emotion, user_text, emotional_context)

        # Génération de la conclusion personnalisée
        conclusion = self.analyst.generate_personalized_conclusion(
            emotion, mood_score, user_text, emotional_context
        )

        # Génération des recommandations
        recommendations = self.analyst.generate_recommendations(emotion, mood_score, conclusion)

        # Génération du défi quotidien
        daily_challenge = self.challenge_generator.generate_daily_challenge(mood_score, emotion)

        # Tags basés sur le contexte émotionnel
        tags = list(emotional_context.keys())[:3]

        # Création de l'entrée d'historique (avec id pour CRUD côté client)
        history_entry = {
            'id': uuid.uuid4().hex,
            "created_at": datetime.now(),
            "text": user_text,
            "emotion": emotion,
            "prediction": prediction,
            "mood_score": mood_score,
            "score_percent": score_percent,
            "sentiment_score": sentiment_score,
            "conclusion": conclusion,
            "recommendations": recommendations,
            "quiz": quiz,
            "daily_challenge": daily_challenge,
            "tags": ", ".join(tags) if tags else "general"
        }

        # Mise à jour de l'historique
        self.history_entries.insert(0, history_entry)
        self.history_entries = self.history_entries[:self.max_history]

        # Tableau de bord
        dashboard = PersonalDashboard(self.history_entries)

        return {
            'prediction': prediction,
            'emotion': emotion,
            'mood_score': mood_score,
            'score_percent': score_percent,
            'conclusion': conclusion,
            'recommendations': recommendations,
            'quiz': quiz,
            'daily_challenge': daily_challenge,
            'user_text': user_text,
            'entries': self.history_entries,
            'average_score': self.get_average_score(),
            'analysis_complete': True,
            'quiz_responses': quiz_responses,
            'wellness_score': dashboard.get_wellness_score(),
            'weekly_trends': dashboard.get_weekly_trends(),
            'emotion_patterns': dashboard.get_emotion_patterns()
        }

    def chat_with_bot(self, user_message):
        """Interagit avec le chatbot thérapeutique"""
        # Détection d'émotion pour le message de chat
        emotion = self.emotion_detector.detect_emotion(user_message)

        # Génération de la réponse
        bot_response = self.chatbot.generate_response(user_message, emotion, self.history_entries)

        return {
            'user_message': user_message,
            'bot_response': bot_response,
            'emotion': emotion,
            'conversation_summary': self.chatbot.get_conversation_summary()
        }

    def get_average_score(self):
        """Calcule le score moyen"""
        if not self.history_entries:
            return 0
        return round(sum(entry['mood_score'] for entry in self.history_entries) / len(self.history_entries), 2)


# Instance globale (laisse cette ligne en bas du fichier)
mental_health_app = MentalHealthAssistant()


# ===============================
# 🎯 VIEWS PRINCIPALES
# ===============================
@csrf_exempt
def predict_text(request):
    """Vue principale pour l'analyse de texte avec quiz"""
    try:
        if request.method == 'POST':
            user_text = request.POST.get('text', '').strip()
            
            if not user_text:
                return render(request, 'mental/Mental.html', {
                    'error': "Please share your feelings for a personalized analysis.",
                    'entries': mental_health_app.history_entries,
                    'average_score': mental_health_app.get_average_score()
                })
            
            # Traitement complet
            result = mental_health_app.process_user_input(user_text)
            return render(request, 'mental/Mental.html', result)
        
        # Requête GET - affichage de l'historique
        return render(request, 'mental/Mental.html', {
            'entries': mental_health_app.history_entries,
            'average_score': mental_health_app.get_average_score()
        })
        
    except Exception as e:
        logger.error(f"Error in predict_text: {e}")
        return render(request, 'mental/Mental.html', {
            'error': "An error occurred during analysis. Please try again.",
            'entries': mental_health_app.history_entries,
            'average_score': mental_health_app.get_average_score()
        })

@csrf_exempt
def submit_quiz(request):
    """Vue pour traiter les réponses du quiz"""
    if request.method == 'POST':
        try:
            user_text = request.POST.get('original_text', '')
            
            if user_text:
                # Retraiter l'analyse avec le texte original
                result = mental_health_app.process_user_input(user_text)
                result['quiz_completed'] = True
                result['success_message'] = "Thank you for completing the assessment! Your analysis has been updated."
                return render(request, 'mental/Mental.html', result)
            else:
                return render(request, 'mental/Mental.html', {
                    'error': "No text provided for analysis.",
                    'entries': mental_health_app.history_entries,
                    'average_score': mental_health_app.get_average_score()
                })
            
        except Exception as e:
            logger.error(f"Error in submit_quiz: {e}")
        
        return render(request, 'mental/Mental.html', {
            'error': "Error processing quiz responses.",
            'entries': mental_health_app.history_entries
        })
    
    # Si GET, rediriger vers la page principale
    return render(request, 'mental/Mental.html', {
        'entries': mental_health_app.history_entries,
        'average_score': mental_health_app.get_average_score()
    })

@csrf_exempt
@csrf_exempt
def chat_with_bot(request):
    """Vue améliorée pour le chatbot"""
    # Helper to detect AJAX requests robustly (case-insensitive)
    def _is_ajax(req):
        return req.headers.get('X-Requested-With', req.headers.get('x-requested-with', '')).lower() == 'xmlhttprequest'

    if request.method == 'POST':
        try:
            user_message = request.POST.get('message', '').strip()

            if user_message:
                # Utiliser le chatbot amélioré
                result = mental_health_app.chat_with_bot(user_message)

                # If this is an AJAX request, return JSON with bot response and recent conversation
                if _is_ajax(request):
                    # Serialize the last 10 conversation messages
                    conv = []
                    for m in mental_health_app.chatbot.conversation_history[-10:]:
                        conv.append({
                            'timestamp': m.get('timestamp').isoformat() if hasattr(m.get('timestamp'), 'isoformat') else str(m.get('timestamp')),
                            'user': m.get('user'),
                            'bot': m.get('bot'),
                            'technique': m.get('technique')
                        })
                    return JsonResponse({
                        'bot_response': result.get('bot_response'),
                        'emotion': result.get('emotion'),
                        'conversation': conv
                    })

                # Non-AJAX: render full page
                return render(request, 'mental/Mental.html', {
                    'chat_result': result,
                    'chat_messages': mental_health_app.chatbot.conversation_history[-10:],  # Derniers 10 messages
                    'entries': mental_health_app.history_entries,
                    'average_score': mental_health_app.get_average_score(),
                    'active_tab': 'chatbot'  # Pour rester sur l'onglet chatbot
                })
            else:
                # If AJAX, return JSON error
                if _is_ajax(request):
                    return JsonResponse({'error': 'Please enter a message to chat.'}, status=400)
                return render(request, 'mental/Mental.html', {
                    'error': "Please enter a message to chat.",
                    'entries': mental_health_app.history_entries,
                    'average_score': mental_health_app.get_average_score(),
                    'active_tab': 'chatbot'
                })

        except Exception as e:
            logger.exception(f"Error in chat_with_bot: {e}")
            # If AJAX, return JSON error (avoid returning HTML which breaks client-side JSON.parse)
            if _is_ajax(request):
                return JsonResponse({'error': 'Error processing chat message.'}, status=500)

        return render(request, 'mental/Mental.html', {
            'error': "Error processing chat message.",
            'entries': mental_health_app.history_entries,
            'average_score': mental_health_app.get_average_score(),
            'active_tab': 'chatbot'
        })

    return render(request, 'mental/Mental.html', {
        'entries': mental_health_app.history_entries,
        'average_score': mental_health_app.get_average_score(),
        'active_tab': 'chatbot'
    })
@csrf_exempt
def clear_history(request):
    """Vue pour effacer l'historique"""
    if request.method == 'POST':
        mental_health_app.history_entries.clear()
        return render(request, 'mental/Mental.html', {
            'entries': [],
            'average_score': 0,
            'success_message': "History cleared successfully."
        })
    return render(request, 'mental/Mental.html')


@csrf_exempt
def edit_entry(request):
    """Edit an existing in-memory history entry (AJAX)."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed'}, status=405)

    entry_id = request.POST.get('id') or request.POST.get('entry_id')
    new_text = request.POST.get('text')
    new_emotion = request.POST.get('emotion')

    if not entry_id:
        return JsonResponse({'error': 'Missing entry id'}, status=400)

    # Find entry
    entry = next((e for e in mental_health_app.history_entries if e.get('id') == entry_id), None)
    if not entry:
        return JsonResponse({'error': 'Entry not found'}, status=404)

    # Update fields
    if new_text is not None:
        entry['text'] = new_text
    if new_emotion is not None:
        entry['emotion'] = new_emotion

    # Recompute derived fields
    emotional_context = mental_health_app.text_processor.extract_emotional_context(entry.get('text', ''))
    mood_score, score_percent, sentiment_score = mental_health_app.analyst.calculate_mood_score(
        entry.get('emotion', 'neutral'), entry.get('text', ''), emotional_context
    )
    entry['mood_score'] = mood_score
    entry['score_percent'] = score_percent
    entry['sentiment_score'] = sentiment_score

    # Regenerate conclusion and recommendations
    entry['conclusion'] = mental_health_app.analyst.generate_personalized_conclusion(
        entry.get('emotion', 'neutral'), mood_score, entry.get('text', ''), emotional_context
    )
    entry['recommendations'] = mental_health_app.analyst.generate_recommendations(
        entry.get('emotion', 'neutral'), mood_score, entry.get('conclusion', '')
    )

    # Update tags
    tags = list(emotional_context.keys())[:3]
    entry['tags'] = ", ".join(tags) if tags else "general"

    # Return updated entry (serialize created_at)
    serialized = entry.copy()
    created = serialized.get('created_at')
    serialized['created_at'] = created.isoformat() if hasattr(created, 'isoformat') else str(created)

    return JsonResponse({'updated': serialized})


@csrf_exempt
def delete_entry(request):
    """Delete an existing in-memory history entry (AJAX)."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST allowed'}, status=405)

    entry_id = request.POST.get('id') or request.POST.get('entry_id')
    if not entry_id:
        return JsonResponse({'error': 'Missing entry id'}, status=400)

    idx = next((i for i, e in enumerate(mental_health_app.history_entries) if e.get('id') == entry_id), None)
    if idx is None:
        return JsonResponse({'error': 'Entry not found'}, status=404)

    # Remove entry
    mental_health_app.history_entries.pop(idx)

    return JsonResponse({'deleted': entry_id, 'remaining': len(mental_health_app.history_entries)})