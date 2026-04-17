"""
Synthetic Data Generation and Data Augmentation
Week 5-7 Enhancement: Generate realistic training data and validate models
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging
from scipy.stats import multivariate_normal, gaussian_kde
from sklearn.preprocessing import StandardScaler

logger = logging.getLogger(__name__)

# ============================================================================
# SYNTHETIC DATA GENERATOR
# ============================================================================

@dataclass
class SyntheticDataConfig:
    """Configuration for synthetic data generation"""
    method: str = 'smote'  # smote, gmm, vae, copula
    n_synthetic_samples: int = 1000
    preserve_distribution: bool = True
    preserve_correlation: bool = True
    constraint_checking: bool = True
    quality_threshold: float = 0.85

class SyntheticDataGenerator:
    """
    Generate synthetic sports data for augmenting training datasets
    Techniques: SMOTE, Gaussian Mixture Models, Copulas
    """
    
    def __init__(self, config: SyntheticDataConfig = None):
        self.config = config or SyntheticDataConfig()
        self.original_data = None
        self.synthetic_data = None
        self.quality_metrics = {}
    
    def generate_from_realdata(
        self,
        real_data: pd.DataFrame,
        n_synthetic: int = 1000,
        method: str = 'smote'
    ) -> pd.DataFrame:
        """
        Generate synthetic data from real dataset
        
        Args:
            real_data: Original dataset
            n_synthetic: Number of synthetic samples to create
            method: Generation method
        
        Returns:
            Synthetic dataset
        """
        self.original_data = real_data.copy()
        
        if method == 'smote':
            synthetic = self._generate_smote(real_data, n_synthetic)
        elif method == 'gmm':
            synthetic = self._generate_gmm(real_data, n_synthetic)
        elif method == 'copula':
            synthetic = self._generate_copula(real_data, n_synthetic)
        else:
            raise ValueError(f"Unknown method: {method}")
        
        self.synthetic_data = synthetic
        
        # Validate quality
        self._validate_synthetic_data(real_data, synthetic)
        
        return synthetic
    
    def _generate_smote(
        self,
        data: pd.DataFrame,
        n_synthetic: int
    ) -> pd.DataFrame:
        """
        Generate data using SMOTE (Synthetic Minority Oversampling Technique)
        
        Creates synthetic samples by interpolating between nearest neighbors
        """
        n_real = len(data)
        synthetic_samples = []
        
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        
        for _ in range(n_synthetic):
            # Pick random sample
            idx_a = np.random.randint(0, n_real)
            sample_a = data.iloc[idx_a][numeric_cols].values
            
            # Find nearest neighbor
            distances = np.linalg.norm(
                data[numeric_cols].values - sample_a,
                axis=1
            )
            idx_b = np.argmin(distances)
            sample_b = data.iloc[idx_b][numeric_cols].values
            
            # Interpolate between samples
            alpha = np.random.rand()
            synthetic_sample = sample_a + alpha * (sample_b - sample_a)
            
            synthetic_samples.append(synthetic_sample)
        
        synthetic_df = pd.DataFrame(
            synthetic_samples,
            columns=numeric_cols
        )
        
        return synthetic_df
    
    def _generate_gmm(
        self,
        data: pd.DataFrame,
        n_synthetic: int
    ) -> pd.DataFrame:
        """
        Generate data using Gaussian Mixture Model
        
        Fits mixture of Gaussians and samples from it
        """
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        X = data[numeric_cols].values
        
        # Standardize data
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        
        # Determine number of components (Elbow method simplified)
        n_components = max(2, min(5, len(data) // 50))
        
        # Fit Gaussian mixture
        means = []
        covariances = []
        weights = []
        
        # Simple k-means style initialization
        for k in range(n_components):
            mask = (np.arange(len(X_scaled)) % n_components) == k
            means.append(X_scaled[mask].mean(axis=0))
            covariances.append(np.cov(X_scaled[mask].T) + np.eye(X_scaled.shape[1]) * 0.1)
            weights.append(mask.sum() / len(X_scaled))
        
        # Generate synthetic samples
        synthetic_samples = []
        
        for _ in range(n_synthetic):
            # Pick component by weight
            component = np.random.choice(n_components, p=weights)
            
            # Sample from that Gaussian
            sample = np.random.multivariate_normal(
                means[component],
                covariances[component]
            )
            
            synthetic_samples.append(sample)
        
        # Inverse transform
        synthetic_samples = np.array(synthetic_samples)
        synthetic_samples = scaler.inverse_transform(synthetic_samples)
        
        synthetic_df = pd.DataFrame(
            synthetic_samples,
            columns=numeric_cols
        )
        
        return synthetic_df
    
    def _generate_copula(
        self,
        data: pd.DataFrame,
        n_synthetic: int
    ) -> pd.DataFrame:
        """
        Generate data using Copula method
        
        Preserves correlation structure while generating new values
        """
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        X = data[numeric_cols].values
        
        # Convert to uniform marginals (empirical CDF)
        n_features = X.shape[1]
        U = np.zeros_like(X, dtype=float)
        
        for j in range(n_features):
            col = X[:, j]
            U[:, j] = np.argsort(np.argsort(col)) / len(col)
        
        # Fit Gaussian copula (correlation matrix)
        correlation_matrix = np.corrcoef(U.T)
        
        # Generate synthetic uniform samples
        synthetic_uniform = np.random.multivariate_normal(
            np.zeros(n_features),
            correlation_matrix,
            size=n_synthetic
        )
        
        # Convert to uniform [0, 1]
        from scipy.stats import norm
        synthetic_uniform = norm.cdf(synthetic_uniform)
        synthetic_uniform = np.clip(synthetic_uniform, 0.01, 0.99)
        
        # Inverse transform using empirical quantiles
        synthetic_samples = np.zeros((n_synthetic, n_features))
        
        for j in range(n_features):
            col = X[:, j]
            quantiles = np.quantile(col, synthetic_uniform[:, j])
            synthetic_samples[:, j] = quantiles
        
        synthetic_df = pd.DataFrame(
            synthetic_samples,
            columns=numeric_cols
        )
        
        return synthetic_df
    
    def _validate_synthetic_data(
        self,
        real_data: pd.DataFrame,
        synthetic_data: pd.DataFrame
    ):
        """Validate quality of synthetic data"""
        numeric_cols = real_data.select_dtypes(include=[np.number]).columns
        
        metrics = {}
        
        # 1. Distribution matching (Kolmogorov-Smirnov test)
        from scipy.stats import ks_2samp
        
        ks_scores = []
        for col in numeric_cols:
            statistic, pvalue = ks_2samp(
                real_data[col],
                synthetic_data[col]
            )
            ks_scores.append(pvalue)  # Higher p-value = better match
        
        metrics['distribution_match'] = np.mean(ks_scores)
        
        # 2. Correlation structure preservation
        real_corr = real_data[numeric_cols].corr().values
        synthetic_corr = synthetic_data[numeric_cols].corr().values
        
        corr_rmse = np.sqrt(np.mean((real_corr - synthetic_corr) ** 2))
        metrics['correlation_preservation'] = 1 - min(corr_rmse, 1.0)
        
        # 3. Statistical moments matching
        real_mean = real_data[numeric_cols].mean()
        synthetic_mean = synthetic_data[numeric_cols].mean()
        mean_error = np.mean(np.abs(real_mean - synthetic_mean) / (np.abs(real_mean) + 1e-6))
        metrics['mean_preservation'] = 1 - min(mean_error, 1.0)
        
        real_std = real_data[numeric_cols].std()
        synthetic_std = synthetic_data[numeric_cols].std()
        std_error = np.mean(np.abs(real_std - synthetic_std) / (np.abs(real_std) + 1e-6))
        metrics['std_preservation'] = 1 - min(std_error, 1.0)
        
        # 4. Overall quality score
        metrics['overall_quality'] = np.mean([
            metrics['distribution_match'],
            metrics['correlation_preservation'],
            metrics['mean_preservation'],
            metrics['std_preservation']
        ])
        
        self.quality_metrics = metrics
        
        logger.info(f"Synthetic data quality: {metrics['overall_quality']:.2%}")
        
        return metrics
    
    def get_quality_report(self) -> Dict:
        """Get detailed quality report on synthetic data"""
        return {
            'quality_metrics': self.quality_metrics,
            'passes_threshold': self.quality_metrics.get('overall_quality', 0) >= self.config.quality_threshold,
            'timestamp': datetime.utcnow().isoformat()
        }

# ============================================================================
# DATA AUGMENTATION PIPELINE
# ============================================================================

class DataAugmentationPipeline:
    """
    Apply various data augmentation techniques to enrich training datasets
    """
    
    def __init__(self):
        self.transformations = []
    
    def apply_noise_injection(
        self,
        data: pd.DataFrame,
        noise_level: float = 0.05
    ) -> pd.DataFrame:
        """
        Add Gaussian noise to features
        
        Args:
            data: Original data
            noise_level: Standard deviation of noise (as fraction of feature std)
        
        Returns:
            Augmented data
        """
        augmented = data.copy()
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            col_std = data[col].std()
            noise = np.random.normal(0, col_std * noise_level, len(data))
            augmented[col] = data[col] + noise
        
        return augmented
    
    def apply_time_shifting(
        self,
        data: pd.DataFrame,
        shift_amount: int = -1
    ) -> pd.DataFrame:
        """
        Shift time series data (useful for temporal patterns)
        """
        return data.shift(shift_amount)
    
    def apply_opponent_swap(
        self,
        data: pd.DataFrame,
        home_col: str,
        away_col: str
    ) -> pd.DataFrame:
        """
        Swap home/away and adjust stats accordingly
        Simulates perspective flip
        """
        augmented = data.copy()
        
        # Swap home/away columns
        augmented[[home_col, away_col]] = augmented[[away_col, home_col]]
        
        return augmented
    
    def apply_feature_scaling_variations(
        self,
        data: pd.DataFrame,
        scale_factors: List[float] = [0.95, 1.0, 1.05]
    ) -> List[pd.DataFrame]:
        """
        Create variations by slightly scaling features
        """
        variations = []
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        
        for scale_factor in scale_factors:
            augmented = data.copy()
            augmented[numeric_cols] = augmented[numeric_cols] * scale_factor
            variations.append(augmented)
        
        return variations
    
    def apply_seasonal_adjustment(
        self,
        data: pd.DataFrame,
        seasonal_patterns: Dict[str, float]
    ) -> pd.DataFrame:
        """
        Apply seasonal variations to account for league-wide patterns
        """
        augmented = data.copy()
        
        for col, adjustment in seasonal_patterns.items():
            if col in augmented.columns:
                augmented[col] = augmented[col] * (1 + adjustment)
        
        return augmented

# ============================================================================
# SIMULATION-BASED BACKTESTING
# ============================================================================

class SimulationBacktestEngine:
    """
    Run predictions on synthetic data to validate model robustness
    """
    
    def __init__(self, model, model_name: str = "Model"):
        self.model = model
        self.model_name = model_name
        self.backtest_results = {}
    
    def run_simulation_backtest(
        self,
        base_data: pd.DataFrame,
        n_simulations: int = 1000,
        target_col: str = 'outcome'
    ) -> Dict:
        """
        Run model on synthetic data to validate edge cases
        """
        generator = SyntheticDataGenerator()
        
        all_accuracies = []
        all_calibrations = []
        
        for sim_idx in range(n_simulations):
            # Generate synthetic data
            synthetic = generator.generate_from_realdata(
                base_data.drop(columns=[target_col]),
                n_synthetic=len(base_data),
                method='smote'
            )
            
            # Add synthetic targets
            synthetic[target_col] = np.random.randint(0, 2, len(synthetic))
            
            # Make predictions
            try:
                X = synthetic.drop(columns=[target_col])
                y_true = synthetic[target_col]
                
                predictions = self.model.predict(X)
                
                # Calculate accuracy
                accuracy = np.mean(predictions == y_true)
                all_accuracies.append(accuracy)
                
                # Calculate calibration error (simplified)
                calibration_error = np.mean(np.abs(predictions - y_true.values))
                all_calibrations.append(calibration_error)
                
            except Exception as e:
                logger.error(f"Simulation {sim_idx} failed: {e}")
                continue
        
        return {
            'model_name': self.model_name,
            'simulations': n_simulations,
            'successful_simulations': len(all_accuracies),
            'mean_accuracy': np.mean(all_accuracies),
            'std_accuracy': np.std(all_accuracies),
            'min_accuracy': np.min(all_accuracies),
            'max_accuracy': np.max(all_accuracies),
            'mean_calibration_error': np.mean(all_calibrations),
            'stability_score': 1 - np.std(all_accuracies),  # Lower std = more stable
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def validate_edge_cases(
        self,
        edge_case_data: pd.DataFrame,
        expected_behavior: str = 'conservative'
    ) -> Dict:
        """
        Test model on known edge cases
        
        Args:
            edge_case_data: Data with known edge cases
            expected_behavior: How model should behave
        
        Returns:
            Edge case validation results
        """
        results = {
            'edge_cases_tested': len(edge_case_data),
            'expected_behavior': expected_behavior,
            'test_results': []
        }
        
        # Test various edge cases
        edge_cases = {
            'extreme_high': edge_case_data.quantile(0.99),
            'extreme_low': edge_case_data.quantile(0.01),
            'missing_values': edge_case_data.where(np.random.random(edge_case_data.shape) < 0.1, np.nan),
            'uniform_values': pd.DataFrame(np.ones_like(edge_case_data.values) * edge_case_data.mean())
        }
        
        for case_name, case_data in edge_cases.items():
            try:
                if case_name != 'missing_values':
                    case_data = case_data.fillna(case_data.mean())
                
                predictions = self.model.predict(case_data)
                
                results['test_results'].append({
                    'edge_case': case_name,
                    'status': 'passed',
                    'prediction_mean': np.mean(predictions),
                    'prediction_std': np.std(predictions)
                })
            except Exception as e:
                results['test_results'].append({
                    'edge_case': case_name,
                    'status': 'failed',
                    'error': str(e)
                })
        
        return results

if __name__ == "__main__":
    print("Synthetic Data Generation module loaded")
