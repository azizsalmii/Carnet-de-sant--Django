"""
Extended rules with multiple variations to avoid repetition.
Each health condition has 3-5 different recommendation texts.
"""
import random


def get_sleep_recommendations():
    """Multiple sleep recommendations to rotate."""
    return [
        'Essayez d\'éviter les écrans 1 heure avant de dormir pour améliorer la qualité du sommeil.',
        'Créez une routine de coucher relaxante : lecture, méditation ou musique douce pendant 20 minutes.',
        'Gardez votre chambre fraîche (18-20°C) et sombre pour favoriser un sommeil réparateur.',
        'Évitez la caféine après 15h et l\'alcool 3h avant le coucher pour un meilleur sommeil.',
        'Essayez la technique 4-7-8 : inspirez 4s, retenez 7s, expirez 8s pour vous endormir plus vite.',
    ]


def get_activity_recommendations():
    """Multiple activity recommendations to rotate."""
    return [
        'Faites une marche de 10-15 minutes après le déjeuner pour augmenter votre activité quotidienne.',
        'Montez les escaliers au lieu de prendre l\'ascenseur : 3 étages = 30 calories brûlées.',
        'Essayez le "desk yoga" : 5 minutes d\'étirements toutes les 2 heures au bureau.',
        'Dansez sur 3 chansons préférées par jour : fun et excellent cardio (150 calories).',
        'Marchez en parlant au téléphone : transformez 30 min d\'appels en 2000 pas.',
        'Faites une pause active : 10 squats + 10 pompes murales toutes les heures.',
    ]


def get_bp_high_recommendations():
    """Multiple BP recommendations for high pressure."""
    return [
        'Votre tension artérielle est élevée. Réduisez le sel, gérez le stress et consultez votre médecin.',
        'Tension élevée détectée. Essayez la respiration profonde 10 min/jour et limitez le sel à 5g/jour.',
        'Hypertension constatée. Privilégiez les fruits, légumes et poissons gras (oméga-3).',
        'Pression élevée : marchez 30 min/jour, évitez l\'alcool et consultez pour un suivi médical.',
        'Votre tension nécessite attention : réduisez le stress, dormez 7-8h et mangez moins salé.',
    ]


def get_bp_moderate_recommendations():
    """Multiple BP recommendations for moderate elevation."""
    return [
        'Votre tension artérielle commence à augmenter. Surveillez-la régulièrement et adoptez un mode de vie sain.',
        'Tension en hausse : pratiquez 150 min d\'activité modérée par semaine et réduisez le sel.',
        'Pression sanguine à surveiller : adoptez le régime DASH (fruits, légumes, grains entiers).',
        'Tension pré-hypertensive : limitez le café, buvez plus d\'eau et gérez votre stress.',
        'Augmentation de la tension détectée : perdez 2-3 kg si surpoids, cela aide énormément.',
    ]


def get_stress_recommendations():
    """Multiple stress management recommendations."""
    return [
        'Essayez des techniques de relaxation comme la méditation ou le yoga pour gérer le stress.',
        'Pratiquez la cohérence cardiaque : 6 respirations/min pendant 5 min, 3x/jour.',
        'Adoptez la règle des 5-5-5 : 5 min de gratitude matin, 5 min de pause midi, 5 min de détente soir.',
        'Essayez l\'application Petit Bambou ou Calm pour 10 min de méditation guidée quotidienne.',
        'Tenez un journal : écrivez 3 choses positives chaque soir pour réduire l\'anxiété.',
    ]


def get_hydration_recommendations():
    """Multiple hydration recommendations."""
    return [
        'Pensez à boire 1.5-2 litres d\'eau par jour pour maintenir une bonne hydratation.',
        'Buvez un grand verre d\'eau au réveil pour réhydrater votre corps après la nuit.',
        'Gardez une bouteille d\'eau à portée de main : objectif 8 verres de 250ml par jour.',
        'Variez avec des infusions : citron, gingembre, menthe pour une hydratation savoureuse.',
        'Mangez des aliments riches en eau : concombre, pastèque, tomate (20% de vos besoins).',
    ]


def get_nutrition_recommendations():
    """Multiple nutrition recommendations."""
    return [
        'Privilégiez les repas équilibrés avec légumes, protéines maigres et grains entiers.',
        'Adoptez la règle de l\'assiette : 1/2 légumes, 1/4 protéines, 1/4 glucides complexes.',
        'Mangez l\'arc-en-ciel : 5 couleurs de fruits/légumes par jour pour tous les nutriments.',
        'Préparez vos repas le dimanche : meal prep de 4-5 repas sains pour la semaine.',
        'Réduisez les aliments ultra-transformés : privilégiez le fait maison et le frais.',
    ]


def get_morning_sunlight_recommendations():
    """Multiple morning light recommendations."""
    return [
        'Exposez-vous à la lumière naturelle le matin pour réguler votre rythme circadien.',
        'Ouvrez les volets dès le réveil : 15 min de lumière naturelle boost votre énergie.',
        'Prenez votre café/thé près d\'une fenêtre : combinez routine matinale et exposition lumineuse.',
        'Marchez 10 min dehors le matin : lumière + mouvement = réveil optimal du corps.',
    ]


def get_schedule_recommendations():
    """Multiple routine/schedule recommendations."""
    return [
        'Établissez un horaire de sommeil régulier en vous couchant et levant à heures fixes.',
        'Créez une routine matinale : même heure de réveil tous les jours, même le week-end.',
        'Planifiez vos repas à heures régulières : 3 repas + 1 collation si besoin.',
        'Bloquez 30 min d\'activité physique à la même heure chaque jour pour créer l\'habitude.',
    ]


def get_standing_breaks_recommendations():
    """Multiple recommendations for breaking sedentary time."""
    return [
        'Levez-vous et étirez-vous toutes les heures si vous travaillez assis.',
        'Réglez une alarme toutes les 60 min : 2 min d\'étirements pour contrer la sédentarité.',
        'Marchez pendant les réunions téléphoniques : stimule la créativité et réduit la fatigue.',
        'Essayez le "standing desk" 2h par jour : alternez assis/debout pour votre santé.',
    ]
