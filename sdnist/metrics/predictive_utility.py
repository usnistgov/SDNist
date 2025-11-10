import os
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.metrics import accuracy_score, f1_score
from sklearn.base import clone
import matplotlib.pyplot as plt

from sdnist.utils import *
import sdnist.strs as strs
from sdnist.metrics.predictive_utility_helpers import FeatureCombiner, PredictiveAnalyzer

class PredictiveUtility:
    NAME = 'Predictive Utility'
    
    # SC features to use as targets
    SC_TARGETS = [
        'SCSAVINGS', 'SCASSETS',
        'SCEQUITY', 'SCCREDIT',
        'SCGOVTLOAN', 'SCGOVTGUAR', 'SCBANKLOAN', 'SCFAMLOAN',
        'SCVENTURE', 'SCGRANT', 'SCOTHER', 'SCDONTKNOW',
        'SCNONENEEDED', 'SCNOTREPORTED',
        'SCAMOUNT'
    ]
    
    def __init__(self, target, synthetic, output_directory, feature_types=None, data_dict=None):
        self.target = target
        self.synthetic = synthetic
        self.o_dir = output_directory
        self.o_path = Path(self.o_dir, 'predictive_utility')
        self.feature_types = feature_types or {}
        self.data_dict = data_dict or {}
        
        # Results storage
        self.results = {}
        self.loan_results = {}  # Store loan analysis results separately
        self.combined_feature_results = {}  # Store results for all combined features
        self.report_data = {}
        
        # Model parameters
        self.model_params = {
            'max_iter': 100,
            'solver': 'lbfgs',
            'class_weight': 'balanced',
            'n_jobs': -1,
            'random_state': 42
        }
        
        # Initialize helper classes
        self.feature_combiner = FeatureCombiner()
        self.analyzer = PredictiveAnalyzer()
        
        self._setup()
    
    def compute_score(self):
        """Main computation method - runs all analyses"""
        
        # Section 1: Individual SC features analysis
        # self._analyze_individual_sc_features()
        
        # Section 2: Combined feature analyses (includes original loan feature)
        self._analyze_combined_features()
        
        # Section 3: Create visualizations
        # self._create_accuracy_grid()
        # self._create_plot()
        self._create_summary_degradation_grid()
        self._create_combined_feature_visualizations()
        
        # Section 4: Prepare report data
        self._prepare_report_data()
        
        return self.results
    
    def _get_feature_description(self, feature):
        """Get feature description from data dictionary"""
        if feature in self.data_dict and 'description' in self.data_dict[feature]:
            return self.data_dict[feature]['description']
        else:
            # Return a default description if not available
            return f"Startup Capital: {feature}"
    
    def _setup(self):
        if not self.o_dir.exists():
            raise Exception(f'Path {self.o_dir} does not exist')
        if not self.o_path.exists():
            os.mkdir(self.o_path)
    
    def _create_preprocessor(self, feature_columns):
        """Create preprocessor for selective scaling and one-hot encoding"""
        continuous_features = []
        categorical_features = []
        
        for feature in feature_columns:
            feature_type = self.feature_types.get(feature, strs.CATEGORICAL)
            if feature_type == strs.CONTINUOUS:
                continuous_features.append(feature)
            else:
                categorical_features.append(feature)
        
        transformers = []
        
        if continuous_features:
            transformers.append(('scaler', StandardScaler(), continuous_features))
        
        if categorical_features:
            transformers.append(('onehot', OneHotEncoder(sparse_output=False, handle_unknown='ignore'), categorical_features))

        if not transformers:
            return None
        
        return ColumnTransformer(transformers=transformers, remainder='passthrough')
    
    def _analyze_combined_features(self):
        """Analyze all combined feature combinations using the helper module."""
        # print('Processing combined feature analyses...')
        
        # Get X features (all non-SC columns)
        X_columns = [col for col in self.target.columns 
                    if col not in self.SC_TARGETS]
        
        X_target = self.target[X_columns]
        X_synthetic = self.synthetic[X_columns]
        
        # Define feature combinations to analyze
        feature_combinations = {
            'SCGOVTLOAN': self.feature_combiner.create_scgovtloan_individual,
            'SCGOVTGUAR': self.feature_combiner.create_scgovtguar_individual,
            'SCBANKLOAN': self.feature_combiner.create_scbankloan_individual,
            'SCFAMLOAN': self.feature_combiner.create_scfamloan_individual,
            'SCGRANT': self.feature_combiner.create_scgrant_individual,
            'Combined_Loan_Feature': self.feature_combiner.create_original_loan_feature,
            'Self_Funded_vs_External': self.feature_combiner.create_self_funded_vs_external,
            'Funding_Risk_Profile': self.feature_combiner.create_funding_risk_profile,
            'Government_Support': self.feature_combiner.create_government_support,
            'Funding_Complexity': self.feature_combiner.create_funding_complexity,
            'Bootstrap_vs_Institutional': self.feature_combiner.create_bootstrap_vs_institutional,
            'Formal_vs_Informal': self.feature_combiner.create_formal_vs_informal,
            'Credit_Dependency': self.feature_combiner.create_credit_dependency
        }
        print('--Predictive Utility')
        # Analyze each combination for overall and by SEX1 subgroups
        for feature_name, combiner_func in feature_combinations.items():
            print(f'----Processing: {feature_name}')
            try:
                # Overall analysis (all data)
                y_target_combined = combiner_func(self.target)
                y_synthetic_combined = combiner_func(self.synthetic)
                
                # Create fresh preprocessors for each feature combination
                base_preprocessor = self._create_preprocessor(X_columns)
                synth_preprocessor = self._create_preprocessor(X_columns)
                preprocessor_target = clone(base_preprocessor) if base_preprocessor else None

                # Run overall analysis using shared model parameters
                results = self.analyzer.analyze_feature_combination(
                    X_target=X_target,
                    X_synthetic=X_synthetic,
                    y_target=y_target_combined,
                    y_synthetic=y_synthetic_combined,
                    feature_name=feature_name,
                    preprocessor_target=preprocessor_target,
                    preprocessor_synthetic=synth_preprocessor,
                    model_params=self.model_params,
                    subgroup_name=None
                )
                
                self.combined_feature_results[feature_name] = results
                # self.analyzer.print_summary(feature_name)
                
                # Analyze by demographic subgroups
                self._analyze_demographic_subgroups(feature_name, combiner_func, X_target, X_synthetic, X_columns)
                
            except Exception as e:
                print(f"Error analyzing {feature_name}: {e}")
                continue
    
    def _analyze_demographic_subgroups(self, feature_name, combiner_func, X_target, X_synthetic, X_columns):
        """Analyze subgroups by SEX1 and AGE1."""
        
        # SEX1 subgroup analysis
        if 'SEX1' in self.target.columns and 'SEX1' in self.synthetic.columns:
            sex_values = self.target['SEX1'].unique()
            
            for sex_value in sex_values:
                try:
                    self._run_subgroup_analysis(
                        feature_name, combiner_func, X_target, X_synthetic, X_columns,
                        'SEX1', sex_value
                    )
                except Exception as e:
                    print(f"Error analyzing {feature_name} for SEX1={sex_value}: {e}")
                    continue
        
        # AGE1 subgroup analysis
        if 'AGE1' in self.target.columns and 'AGE1' in self.synthetic.columns:
            age_values = self.target['AGE1'].unique()
            
            for age_value in age_values:
                try:
                    self._run_subgroup_analysis(
                        feature_name, combiner_func, X_target, X_synthetic, X_columns,
                        'AGE1', age_value
                    )
                except Exception as e:
                    print(f"Error analyzing {feature_name} for AGE1={age_value}: {e}")
                    continue
    
    def _run_subgroup_analysis(self, feature_name, combiner_func, X_target, X_synthetic, X_columns, 
                              demographic_col, demographic_value):
        """Run analysis for a specific demographic subgroup."""
        # Filter data by demographic column
        target_mask = self.target[demographic_col] == demographic_value
        synthetic_mask = self.synthetic[demographic_col] == demographic_value
        
        # Get subgroup data
        target_subgroup = self.target[target_mask]
        synthetic_subgroup = self.synthetic[synthetic_mask]
        
        # Skip if subgroup too small
        if len(target_subgroup) < 100 or len(synthetic_subgroup) < 100:
            print(f"Skipping {feature_name} for {demographic_col}={demographic_value}: insufficient data")
            return
        
        # Create combined features for subgroup
        y_target_subgroup = combiner_func(target_subgroup)
        y_synthetic_subgroup = combiner_func(synthetic_subgroup)
        
        # Get X data for subgroup
        X_target_subgroup = X_target[target_mask]
        X_synthetic_subgroup = X_synthetic[synthetic_mask]
        
        # Create fresh preprocessors for subgroup
        base_preprocessor_sub = self._create_preprocessor(X_columns)
        synth_preprocessor_sub = self._create_preprocessor(X_columns)
        preprocessor_target_sub = clone(base_preprocessor_sub) if base_preprocessor_sub else None
        
        # Run subgroup analysis
        subgroup_name = f"{demographic_col}={demographic_value}"
        results_subgroup = self.analyzer.analyze_feature_combination(
            X_target=X_target_subgroup,
            X_synthetic=X_synthetic_subgroup,
            y_target=y_target_subgroup,
            y_synthetic=y_synthetic_subgroup,
            feature_name=feature_name,
            preprocessor_target=preprocessor_target_sub,
            preprocessor_synthetic=synth_preprocessor_sub,
            model_params=self.model_params,
            subgroup_name=subgroup_name
        )
        
        # Store subgroup results with special key
        subgroup_key = f"{feature_name}_{demographic_col}_{demographic_value}"
        self.combined_feature_results[subgroup_key] = results_subgroup
        # self.analyzer.print_summary(feature_name)


    def _analyze_individual_sc_features(self):
        """Analyze individual SC features using logistic regression"""
        # Get predictor columns (all non-SC columns)
        X_columns = [col for col in self.target.columns 
                    if col not in self.SC_TARGETS]
        
        # Get X features once for all models
        X_target = self.target[X_columns]
        X_synthetic = self.synthetic[X_columns]
        
        # Create preprocessors once
        preprocessor_target = self._create_preprocessor(X_columns)
        preprocessor_synthetic = self._create_preprocessor(X_columns)
        
        # Process each SC target
        for sc_target in self.SC_TARGETS:
            if sc_target not in self.target.columns:
                continue
            
            # Get target variables
            y_target = self.target[sc_target]
            y_synthetic = self.synthetic[sc_target]
            
            # Split target data (X and y together)
            X_t_train, X_t_test, y_t_train, y_t_test = train_test_split(
                X_target, y_target, test_size=0.4, random_state=42
            )
            
            # Split synthetic data (X and y together)
            X_s_train, X_s_test, y_s_train, y_s_test = train_test_split(
                X_synthetic, y_synthetic, test_size=0.4, random_state=42
            )
            
            # Apply preprocessing for each split
            if preprocessor_target is not None:
                X_t_train_processed = preprocessor_target.fit_transform(X_t_train)
                X_t_test_processed = preprocessor_target.transform(X_t_test)
                
                X_s_train_processed = preprocessor_synthetic.fit_transform(X_s_train)
                X_s_test_processed = preprocessor_synthetic.transform(X_s_test)
            else:
                # No preprocessing needed (all features same type or no transformers)
                X_t_train_processed = X_t_train.values
                X_t_test_processed = X_t_test.values
                X_s_train_processed = X_s_train.values
                X_s_test_processed = X_s_test.values

            # Use shared model parameters
            hyper_params = self.model_params.copy()
            # Train models
            model_target = LogisticRegression(**hyper_params)
            model_target.fit(X_t_train_processed, y_t_train)
            
            model_synthetic = LogisticRegression(**hyper_params)
            model_synthetic.fit(X_s_train_processed, y_s_train)
            
            # Get predictions on their respective test sets
            pred_target_on_target = model_target.predict(X_t_test_processed)
            pred_synthetic_on_synthetic = model_synthetic.predict(X_s_test_processed)
            
            # Also get cross predictions for better comparison
            pred_synthetic_on_target = model_synthetic.predict(X_t_test_processed)
            
            # Calculate metrics - both models evaluated on target test set
            acc_target = accuracy_score(y_t_test, pred_target_on_target)
            acc_synthetic_on_target = accuracy_score(y_t_test, pred_synthetic_on_target)
            
            # Store results
            self.results[sc_target] = {
                'actual_target': y_t_test,
                'pred_target_on_target': pred_target_on_target,
                'pred_synthetic_on_target': pred_synthetic_on_target,  # Synthetic model on target test
                'acc_target': acc_target,
                'acc_synthetic_on_target': acc_synthetic_on_target,
                'degradation': acc_target - acc_synthetic_on_target  # Compare on same test set
            }
    
    def _create_accuracy_grid(self):
        """Create accuracy grid chart with target features on y-axis and accuracy comparisons on x-axis"""
        if not self.results:
            return
        
        # Prepare data for grid
        features = list(self.results.keys())
        n_features = len(features)
        
        # Create accuracy matrix: [target_acc, deid_acc, abs_diff]
        accuracy_matrix = np.zeros((n_features, 3))
        
        for i, feature in enumerate(features):
            target_acc = self.results[feature]['acc_target']
            deid_acc = self.results[feature]['acc_synthetic_on_target']
            abs_diff = abs(target_acc - deid_acc)
            
            accuracy_matrix[i, 0] = target_acc
            accuracy_matrix[i, 1] = deid_acc
            accuracy_matrix[i, 2] = abs_diff
        
        # Create figure with subplots for different colorbars
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8, max(3, n_features * 0.5)), gridspec_kw={'width_ratios': [2, 1]})
        
        # First subplot: Target and Deid accuracies
        acc_grid = accuracy_matrix[:, :2]
        im1 = ax1.imshow(acc_grid, cmap='Blues', aspect='auto', vmin=0, vmax=1)
        
        # Set ticks and labels for first subplot
        ax1.set_xticks([0, 1])
        ax1.set_xticklabels(['Target', 'Deid'])
        ax1.set_yticks(range(n_features))
        ax1.set_yticklabels(features)
        ax1.set_title('Model Accuracies', fontsize=12)
        
        # Add text annotations for accuracies
        for i in range(n_features):
            for j in range(2):
                text = f'{acc_grid[i, j]:.3f}'
                ax1.text(j, i, text, ha='center', va='center', fontsize=9, 
                        color='white' if acc_grid[i, j] > 0.5 else 'black')
        
        # Add colorbar for first subplot
        cbar1 = plt.colorbar(im1, ax=ax1, shrink=0.8)
        cbar1.set_label('Accuracy', rotation=270, labelpad=15)
        
        # Second subplot: Absolute differences
        diff_grid = accuracy_matrix[:, 2:3]
        im2 = ax2.imshow(diff_grid, cmap='Reds', aspect='auto', vmin=0, vmax=max(0.1, np.max(diff_grid)))
        
        # Set ticks and labels for second subplot
        ax2.set_xticks([0])
        ax2.set_xticklabels(['Diff'])
        ax2.set_yticks(range(n_features))
        ax2.set_yticklabels([])  # No labels since they're on the left subplot
        ax2.set_title('Absolute Difference', fontsize=12)
        
        # Add text annotations for differences
        for i in range(n_features):
            text = f'{diff_grid[i, 0]:.3f}'
            ax2.text(0, i, text, ha='center', va='center', fontsize=9,
                    color='white' if diff_grid[i, 0] > 0.05 else 'black')
        
        # Add colorbar for second subplot
        cbar2 = plt.colorbar(im2, ax=ax2, shrink=0.8)
        cbar2.set_label('|Target - Deid|', rotation=270, labelpad=15)
        
        # Overall title and layout
        fig.suptitle('Target and Deid Models Accuracies', fontsize=14)
        plt.tight_layout()
        
        # Save the plot
        grid_path = Path(self.o_path, 'predictive_utility_accuracy_grid.png')
        fig.savefig(grid_path, dpi=100, bbox_inches='tight')
        plt.close(fig)
        
        return grid_path
    
    def _create_plot(self):
        # Calculate grid dimensions for combined plot
        n_targets = len(self.results)
        n_cols = 2  # 2 columns: counts and percentage difference
        n_rows = n_targets
        
        # Create combined plot with 2 columns per target (extra height for headers)
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(12, n_rows * 3.5))
        if n_targets == 1:
            axes = axes.reshape(1, -1)  # Ensure 2D array for single target
        
        for idx, (sc_target, data) in enumerate(self.results.items()):
            # Add feature header above the chart pair
            feature_desc = self._get_feature_description(sc_target)
            avl_figh = 0.973
            h_per_row = avl_figh / n_rows
            # Calculate y position for header - position above each row of subplots
            header_y = avl_figh - (idx * h_per_row)
            fig.text(0.05, header_y, f"{sc_target}: {feature_desc}",
                    ha='left', va='top', fontsize=11, fontweight='bold',
                    transform=fig.transFigure)
            
            # Column 1: Distribution comparison
            ax1 = axes[idx, 0]
            
            # Compare on target test set
            actual_target = data['actual_target']
            pred_target_model = data['pred_target_on_target']
            pred_deid_model = data['pred_synthetic_on_target']  # Both models on same test set!
            
            # Get unique labels
            labels = sorted(set(actual_target) | set(pred_target_model) | set(pred_deid_model))
            
            # Count occurrences - all on target test set
            actual_counts = [np.sum(actual_target == label) for label in labels]
            target_model_counts = [np.sum(pred_target_model == label) for label in labels]
            deid_model_counts = [np.sum(pred_deid_model == label) for label in labels]
            
            # Create bars for distribution comparison
            x = np.arange(len(labels))
            width = 0.25
            
            ax1.bar(x - width, actual_counts, width, label='Actual', color='#ff9500', alpha=0.8)
            ax1.bar(x, target_model_counts, width, label='Target Model', color='#5373d8', alpha=0.8)
            ax1.bar(x + width, deid_model_counts, width, label='Deidentified Model', color='#4eb07a', alpha=0.8)
            
            ax1.set_xlabel('Label')
            ax1.set_ylabel('Count')
            ax1.set_title(f'{sc_target} - Counts\nTar Acc={data["acc_target"]:.3f}, Deid Acc={data["acc_synthetic_on_target"]:.3f}', fontsize=10)
            ax1.set_xticks(x)
            ax1.set_xticklabels([str(l) for l in labels])
            ax1.legend(fontsize=8, framealpha=0.7)
            ax1.grid(axis='y', alpha=0.3)
            
            # Column 2: Percentage differences with 3 bars per label
            ax2 = axes[idx, 1]
            
            # Calculate three different percentage differences
            actual_target_diffs = []  # (actual - target) / actual * 100
            actual_deid_diffs = []  # (actual - deidentified) / actual * 100
            target_deid_diffs = []  # (target - deidentified) / actual * 100
            
            for i, label in enumerate(labels):
                actual_count = actual_counts[i]
                target_count = target_model_counts[i]
                deid_count = deid_model_counts[i]
                
                if actual_count > 0:
                    actual_target_diff = ((actual_count - target_count) / actual_count) * 100
                    actual_deid_diff = ((actual_count - deid_count) / actual_count) * 100
                    target_deid_diff = ((target_count - deid_count) / actual_count) * 100
                else:
                    # If actual count is 0, use simple differences
                    actual_target_diff = -target_count * 100 if target_count > 0 else 0
                    actual_deid_diff = -deid_count * 100 if deid_count > 0 else 0
                    target_deid_diff = (target_count - deid_count) * 100 if (target_count + deid_count) > 0 else 0
                
                actual_target_diffs.append(actual_target_diff)
                actual_deid_diffs.append(actual_deid_diff)
                target_deid_diffs.append(target_deid_diff)
            
            # Create bars for percentage differences - 3 bars per label
            width = 0.25
            ax2.bar(x - width, actual_target_diffs, width, label='Act - Tar', color='#5373d8', alpha=0.8)
            ax2.bar(x, actual_deid_diffs, width, label='Act - Deid', color='#4eb07a', alpha=0.8)
            ax2.bar(x + width, target_deid_diffs, width, label='Tar - Deid', color='#e11d48', alpha=0.8)
            
            # Add horizontal line at 0
            ax2.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
            
            # Calculate y-axis limits with padding for text
            all_diffs = actual_target_diffs + actual_deid_diffs + target_deid_diffs
            if all_diffs:
                y_min = min(all_diffs) * 1.2 if min(all_diffs) < 0 else min(all_diffs) - 10
                y_max = max(all_diffs) * 1.2 if max(all_diffs) > 0 else max(all_diffs) + 10
                ax2.set_ylim(y_min, y_max)
            
            ax2.set_xlabel('Label')
            ax2.set_ylabel('Difference (%)')
            ax2.set_title(f'{sc_target} - Differences', fontsize=10)
            ax2.set_xticks(x)
            ax2.set_xticklabels([str(l) for l in labels])
            ax2.legend(fontsize=7, loc='upper right', framealpha=0.7)
            ax2.grid(axis='y', alpha=0.3)
        
        # Save combined plot with proper spacing
        fig.suptitle('Predictive Utility Analysis', fontsize=14)
        fig.tight_layout(pad=1.5, h_pad=3.0, rect=(0, 0, 1, 0.98))  # Minimal space for headers
        plot_path = Path(self.o_path, 'predictive_utility_combined.png')
        fig.savefig(plot_path, dpi=100, bbox_inches='tight')
        plt.close(fig)
        
        return [plot_path]
    
    def _create_loan_visualizations(self):
        """Create visualizations for the combined loan feature analysis"""
        if not self.loan_results:
            return
        
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # Get data from loan results
        actual = self.loan_results['actual_target']
        pred_target = self.loan_results['pred_target_on_target']
        pred_synthetic = self.loan_results['pred_synthetic_on_target']
        
        # Get unique labels
        labels = sorted(set(actual) | set(pred_target) | set(pred_synthetic))
        label_map = {'no_loan': 'No Loan', 
                    'govt_loan': 'Govt Loan',
                    'govt_guaranteed_bank_loan': 'Govt Guaranteed',
                    'bank_loan': 'Bank Loan',
                    'family_loan': 'Family Loan'}
        display_labels = [label_map.get(l, l) for l in labels]
        
        # Count occurrences
        actual_counts = [np.sum(actual == label) for label in labels]
        target_counts = [np.sum(pred_target == label) for label in labels]
        synthetic_counts = [np.sum(pred_synthetic == label) for label in labels]
        
        # First subplot: Distribution comparison
        x = np.arange(len(labels))
        width = 0.25
        
        ax1.bar(x - width, actual_counts, width, label='Actual', color='#ff9500', alpha=0.8)
        ax1.bar(x, target_counts, width, label='Target Model', color='#5373d8', alpha=0.8)
        ax1.bar(x + width, synthetic_counts, width, label='Deidentified Model', color='#4eb07a', alpha=0.8)
        
        ax1.set_xlabel('Loan Type', fontsize=11)
        ax1.set_ylabel('Count', fontsize=11)
        ax1.set_title(f'Combined Loan Feature - Distribution Comparison\n'
                     f'Target Acc={self.loan_results["acc_target"]:.3f}, '
                     f'Deid Acc={self.loan_results["acc_synthetic_on_target"]:.3f}',
                     fontsize=12)
        ax1.set_xticks(x)
        ax1.set_xticklabels(display_labels, rotation=45, ha='right')
        ax1.legend(fontsize=9)
        ax1.grid(axis='y', alpha=0.3)
        
        # Add value labels on bars
        for i, (a, t, s) in enumerate(zip(actual_counts, target_counts, synthetic_counts)):
            if a > 0:
                ax1.text(i - width, a, str(a), ha='center', va='bottom', fontsize=8)
            if t > 0:
                ax1.text(i, t, str(t), ha='center', va='bottom', fontsize=8)
            if s > 0:
                ax1.text(i + width, s, str(s), ha='center', va='bottom', fontsize=8)
        
        # Second subplot: Accuracy metrics comparison
        metrics = ['Accuracy', 'F1-Score']
        target_metrics = [self.loan_results['acc_target'], self.loan_results['f1_target']]
        synthetic_metrics = [self.loan_results['acc_synthetic_on_target'], self.loan_results['f1_synthetic']]
        
        x2 = np.arange(len(metrics))
        width2 = 0.35
        
        bars1 = ax2.bar(x2 - width2/2, target_metrics, width2, label='Target Model', color='#5373d8', alpha=0.8)
        bars2 = ax2.bar(x2 + width2/2, synthetic_metrics, width2, label='Deidentified Model', color='#4eb07a', alpha=0.8)
        
        ax2.set_ylabel('Score', fontsize=11)
        ax2.set_title('Loan Feature - Model Performance Metrics', fontsize=12)
        ax2.set_xticks(x2)
        ax2.set_xticklabels(metrics)
        ax2.legend(fontsize=9)
        ax2.set_ylim(0, 1.1)
        ax2.grid(axis='y', alpha=0.3)
        
        # Add value labels on bars
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax2.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:.3f}', ha='center', va='bottom', fontsize=9)
        
        # Add degradation text
        ax2.text(0.5, 0.95, 
                f'Accuracy Degradation: {self.loan_results["degradation"]:.3f}\n'
                f'F1-Score Degradation: {self.loan_results["f1_degradation"]:.3f}',
                transform=ax2.transAxes, ha='center', va='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5),
                fontsize=9)
        
        fig.suptitle('Combined Loan Feature - Predictive Utility Analysis', fontsize=14, fontweight='bold')
        fig.tight_layout()
        
        # Save plot
        loan_plot_path = Path(self.o_path, 'predictive_utility_loan_feature.png')
        fig.savefig(loan_plot_path, dpi=100, bbox_inches='tight')
        plt.close(fig)
        
        return loan_plot_path
    
    def _create_summary_degradation_grid(self):
        """Create a summary grid showing accuracy degradation for all features across subgroups."""
        # print(f"\nCreating summary degradation grid...")
        if not self.combined_feature_results:
            print("No combined feature results available for summary grid")
            return

        # Define the feature order (same as in feature_combinations dictionary)
        feature_order = [
            'SCGOVTLOAN', 'SCGOVTGUAR', 'SCBANKLOAN', 'SCFAMLOAN', 'SCGRANT',
            'Combined_Loan_Feature', 'Self_Funded_vs_External', 'Funding_Risk_Profile',
            'Government_Support', 'Funding_Complexity', 'Bootstrap_vs_Institutional',
            'Formal_vs_Informal', 'Credit_Dependency'
        ]

        # Get unique base features that exist in results (preserve order)
        base_feature_list = []
        for feature in feature_order:
            # Check if this feature exists in the results (excluding subgroup variants)
            if any(key == feature or key.startswith(f"{feature}_SEX1_") or key.startswith(f"{feature}_AGE1_")
                   for key in self.combined_feature_results.keys()):
                base_feature_list.append(feature)

        # Prepare data structures
        base_features = []
        all_degradations = []  # Will be list of lists for each subgroup
        subgroup_labels = []

        # Define subgroups to include
        subgroups = [
            ('Overall', ''),
            ('Male', '_SEX1_1'),
            ('Female', '_SEX1_2')
        ]

        # Add AGE1 subgroups if available
        age_values = set()
        for key in self.combined_feature_results.keys():
            if '_AGE1_' in key:
                age_val = key.split('_AGE1_')[-1]
                age_values.add(age_val)

        # Get age labels from data dictionary
        age_labels = self._get_age_labels()

        for age_val in sorted(age_values):
            age_label = age_labels.get(age_val, f'Age_{age_val}')
            subgroups.append((age_label, f'_AGE1_{age_val}'))

        # Extract subgroup labels for axis
        subgroup_labels = [sg[0] for sg in subgroups]

        # Collect degradation data for each feature and subgroup (preserving order)
        for feature in base_feature_list:
            base_features.append(feature.replace('_', ' '))
            
            feature_degradations = []
            for _, suffix in subgroups:
                if suffix == '':
                    # Overall feature
                    key = feature
                else:
                    # Subgroup feature
                    key = f"{feature}{suffix}"
                
                if key in self.combined_feature_results:
                    degradation = self.combined_feature_results[key].get('balanced_accuracy_degradation', 0) * 100
                    feature_degradations.append(degradation)
                else:
                    feature_degradations.append(0)
            
            all_degradations.append(feature_degradations)
        
        # Create the grid chart with dynamic size
        n_subgroups = len(subgroup_labels)
        fig, ax = plt.subplots(figsize=(max(8, n_subgroups * 1.2), 6))
        
        # Prepare data matrix (features x subgroups)
        degradation_matrix = np.array(all_degradations)
        
        # Create heatmap
        im = ax.imshow(degradation_matrix, cmap='RdYlGn_r', aspect='auto', vmin=-10, vmax=20)
        
        # Set ticks and labels
        ax.set_xticks(range(len(subgroup_labels)))
        ax.set_xticklabels(subgroup_labels, rotation=45, ha='right')
        ax.set_yticks(range(len(base_features)))
        ax.set_yticklabels(base_features)
        
        # Add title and labels
        ax.set_title('Predictive Utility Degradation Summary\n(Target - Deidentified) %', fontsize=12, pad=10)
        ax.set_xlabel('Population Group', fontsize=10)
        ax.set_ylabel('Feature Combination', fontsize=10)
        
        # Add text annotations
        for i in range(len(base_features)):
            for j in range(len(subgroup_labels)):
                value = degradation_matrix[i, j]
                color = 'white' if abs(value) > 10 else 'black'
                ax.text(j, i, f'{value:.1f}%', ha='center', va='center', 
                       color=color, fontsize=8, fontweight='bold')
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Degradation %', rotation=270, labelpad=20)
        
        # Adjust layout
        plt.tight_layout()
        
        # Save plot
        plot_path = Path(self.o_path, 'summary_degradation_grid.png')
        fig.savefig(plot_path, dpi=100, bbox_inches='tight')
        plt.close(fig)
        
        return plot_path
    
    def _get_age_labels(self):
        """Get age labels from data dictionary or return defaults."""
        if hasattr(self, 'data_dict') and self.data_dict and 'AGE1' in self.data_dict:
            age_dict_values = self.data_dict.get('AGE1', {}).get('values', {})
            # Convert to string keys for consistency
            return {str(k): v for k, v in age_dict_values.items()}
        else:
            # Fallback to default labels
            return {
            "0": "NOT REPORTED",
            "1": "UNDER 25",
            "2": "25 TO 34",
            "3": "35 TO 44",
            "4": "45 TO 54",
            "5": "55 TO 64",
            "6": "65 OR OVER"
        }
    
    def _create_combined_feature_visualizations(self):
        """Create visualizations for all combined feature analyses."""
        if not self.combined_feature_results:
            return []
        
        # Debug: Show what features we have
        # print(f"\nCreating plots for {len(self.combined_feature_results)} feature analyses:")
        # for key in sorted(self.combined_feature_results.keys()):
        #     print(f"  - {key}")
        
        plot_paths = []
        
        for feature_name, results in self.combined_feature_results.items():
            try:
                plot_path = self._create_combined_feature_plot(feature_name, results)
                if plot_path:
                    plot_paths.append(plot_path)
            except Exception as e:
                print(f"Error creating plot for {feature_name}: {e}")
                continue
        
        return plot_paths
    
    def _create_combined_feature_plot(self, feature_name: str, results: dict):
        """Create visualization for a specific combined feature with confusion matrix analysis."""
        # Check if this is a subgroup analysis
        subgroup_name = results.get('subgroup_name', None)
        
        # Clean feature name - remove SEX1 suffix if present for plotting
        if '_SEX1_' in feature_name:
            base_feature_name = feature_name.rsplit('_SEX1_', 1)[0]
        elif 'AGE1' in feature_name:
            base_feature_name = feature_name.rsplit('_AGE1_', 1)[0]
        else:
            base_feature_name = feature_name
        
        # Figure with 1 row, 3 columns (distribution + confusion matrix + degradation)
        fig, axes = plt.subplots(1, 3, figsize=(12, 3.5))
        
        # Get data
        actual = results['actual_target']
        pred_target = results['pred_target_on_target'] 
        pred_synthetic = results['pred_synthetic_on_target']
        
        # Get unique labels and their display names
        labels = sorted(set(actual) | set(pred_target) | set(pred_synthetic))
        
        # Count occurrences
        actual_counts = [np.sum(actual == label) for label in labels]
        target_counts = [np.sum(pred_target == label) for label in labels]
        synthetic_counts = [np.sum(pred_synthetic == label) for label in labels]
        
        # Plot 1: Distribution comparison
        x = np.arange(len(labels))
        width = 0.25
        
        axes[0].bar(x - width, actual_counts, width, label='Actual', color='#ff9500', alpha=0.8)
        axes[0].bar(x, target_counts, width, label='Target Model', color='#5373d8', alpha=0.8)
        axes[0].bar(x + width, synthetic_counts, width, label='Synthetic Model', color='#4eb07a', alpha=0.8)
        
        axes[0].set_xlabel('Category', fontsize=9)
        axes[0].set_ylabel('Count', fontsize=9)
        axes[0].set_title('Distribution Comparison', fontsize=10)
        axes[0].set_xticks(x)
        axes[0].set_xticklabels(labels, rotation=45, ha='right', fontsize=8)
        axes[0].legend(fontsize=8)
        axes[0].grid(axis='y', alpha=0.3)
        axes[0].tick_params(axis='both', which='major', labelsize=8)
        
        # Get y-axis max for matching scales
        y_max = max(max(actual_counts), max(target_counts), max(synthetic_counts)) * 1.1
        
        # Plot 2: Confusion Matrix comparison 
        cm_target = np.array(results['confusion_matrix_target'])
        cm_synthetic = np.array(results['confusion_matrix_synthetic'])
        
        # For binary classification, extract TP, TN, FP, FN
        if cm_target.shape == (2, 2):
            # Binary classification confusion matrix format:
            # [[TN, FP],
            #  [FN, TP]]
            target_metrics = [cm_target[1,1], cm_target[0,0], cm_target[0,1], cm_target[1,0]]  # TP, TN, FP, FN
            synthetic_metrics = [cm_synthetic[1,1], cm_synthetic[0,0], cm_synthetic[0,1], cm_synthetic[1,0]]  # TP, TN, FP, FN
            cm_labels = ['True +', 'True -', 'False +', 'False -']
        else:
            # Multi-class: show diagonal (correct) vs off-diagonal (incorrect) totals
            target_correct = np.diag(cm_target).sum()
            target_incorrect = cm_target.sum() - target_correct
            synthetic_correct = np.diag(cm_synthetic).sum()
            synthetic_incorrect = cm_synthetic.sum() - synthetic_correct
            target_metrics = [target_correct, target_incorrect]
            synthetic_metrics = [synthetic_correct, synthetic_incorrect]
            cm_labels = ['Correct', 'Incorrect']
        
        x2 = np.arange(len(cm_labels))
        width2 = 0.35
        
        bars1 = axes[1].bar(x2 - width2/2, target_metrics, width2, label='Target Model', color='#5373d8', alpha=0.8)
        bars2 = axes[1].bar(x2 + width2/2, synthetic_metrics, width2, label='Synthetic Model', color='#4eb07a', alpha=0.8)
        
        axes[1].set_ylabel('Count', fontsize=9)
        axes[1].set_title('Confusion Matrix', fontsize=10)
        axes[1].set_xticks(x2)
        axes[1].set_xticklabels(cm_labels, fontsize=8)
        axes[1].legend(fontsize=8)
        axes[1].grid(axis='y', alpha=0.3)
        axes[1].tick_params(axis='both', which='major', labelsize=8)
        
        # Match y-axis range with first chart
        axes[1].set_ylim(0, y_max)
        
        # No value labels on bars for cleaner look
        
        # Get balanced accuracy values from results
        bal_acc_target = results['balanced_accuracy_target']
        bal_acc_synthetic = results['balanced_accuracy_synthetic']
        
        # Plot 3: Per-category degradation percentages
        # Calculate degradation for each category/label
        target_degradations = []
        synthetic_degradations = []
        
        for label in labels:
            # Count correct predictions for this label
            actual_label_mask = actual == label
            if np.sum(actual_label_mask) > 0:
                # Target model accuracy for this label
                target_correct = np.sum((pred_target == label) & actual_label_mask)
                target_acc = target_correct / np.sum(actual_label_mask)
                target_deg = (1.0 - target_acc) * 100
                
                # Synthetic model accuracy for this label
                synthetic_correct = np.sum((pred_synthetic == label) & actual_label_mask)
                synthetic_acc = synthetic_correct / np.sum(actual_label_mask)
                synthetic_deg = (1.0 - synthetic_acc) * 100
            else:
                target_deg = 0
                synthetic_deg = 0
            
            target_degradations.append(target_deg)
            synthetic_degradations.append(synthetic_deg)
        
        # Plot grouped bars for each category
        x3 = np.arange(len(labels))
        width3 = 0.35  # Bar width
        
        bars3_target = axes[2].bar(x3 - width3/2, target_degradations, width3, 
                                   label='Target Model', color='#5373d8', alpha=0.8)
        bars3_synthetic = axes[2].bar(x3 + width3/2, synthetic_degradations, width3, 
                                      label='Deid Model', color='#4eb07a', alpha=0.8)
        
        axes[2].axhline(y=0, color='black', linestyle='-', linewidth=0.8)
        axes[2].set_ylabel('Error Rate %', fontsize=9)
        axes[2].set_title('Per-Category Error Rates', fontsize=10)
        axes[2].set_xticks(x3)
        axes[2].set_xticklabels(labels, rotation=45, ha='right', fontsize=8)
        axes[2].legend(fontsize=8)
        axes[2].grid(axis='y', alpha=0.3)
        axes[2].tick_params(axis='both', which='major', labelsize=8)
        
        # No value labels on bars for cleaner look
        
        # Fix y-axis range to 0-100
        axes[2].set_ylim(0, 100)
        
        # Add balanced accuracy info to main title
        if subgroup_name:
            title = f'{base_feature_name} ({subgroup_name}) | Bal.Acc: Target={bal_acc_target:.3f}, Deid={bal_acc_synthetic:.3f}, Δ={bal_acc_target - bal_acc_synthetic:+.3f}'
        else:
            title = f'{base_feature_name} | Bal.Acc: Target={bal_acc_target:.3f}, Deid={bal_acc_synthetic:.3f}, Δ={bal_acc_target - bal_acc_synthetic:+.3f}'
        fig.suptitle(title, fontsize=10, y=1.02)
        
        plt.tight_layout()
        plt.subplots_adjust(top=0.88)  # Make more room for suptitle
        
        # Save plot with appropriate filename
        if subgroup_name:
            # print(f"DEBUG: subgroup_name = '{subgroup_name}'")  # Debug print
            if 'SEX1=' in subgroup_name:
                # Extract SEX value from subgroup_name (e.g., "SEX1=1" -> "1")
                sex_value = subgroup_name.split('=')[1]
                plot_filename = f'combined_feature_{base_feature_name.lower()}_sex{sex_value}.png'
            elif 'AGE1=' in subgroup_name:
                # Extract AGE1 value from subgroup_name (e.g., "AGE1=1" -> "1")
                age_value = subgroup_name.split('=')[1]
                plot_filename = f'combined_feature_{base_feature_name.lower()}_age1_{age_value}.png'
            else:
                # Fallback for other subgroup types
                plot_filename = f'combined_feature_{base_feature_name.lower()}_{subgroup_name.lower().replace("=", "_")}.png'
            # print(f"DEBUG: plot_filename = '{plot_filename}'")  # Debug print
        else:
            plot_filename = f'combined_feature_{base_feature_name.lower()}.png'
        plot_path = Path(self.o_path, plot_filename)
        fig.savefig(plot_path, dpi=100, bbox_inches='tight')
        plt.close(fig)
        
        return plot_path
    
    def _prepare_report_data(self):
        # Handle case where individual results might be empty
        if self.results:
            # Summary statistics for individual features
            accuracies_target = [r['acc_target'] for r in self.results.values()]
            accuracies_synthetic = [r['acc_synthetic_on_target'] for r in self.results.values()]
            degradations = [r['degradation'] for r in self.results.values()]
            
            self.report_data = {
                'features_evaluated': list(self.results.keys()),
                'mean_target_accuracy': np.mean(accuracies_target),
                'mean_synthetic_accuracy': np.mean(accuracies_synthetic),
                'mean_degradation': np.mean(degradations),
                'individual_results': {
                    k: {
                        'accuracy_target': v['acc_target'],
                        'accuracy_synthetic': v['acc_synthetic_on_target'],
                        'degradation': v['degradation']
                    }
                    for k, v in self.results.items()
                }
            }
        else:
            # No individual results, just initialize base structure
            self.report_data = {
                'features_evaluated': [],
                'mean_target_accuracy': 0,
                'mean_synthetic_accuracy': 0,
                'mean_degradation': 0,
                'individual_results': {}
            }
        
        # Add combined feature analyses if available
        if self.combined_feature_results:
            self.report_data['combined_feature_analyses'] = {}
            for feature_name, results in self.combined_feature_results.items():
                # Ensure all values are native Python types for JSON serialization
                self.report_data['combined_feature_analyses'][feature_name] = {
                    'accuracy_target': float(results.get('accuracy_target', 0)),
                    'accuracy_synthetic': float(results.get('accuracy_synthetic', 0)),
                    'balanced_accuracy_target': float(results.get('balanced_accuracy_target', 0)),
                    'balanced_accuracy_synthetic': float(results.get('balanced_accuracy_synthetic', 0)),
                    'f1_target': float(results.get('f1_target', 0)),
                    'f1_synthetic': float(results.get('f1_synthetic', 0)),
                    'accuracy_degradation': float(results.get('accuracy_degradation', 0)),
                    'balanced_accuracy_degradation': float(results.get('balanced_accuracy_degradation', 0)),
                    'f1_degradation': float(results.get('f1_degradation', 0)),
                    'class_distribution': {str(k): int(v) for k, v in results.get('class_distribution', {}).items()},
                    'is_multiclass': bool(results.get('is_multiclass', False))
                }