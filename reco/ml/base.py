"""
Base classes and utilities for ML model training.

Provides infrastructure for:
- Model versioning
- Training pipeline
- Evaluation metrics
- Model persistence
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, List, Tuple, Any, Optional
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class BaseRecommendationModel(ABC):
    """
    Abstract base class for recommendation models.
    
    Defines the interface that all recommendation models must implement.
    """
    
    def __init__(self, model_id: str, version: str):
        """
        Initialize model.
        
        Args:
            model_id: Unique identifier for this model
            version: Model version string
        """
        self.model_id = model_id
        self.version = version
        self.trained_at = None
        self.metadata = {}
    
    @abstractmethod
    def train(self, features: List[Dict], labels: List[Dict]) -> Dict:
        """
        Train the model on provided data.
        
        Args:
            features: List of feature dictionaries
            labels: List of label/outcome dictionaries
            
        Returns:
            Training metrics dictionary
        """
        pass
    
    @abstractmethod
    def predict(self, features: Dict) -> List[Dict]:
        """
        Generate recommendations for given features.
        
        Args:
            features: Feature dictionary for one user
            
        Returns:
            List of recommendation dictionaries with category, text, score
        """
        pass
    
    @abstractmethod
    def evaluate(self, features: List[Dict], labels: List[Dict]) -> Dict:
        """
        Evaluate model performance on test data.
        
        Args:
            features: List of feature dictionaries
            labels: List of ground truth labels
            
        Returns:
            Evaluation metrics dictionary
        """
        pass
    
    def save(self, filepath: Path) -> bool:
        """
        Save model to disk.
        
        Args:
            filepath: Path to save model
            
        Returns:
            True if successful
        """
        try:
            model_data = {
                'model_id': self.model_id,
                'version': self.version,
                'trained_at': self.trained_at.isoformat() if self.trained_at else None,
                'metadata': self.metadata,
                'model_state': self._get_model_state(),
            }
            
            filepath.parent.mkdir(parents=True, exist_ok=True)
            with open(filepath, 'w') as f:
                json.dump(model_data, f, indent=2)
            
            logger.info(f"Model saved to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to save model: {e}")
            return False
    
    def load(self, filepath: Path) -> bool:
        """
        Load model from disk.
        
        Args:
            filepath: Path to load model from
            
        Returns:
            True if successful
        """
        try:
            with open(filepath, 'r') as f:
                model_data = json.load(f)
            
            self.model_id = model_data['model_id']
            self.version = model_data['version']
            self.trained_at = datetime.fromisoformat(model_data['trained_at']) if model_data['trained_at'] else None
            self.metadata = model_data['metadata']
            self._set_model_state(model_data['model_state'])
            
            logger.info(f"Model loaded from {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False
    
    @abstractmethod
    def _get_model_state(self) -> Dict:
        """Get model-specific state for serialization."""
        pass
    
    @abstractmethod
    def _set_model_state(self, state: Dict):
        """Set model-specific state from deserialization."""
        pass


class ModelEvaluator:
    """Evaluate recommendation model performance."""
    
    @staticmethod
    def compute_precision_at_k(predictions: List[Dict], ground_truth: List[Dict], k: int = 5) -> float:
        """
        Compute precision@k for recommendations.
        
        Args:
            predictions: List of predicted recommendations
            ground_truth: List of actual helpful recommendations
            k: Number of top recommendations to consider
            
        Returns:
            Precision@k score
        """
        if not predictions or not ground_truth:
            return 0.0
        
        top_k_pred = predictions[:k]
        relevant_count = sum(
            1 for pred in top_k_pred
            if any(gt['category'] == pred['category'] for gt in ground_truth)
        )
        
        return relevant_count / k
    
    @staticmethod
    def compute_recall_at_k(predictions: List[Dict], ground_truth: List[Dict], k: int = 5) -> float:
        """
        Compute recall@k for recommendations.
        
        Args:
            predictions: List of predicted recommendations
            ground_truth: List of actual helpful recommendations
            k: Number of top recommendations to consider
            
        Returns:
            Recall@k score
        """
        if not ground_truth:
            return 0.0
        
        top_k_pred = predictions[:k]
        relevant_count = sum(
            1 for gt in ground_truth
            if any(pred['category'] == gt['category'] for pred in top_k_pred)
        )
        
        return relevant_count / len(ground_truth)
    
    @staticmethod
    def compute_ndcg(predictions: List[Dict], ground_truth: List[Dict], k: int = 5) -> float:
        """
        Compute Normalized Discounted Cumulative Gain (NDCG@k).
        
        Measures ranking quality of recommendations.
        
        Args:
            predictions: List of predicted recommendations with scores
            ground_truth: List of actual helpful recommendations with relevance
            k: Number of top recommendations to consider
            
        Returns:
            NDCG@k score
        """
        import math
        
        if not predictions or not ground_truth:
            return 0.0
        
        # DCG for predictions
        dcg = 0.0
        for i, pred in enumerate(predictions[:k]):
            # Find if this prediction matches ground truth
            relevance = 0
            for gt in ground_truth:
                if gt['category'] == pred['category']:
                    relevance = gt.get('relevance', 1)  # Default relevance = 1
                    break
            
            if relevance > 0:
                dcg += relevance / math.log2(i + 2)  # i+2 because i is 0-indexed
        
        # IDCG (ideal DCG) - if all ground truth items were ranked first
        sorted_relevances = sorted([gt.get('relevance', 1) for gt in ground_truth], reverse=True)
        idcg = sum(rel / math.log2(i + 2) for i, rel in enumerate(sorted_relevances[:k]))
        
        return dcg / idcg if idcg > 0 else 0.0
    
    @classmethod
    def evaluate_model(cls, predictions_by_user: Dict[int, List[Dict]], 
                      ground_truth_by_user: Dict[int, List[Dict]]) -> Dict:
        """
        Comprehensive model evaluation.
        
        Args:
            predictions_by_user: Dict mapping user_id -> list of predictions
            ground_truth_by_user: Dict mapping user_id -> list of helpful recommendations
            
        Returns:
            Dictionary with evaluation metrics
        """
        all_precision = []
        all_recall = []
        all_ndcg = []
        
        for user_id in predictions_by_user:
            preds = predictions_by_user[user_id]
            truth = ground_truth_by_user.get(user_id, [])
            
            if not truth:  # Skip users with no ground truth
                continue
            
            precision = cls.compute_precision_at_k(preds, truth, k=5)
            recall = cls.compute_recall_at_k(preds, truth, k=5)
            ndcg = cls.compute_ndcg(preds, truth, k=5)
            
            all_precision.append(precision)
            all_recall.append(recall)
            all_ndcg.append(ndcg)
        
        if not all_precision:
            return {
                'error': 'No users with ground truth data',
                'num_users': 0,
            }
        
        return {
            'num_users': len(all_precision),
            'precision@5': round(sum(all_precision) / len(all_precision), 4),
            'recall@5': round(sum(all_recall) / len(all_recall), 4),
            'ndcg@5': round(sum(all_ndcg) / len(all_ndcg), 4),
            'f1@5': round(
                2 * (sum(all_precision) / len(all_precision)) * (sum(all_recall) / len(all_recall)) /
                ((sum(all_precision) / len(all_precision)) + (sum(all_recall) / len(all_recall)) + 1e-10),
                4
            ),
        }


class TrainingDataset:
    """Prepare and manage training datasets."""
    
    def __init__(self):
        self.features = []
        self.labels = []
        self.metadata = {}
    
    def add_sample(self, features: Dict, label: Dict):
        """Add a training sample."""
        self.features.append(features)
        self.labels.append(label)
    
    def split(self, train_ratio: float = 0.8) -> Tuple['TrainingDataset', 'TrainingDataset']:
        """
        Split into training and validation sets.
        
        Args:
            train_ratio: Ratio of data to use for training
            
        Returns:
            Tuple of (train_dataset, val_dataset)
        """
        n = len(self.features)
        split_idx = int(n * train_ratio)
        
        train_ds = TrainingDataset()
        train_ds.features = self.features[:split_idx]
        train_ds.labels = self.labels[:split_idx]
        train_ds.metadata = {**self.metadata, 'split': 'train'}
        
        val_ds = TrainingDataset()
        val_ds.features = self.features[split_idx:]
        val_ds.labels = self.labels[split_idx:]
        val_ds.metadata = {**self.metadata, 'split': 'validation'}
        
        return train_ds, val_ds
    
    def save(self, filepath: Path):
        """Save dataset to disk."""
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump({
                'features': self.features,
                'labels': self.labels,
                'metadata': self.metadata,
            }, f, indent=2)
        logger.info(f"Dataset saved to {filepath}")
    
    @classmethod
    def load(cls, filepath: Path) -> 'TrainingDataset':
        """Load dataset from disk."""
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        dataset = cls()
        dataset.features = data['features']
        dataset.labels = data['labels']
        dataset.metadata = data.get('metadata', {})
        logger.info(f"Dataset loaded from {filepath}")
        return dataset
    
    def __len__(self):
        return len(self.features)
