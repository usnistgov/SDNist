"""
Helper module for Predictive Utility feature combinations and analysis.

This module provides functions for creating meaningful feature combinations
from startup capital (SC) features.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Union
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score, classification_report, confusion_matrix
from sklearn.exceptions import ConvergenceWarning
import warnings

class FeatureCombiner:
    """
    Creates combinations of startup capital features.
    """
    
    @staticmethod
    def create_self_funded_vs_external(df: pd.DataFrame) -> pd.Series:
        """
        Create binary classification: Self-funded vs External-funded.
        
        Args:
            df: DataFrame containing SC features
            
        Returns:
            Series with 'self_funded' or 'external_funded' values
        """
        result = pd.Series(['external_funded'] * len(df), index=df.index)
        
        # Personal resources indicators
        has_personal_savings = df.get('SCSAVINGS', 0) == 1
        has_personal_assets = df.get('SCASSETS', 0) == 1
        has_home_equity = df.get('SCEQUITY', 0) == 1
        
        # External funding indicators
        external_sources = [
            'SCGOVTLOAN', 'SCGOVTGUAR', 'SCBANKLOAN', 'SCFAMLOAN', 
            'SCCREDIT', 'SCVENTURE', 'SCGRANT'
        ]
        has_external = df[external_sources].eq(1).any(axis=1)
        
        # Self-funded: has personal resources AND no external funding
        has_personal = has_personal_savings | has_personal_assets | has_home_equity
        is_self_funded = has_personal & ~has_external
        
        result[is_self_funded] = 'self_funded'
        
        return result
    
    @staticmethod
    def create_funding_risk_profile(df: pd.DataFrame) -> pd.Series:
        """
        Create funding risk profile classification.
        
        Args:
            df: DataFrame containing SC features
            
        Returns:
            Series with risk profile categories
        """
        result = pd.Series(['medium_risk'] * len(df), index=df.index)
        
        # Personal resources
        personal_sources = ['SCSAVINGS', 'SCASSETS', 'SCEQUITY']
        has_personal = df[personal_sources].eq(1).any(axis=1)

        # High-risk sources
        high_risk_sources = ['SCCREDIT', 'SCBANKLOAN', 'SCGOVTLOAN', 'SCGOVTGUAR']
        has_high_risk = df[high_risk_sources].eq(1).any(axis=1)
        
        # Very high-risk sources
        has_venture = df.get('SCVENTURE', 0) == 1
        
        # Classification logic
        # Low risk: Only personal resources
        only_personal = has_personal & ~df[['SCFAMLOAN', 'SCCREDIT', 'SCBANKLOAN', 'SCGOVTLOAN', 'SCGOVTGUAR', 'SCVENTURE', 'SCGRANT']].eq(1).any(axis=1)
        result[only_personal] = 'low_risk'
        
        # Very high risk: Has venture capital
        result[has_venture] = 'very_high_risk'
        
        # High risk: Has high-risk sources but no VC
        has_high_no_vc = has_high_risk & ~has_venture
        result[has_high_no_vc] = 'high_risk'
        
        # Medium risk: Personal + family or just family (default for others)
        return result
    
    @staticmethod
    def create_government_support(df: pd.DataFrame) -> pd.Series:
        """
        Create government support indicator.
        
        Args:
            df: DataFrame containing SC features
            
        Returns:
            Series with government support categories
        """
        result = pd.Series(['no_support'] * len(df), index=df.index)
        
        has_govt_loan = (df.get('SCGOVTLOAN', 0) == 1) | (df.get('SCGOVTGUAR', 0) == 1)
        has_grant = df.get('SCGRANT', 0) == 1
        
        result[has_govt_loan] = 'loan_support'
        result[has_grant] = 'grant_support'  # Grant takes priority over loan
        
        return result
    
    @staticmethod
    def create_funding_complexity(df: pd.DataFrame) -> pd.Series:
        """
        Create funding complexity score based on number of sources.
        
        Args:
            df: DataFrame containing SC features
            
        Returns:
            Series with complexity categories
        """
        funding_sources = [
            'SCSAVINGS', 'SCASSETS', 'SCEQUITY', 'SCCREDIT',
            'SCGOVTLOAN', 'SCGOVTGUAR', 'SCBANKLOAN', 'SCFAMLOAN',
            'SCVENTURE', 'SCGRANT', 'SCOTHER'
        ]
        
        # Count sources where value is 1 (YES)
        source_count = df[funding_sources].eq(1).sum(axis=1)
        
        result = pd.Series(['simple'] * len(df), index=df.index)
        result[source_count.between(2, 3)] = 'moderate'
        result[source_count >= 4] = 'complex'
        
        return result
    
    @staticmethod
    def create_bootstrap_vs_institutional(df: pd.DataFrame) -> pd.Series:
        """
        Create bootstrap vs institutional funding classification.
        
        Args:
            df: DataFrame containing SC features
            
        Returns:
            Series with funding approach categories
        """
        result = pd.Series(['mixed'] * len(df), index=df.index)
        
        # Bootstrap sources
        bootstrap_sources = ['SCSAVINGS', 'SCASSETS', 'SCEQUITY', 'SCFAMLOAN']
        has_bootstrap = df[bootstrap_sources].eq(1).any(axis=1)
        
        # Institutional sources
        institutional_sources = ['SCBANKLOAN', 'SCGOVTLOAN', 'SCGOVTGUAR', 'SCVENTURE']
        has_institutional = df[institutional_sources].eq(1).any(axis=1)
        
        # Pure bootstrap: only bootstrap sources
        only_bootstrap = has_bootstrap & ~has_institutional
        result[only_bootstrap] = 'bootstrap'
        
        # Pure institutional: only institutional sources
        only_institutional = has_institutional & ~has_bootstrap
        result[only_institutional] = 'institutional'
        
        return result
    
    @staticmethod
    def create_formal_vs_informal(df: pd.DataFrame) -> pd.Series:
        """
        Create formal vs informal funding classification.
        
        Args:
            df: DataFrame containing SC features
            
        Returns:
            Series with formal/informal categories
        """
        # Formal sources
        formal_sources = ['SCBANKLOAN', 'SCGOVTLOAN', 'SCGOVTGUAR', 'SCVENTURE', 'SCGRANT']
        has_formal = df[formal_sources].eq(1).any(axis=1)
        
        result = pd.Series(['informal'] * len(df), index=df.index)
        result[has_formal] = 'formal'
        
        return result
    
    @staticmethod
    def create_original_loan_feature(df: pd.DataFrame) -> pd.Series:
        """
        Create the original combined loan feature (legacy implementation).
        
        Args:
            df: DataFrame containing SC features
            
        Returns:
            Series with original loan categories
        """
        loan_feature = pd.Series(['no_loan'] * len(df), index=df.index)
        
        # Priority order: govt_loan > govt_guaranteed > bank_loan > family_loan
        for idx in df.index:
            if df.loc[idx, 'SCGOVTLOAN'] == 1:
                loan_feature.loc[idx] = 'govt_loan'
            elif df.loc[idx, 'SCGOVTGUAR'] == 1:
                loan_feature.loc[idx] = 'govt_guaranteed_bank_loan'
            elif df.loc[idx, 'SCBANKLOAN'] == 1:
                loan_feature.loc[idx] = 'bank_loan'
            elif df.loc[idx, 'SCFAMLOAN'] == 1:
                loan_feature.loc[idx] = 'family_loan'
            # If all are 0, 2, or not reported, it remains 'no_loan'
        
        return loan_feature
    
    @staticmethod
    def create_credit_dependency(df: pd.DataFrame) -> pd.Series:
        """
        Create credit dependency indicator.

        Args:
            df: DataFrame containing SC features

        Returns:
            Series with credit dependency categories
        """
        has_credit_risk = (df.get('SCCREDIT', 0) == 1) | (df.get('SCEQUITY', 0) == 1)

        result = pd.Series(['no_credit_risk'] * len(df), index=df.index)
        result[has_credit_risk] = 'has_credit_risk'

        return result

    @staticmethod
    def create_scgovtloan_individual(df: pd.DataFrame) -> pd.Series:
        """
        Create feature using only SCGOVTLOAN column as target.

        Args:
            df: DataFrame containing SC features

        Returns:
            Series with SCGOVTLOAN values
        """
        return df['SCGOVTLOAN'].copy()

    @staticmethod
    def create_scgovtguar_individual(df: pd.DataFrame) -> pd.Series:
        """
        Create feature using only SCGOVTGUAR column as target.

        Args:
            df: DataFrame containing SC features

        Returns:
            Series with SCGOVTGUAR values
        """
        return df['SCGOVTGUAR'].copy()

    @staticmethod
    def create_scbankloan_individual(df: pd.DataFrame) -> pd.Series:
        """
        Create feature using only SCBANKLOAN column as target.

        Args:
            df: DataFrame containing SC features

        Returns:
            Series with SCBANKLOAN values
        """
        return df['SCBANKLOAN'].copy()

    @staticmethod
    def create_scfamloan_individual(df: pd.DataFrame) -> pd.Series:
        """
        Create feature using only SCFAMLOAN column as target.

        Args:
            df: DataFrame containing SC features

        Returns:
            Series with SCFAMLOAN values
        """
        return df['SCFAMLOAN'].copy()

    @staticmethod
    def create_scgrant_individual(df: pd.DataFrame) -> pd.Series:
        """
        Create feature using only SCGRANT column as target.

        Args:
            df: DataFrame containing SC features

        Returns:
            Series with SCGRANT values
        """
        return df['SCGRANT'].copy()


class PredictiveAnalyzer:
    """
    Performs predictive analysis on combined features.
    """
    
    def __init__(self):
        self.results = {}
    
    def analyze_feature_combination(
        self,
        X_target: pd.DataFrame,
        X_synthetic: pd.DataFrame,
        y_target: pd.Series,
        y_synthetic: pd.Series,
        feature_name: str,
        preprocessor_target=None,
        preprocessor_synthetic=None,
        model_params: Dict = None,
        subgroup_name: str = None
    ) -> Dict:
        """
        Perform predictive analysis on a feature combination.
        
        Args:
            X_target: Target dataset features
            X_synthetic: Synthetic dataset features  
            y_target: Target labels
            y_synthetic: Synthetic labels
            feature_name: Name of the combined feature
            preprocessor_target: Preprocessor for target data
            model_params: LogisticRegression parameters
            subgroup_name: To compute regression at sub group level
        Returns:
            Dictionary containing analysis results
        """
        from sklearn.model_selection import train_test_split
        from sklearn.linear_model import LogisticRegression
        
        if model_params is None:
            raise ValueError("model_params must be provided")
        
        # if subgroup_name:
        #     print(f'\nProcessing {feature_name} analysis for {subgroup_name}...')
        # else:
        #     print(f'\nProcessing {feature_name} analysis...')
        
        # Analyze class distribution
        # if subgroup_name:
        #     print(f"\n=== {feature_name} Class Distribution ({subgroup_name}) ===")
        # else:
        #     print(f"\n=== {feature_name} Class Distribution ===")
        target_dist = y_target.value_counts()
        
        # Split data
        X_t_train, X_t_test, y_t_train, y_t_test = train_test_split(
            X_target, y_target, test_size=0.4, random_state=42, stratify=y_target
        )
        
        X_s_train, X_s_test, y_s_train, y_s_test = train_test_split(
            X_synthetic, y_synthetic, test_size=0.4, random_state=42, stratify=y_synthetic
        )
        
        # Apply preprocessing - use same fitted preprocessor for both datasets
        if preprocessor_target is not None:
            try:
                # Fit on target training data
                X_t_train_processed = preprocessor_target.fit_transform(X_t_train)
                X_t_test_processed = preprocessor_target.transform(X_t_test)
                
                # Use the same fitted preprocessor for synthetic data (no fitting)
                X_s_train_processed = preprocessor_target.transform(X_s_train)
                X_s_test_processed = preprocessor_target.transform(X_s_test)
            except Exception as e:
                # print(f"Error in preprocessing for {feature_name}: {e}")
                X_t_train_processed = X_t_train.values
                X_t_test_processed = X_t_test.values
                X_s_train_processed = X_s_train.values
                X_s_test_processed = X_s_test.values
        else:
            X_t_train_processed = X_t_train.values
            X_t_test_processed = X_t_test.values
            X_s_train_processed = X_s_train.values
            X_s_test_processed = X_s_test.values

        # Train models
        model_target = LogisticRegression(**model_params)
        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=ConvergenceWarning,
                                    message=r".*lbfgs failed to converge*")
            model_target.fit(X_t_train_processed, y_t_train)
        
        model_synthetic = LogisticRegression(**model_params)

        with warnings.catch_warnings():
            warnings.filterwarnings("ignore", category=ConvergenceWarning,
                                    message=r".*lbfgs failed to converge*")
            model_synthetic.fit(X_s_train_processed, y_s_train)
        
        # Get predictions
        pred_target_on_target = model_target.predict(X_t_test_processed)
        pred_synthetic_on_target = model_synthetic.predict(X_t_test_processed)
        
        # Calculate balanced accuracy only
        bal_acc_target = accuracy_score(y_t_test, pred_target_on_target)
        bal_acc_synthetic = accuracy_score(y_t_test, pred_synthetic_on_target)
        
        # Calculate confusion matrix components for visualization
        cm_target = confusion_matrix(y_t_test, pred_target_on_target)
        cm_synthetic = confusion_matrix(y_t_test, pred_synthetic_on_target)
        
        # Convert numpy/pandas types to native Python types for JSON serialization
        def convert_to_native(obj):
            """Convert numpy/pandas types to native Python types."""
            if hasattr(obj, 'item'):  # numpy scalars
                return obj.item()
            elif hasattr(obj, 'tolist'):  # numpy arrays
                return obj.tolist()
            elif isinstance(obj, (pd.Series, pd.DataFrame)):
                return obj.tolist()
            elif isinstance(obj, dict):
                return {k: convert_to_native(v) for k, v in obj.items()}
            else:
                return obj
        
        # Store results with type conversion
        results = {
            'feature_name': str(feature_name),
            'subgroup_name': subgroup_name,
            'class_distribution': {str(k): int(v) for k, v in target_dist.items()},
            'actual_target': y_t_test,  # Keep for visualization, not in report
            'pred_target_on_target': pred_target_on_target,  # Keep for visualization, not in report
            'pred_synthetic_on_target': pred_synthetic_on_target,  # Keep for visualization, not in report
            'balanced_accuracy_target': float(bal_acc_target),
            'balanced_accuracy_synthetic': float(bal_acc_synthetic),
            'balanced_accuracy_degradation': float(bal_acc_target - bal_acc_synthetic),
            'confusion_matrix_target': cm_target.tolist(),
            'confusion_matrix_synthetic': cm_synthetic.tolist()
        }
        
        self.results[feature_name] = results
        return results
    
    def print_summary(self, feature_name: str):
        """Print summary of analysis results for a feature."""
        if feature_name not in self.results:
            print(f"No results found for {feature_name}")
            return
        
        r = self.results[feature_name]
        print(f"\n=== {feature_name} Results ===")
        print(f"Balanced Accuracy: Target={r['balanced_accuracy_target']:.3f}, Synthetic={r['balanced_accuracy_synthetic']:.3f}, Degradation={r['balanced_accuracy_degradation']:.3f}")