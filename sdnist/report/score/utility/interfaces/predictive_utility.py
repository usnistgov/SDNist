from pathlib import Path

from sdnist.report.dataset import Dataset
from sdnist.report.dataset.data_dict import get_feature_type
from sdnist.report.report_data import (
    ReportData, ReportUIData, UtilityScorePacket, Attachment, AttachmentType
)
from sdnist.metrics.predictive_utility import PredictiveUtility
import sdnist.strs as strs


class PredictiveUtilityReport:
    def __init__(self, dataset: Dataset, ui_data: ReportUIData, report_data: ReportData):
        self.ds = dataset
        self.r_ui_d = ui_data
        self.rd = report_data
        
        # Extract feature types for all columns
        feature_types = {}
        for feature in self.ds.t_target_data.columns:
            if feature in self.ds.data_dict:
                feature_types[feature] = get_feature_type(self.ds.data_dict, feature)
            else:
                # Default to categorical if not in data dict
                feature_types[feature] = strs.CATEGORICAL
        
        # Use transformed data with feature types
        self.metric = PredictiveUtility(
            self.ds.t_target_data,
            self.ds.t_synthetic_data,
            self.r_ui_d.output_directory,
            feature_types=feature_types,
            data_dict=self.ds.data_dict
        )
        
        self.results = None
    
    def compute(self):
        # Run the metric computation
        self.results = self.metric.compute_score()
    
    def add_to_ui(self):
        # Check if we have any results (individual or combined)
        has_combined_results = hasattr(self.metric, 'combined_feature_results') and self.metric.combined_feature_results
        
        if not self.results and not has_combined_results:
            return
        
        # Add to report data
        self.rd.add('predictive_utility', self.metric.report_data)
        
        # Create attachments for UI
        attachments = []
        
        # Add description paragraph
        desc_para = (
            "Predictive Utility measures how well machine learning models trained on deidentified data "
            "perform compared to models trained on real data. We analyze 8 different feature combinations "
            "that capture various business financing patterns: loan types, funding sources, risk profiles, "
            "and funding complexity. For each combination, we train logistic regression models to predict "
            "the target feature from all other non-SC features. Models are trained on 60% of the data and tested on 40%. "
            "The charts show distribution comparisons and confusion matrix analysis focusing on balanced accuracy."
        )
        
        # Add detailed explanations for each use case
        use_case_explanations = {
            'Original_Loan_Feature': (
                "<b>Original Loan Feature:</b> This use case combines four specific loan-related startup capital features into a single categorical target variable: "
                "<br>• <b>SCGOVTLOAN</b> - Government business loan "
                "<br>• <b>SCGOVTGUAR</b> - Government guaranteed bank loan "
                "<br>• <b>SCBANKLOAN</b> - Bank business loan "
                "<br>• <b>SCFAMLOAN</b> - Family/friend business loan "
                "<br><br><b>Combination Logic:</b> Uses hierarchical priority ordering where each business is classified into exactly one category based on the highest priority loan type used: "
                "1) Government loan (highest priority), 2) Government guaranteed bank loan, 3) Bank loan, 4) Family loan, 5) No loan (if all are 0/2/missing). "
                "This hierarchy reflects the formal lending structure and helps analyze if deidentification preserves governmental vs private loan access patterns across demographic groups."
            ),
            'Self_Funded_vs_External': (
                "<b>Self-Funded vs External:</b> Creates a binary classification to distinguish financing independence levels using multiple startup capital features: "
                "<br><br><b>Personal Resources (Self-Funded):</b> "
                "<br>• <b>SCSAVINGS</b> - Personal/family savings "
                "<br>• <b>SCASSETS</b> - Personal/family assets "
                "<br>• <b>SCEQUITY</b> - Home equity loan "
                "<br><br><b>External Sources:</b> "
                "<br>• <b>SCGOVTLOAN</b> - Government business loan "
                "<br>• <b>SCGOVTGUAR</b> - Government guaranteed loan "
                "<br>• <b>SCBANKLOAN</b> - Bank business loan "
                "<br>• <b>SCFAMLOAN</b> - Family/friend loan "
                "<br>• <b>SCCREDIT</b> - Credit card "
                "<br>• <b>SCVENTURE</b> - Venture capital "
                "<br>• <b>SCGRANT</b> - Government grant "
                "<br><br><b>Classification Logic:</b> A business is 'self_funded' only if it uses personal resources AND has no external funding sources. "
                "All others are 'external_funded'. This captures fundamental entrepreneurial financing philosophy and economic independence."
            ),
            'Funding_Risk_Profile': (
                "<b>Funding Risk Profile:</b> Categorizes businesses into financial risk tiers based on funding source risk characteristics: "
                "<br><br><b>Low Risk:</b> Only personal resources (SCSAVINGS=1 OR SCASSETS=1 OR SCEQUITY=1) with no external sources "
                "<br><b>Medium Risk:</b> Default category for mixed personal/informal or moderate external funding "
                "<br><b>High Risk:</b> Uses formal debt instruments (SCCREDIT=1 OR SCBANKLOAN=1 OR SCGOVTLOAN=1 OR SCGOVTGUAR=1) but no venture capital "
                "<br><b>Very High Risk:</b> Uses venture capital (SCVENTURE=1) regardless of other sources "
                "<br><br><b>Classification Logic:</b> Risk hierarchy with venture capital as highest risk (equity dilution), "
                "formal loans as high risk (debt obligations), personal resources as lowest risk (no external obligations), "
                "and everything else as medium risk. This reflects financial leverage and external dependency levels."
            ),
            'Government_Support': (
                "<b>Government Support:</b> Identifies businesses receiving government financial assistance through various programs: "
                "<br><br><b>Features Used:</b> "
                "<br>• <b>SCGOVTLOAN</b> - Direct government business loan "
                "<br>• <b>SCGOVTGUAR</b> - Government guaranteed bank loan "
                "<br>• <b>SCGRANT</b> - Government grant (non-repayable) "
                "<br><br><b>Classification Logic:</b> Three-tier system with grant priority: "
                "1) 'grant_support' if SCGRANT=1 (highest priority - free money), "
                "2) 'loan_support' if SCGOVTLOAN=1 OR SCGOVTGUAR=1 (government-backed lending), "
                "3) 'no_support' if all are 0/2/missing. "
                "This measures public sector involvement in business financing and helps assess whether deidentification preserves "
                "patterns of government program utilization across different demographic groups, which is crucial for policy analysis."
            ),
            'Funding_Complexity': (
                "<b>Funding Complexity:</b> Measures financing diversification by counting the total number of distinct funding sources used: "
                "<br><br><b>All Startup Capital Features Counted:</b> "
                "<br>• <b>SCSAVINGS</b> - Personal/family savings "
                "<br>• <b>SCASSETS</b> - Personal/family assets "
                "<br>• <b>SCEQUITY</b> - Home equity loan "
                "<br>• <b>SCCREDIT</b> - Credit card "
                "<br>• <b>SCGOVTLOAN</b> - Government business loan "
                "<br>• <b>SCGOVTGUAR</b> - Government guaranteed loan "
                "<br>• <b>SCBANKLOAN</b> - Bank business loan "
                "<br>• <b>SCFAMLOAN</b> - Family/friend loan "
                "<br>• <b>SCVENTURE</b> - Venture capital "
                "<br>• <b>SCGRANT</b> - Government grant "
                "<br>• <b>SCOTHER</b> - Other sources "
                "<br><br><b>Classification Logic:</b> Count sources where value=1 (YES), then categorize: "
                "'simple' (1 source), 'moderate' (2-3 sources), 'complex' (4+ sources). "
                "This indicates financial sophistication, risk diversification strategies, and capital access breadth."
            ),
            'Bootstrap_vs_Institutional': (
                "<b>Bootstrap vs Institutional:</b> Distinguishes entrepreneurial funding strategies between self-reliant and institutional approaches: "
                "<br><br><b>Bootstrap Sources:</b> "
                "<br>• <b>SCSAVINGS</b> - Personal/family savings "
                "<br>• <b>SCASSETS</b> - Personal/family assets "
                "<br>• <b>SCEQUITY</b> - Home equity loan "
                "<br>• <b>SCFAMLOAN</b> - Family/friend loan "
                "<br><br><b>Institutional Sources:</b> "
                "<br>• <b>SCBANKLOAN</b> - Bank business loan "
                "<br>• <b>SCGOVTLOAN</b> - Government business loan "
                "<br>• <b>SCGOVTGUAR</b> - Government guaranteed loan "
                "<br>• <b>SCVENTURE</b> - Venture capital "
                "<br><br><b>Classification Logic:</b> 'bootstrap' if only bootstrap sources used, "
                "'institutional' if only institutional sources used, 'mixed' if both types used or neither. "
                "This reveals market access patterns, financial network strength, and institutional relationship preferences."
            ),
            'Formal_vs_Informal': (
                "<b>Formal vs Informal:</b> Categorizes financing approaches based on financial system formalization levels: "
                "<br><br><b>Formal Financial Institutions:</b> "
                "<br>• <b>SCBANKLOAN</b> - Bank business loan "
                "<br>• <b>SCGOVTLOAN</b> - Government business loan "
                "<br>• <b>SCGOVTGUAR</b> - Government guaranteed loan "
                "<br>• <b>SCVENTURE</b> - Venture capital "
                "<br>• <b>SCGRANT</b> - Government grant "
                "<br><br><b>Informal Sources:</b> All other startup capital sources including personal savings, assets, "
                "home equity, credit cards, family/friend loans, and other sources. "
                "<br><br><b>Classification Logic:</b> 'formal' if any formal institutional source used (=1), "
                "'informal' if only informal sources used. This measures integration with traditional financial markets, "
                "regulatory compliance levels, and access to established financial institutions."
            ),
            'Credit_Dependency': (
                "<b>Credit Dependency:</b> Identifies businesses exposed to personal credit risk through credit-based financing: "
                "<br><br><b>Credit Risk Sources:</b> "
                "<br>• <b>SCCREDIT</b> - Credit card financing "
                "<br>• <b>SCEQUITY</b> - Home equity loan "
                "<br><br><b>Classification Logic:</b> 'has_credit_risk' if SCCREDIT=1 OR SCEQUITY=1, "
                "'no_credit_risk' otherwise. "
                "<br><br>This captures businesses that depend on personal creditworthiness and collateral (home) for financing, "
                "indicating potential financial vulnerability, limited access to business credit, or strategic use of personal leverage. "
                "Credit cards represent unsecured high-interest debt, while home equity represents secured debt with asset risk."
            )
        }
        
        attachments.append(
            Attachment(
                name=None,
                _data=desc_para,
                _type=AttachmentType.String
            )
        )
        
        # Add summary statistics for combined features
        if has_combined_results:
            # Calculate overall statistics from combined features (balanced accuracy only)
            # Exclude subgroup results from overall statistics
            overall_results = {k: v for k, v in self.metric.combined_feature_results.items() 
                             if '_SEX1_' not in k and '_AGE1_' not in k}
            all_target_acc = [r.get('balanced_accuracy_target', 0) for r in overall_results.values()]
            all_synthetic_acc = [r.get('balanced_accuracy_synthetic', 0) for r in overall_results.values()]
            all_degradation = [r.get('balanced_accuracy_degradation', 0) for r in overall_results.values()]
            
            if all_target_acc:  # Only if we have data
                mean_target = sum(all_target_acc) / len(all_target_acc)
                mean_synthetic = sum(all_synthetic_acc) / len(all_synthetic_acc)
                mean_degradation = sum(all_degradation) / len(all_degradation)
                
                summary_text = (
                    f"Combined Features Analysis: {len(self.metric.combined_feature_results)} feature combinations<br>"
                    f"Mean Target Balanced Accuracy: {mean_target:.3f}<br>"
                    f"Mean Deidentified Balanced Accuracy: {mean_synthetic:.3f}<br>"
                    f"Mean Degradation: {mean_degradation:.3f}"
                )
                
                attachments.append(
                    Attachment(
                        name=None,
                        _data=f"Highlight-Score: {summary_text}",
                        _type=AttachmentType.String
                    )
                )
        
        # Note: Old individual plots removed - now using combined feature analyses only
        # Add accuracy grid plot first
        # grid_path = Path(self.metric.o_path, 'predictive_utility_accuracy_grid.png')
        # if grid_path.exists():
        #     rel_path = "/".join(list(grid_path.parts)[-2:])
        #     attachments.append(
        #         Attachment(
        #             name='Target and Deid Models Accuracies',
        #             _data=[{strs.IMAGE_NAME: 'predictive_utility_accuracy_grid', strs.PATH: rel_path}],
        #             _type=AttachmentType.ImageLinks
        #         )
        #     )
        # Add combined feature analyses if available
        if hasattr(self.metric, 'combined_feature_results') and self.metric.combined_feature_results:
            # Add section header for combined analyses
            attachments.append(
                Attachment(
                    name=None,
                    _data="<br><b>Combined Feature Analyses:</b><br>",
                    _type=AttachmentType.String
                )
            )
            
            # Add summary degradation grid if it exists
            summary_grid_path = Path(self.metric.o_path, 'summary_degradation_grid.png')
            # print(f"Debug: Looking for summary grid at {summary_grid_path}")
            if summary_grid_path.exists():
                rel_path = "/".join(list(summary_grid_path.parts)[-2:])
                # print(f"Debug: Summary grid found, adding attachment with rel_path: {rel_path}")
                attachments.append(
                    Attachment(
                        name='Summary: Accuracy Degradation by Group',
                        _data=[{strs.IMAGE_NAME: 'summary_degradation_grid', strs.PATH: rel_path}],
                        _type=AttachmentType.ImageLinks
                    )
                )
                # print(f"Debug: Summary grid attachment added successfully")
            else:
                print(f"Warning: Summary grid not found at {summary_grid_path}")
            
            ## Add summary of all combined features (balanced accuracy only)
            # combined_summary_lines = []
            
            # Process overall features first
            # for feature_name, results in self.metric.combined_feature_results.items():
            #     # Skip subgroup results in main summary
            #     if '_SEX1_' in feature_name or '_RACE1_Transformed_' in feature_name:
            #         continue
            #
            #     bal_acc_target = results.get('balanced_accuracy_target', 0)
            #     bal_acc_synthetic = results.get('balanced_accuracy_synthetic', 0)
            #     degradation = results.get('balanced_accuracy_degradation', 0)
            #
            #     combined_summary_lines.append(
            #         f"<b>{feature_name.replace('_', ' ')} (Overall):</b><br>"
            #         f"  Balanced Acc: {bal_acc_target:.3f} → {bal_acc_synthetic:.3f} (Δ{degradation:+.3f})<br>"
            #     )
            #
            #     # Add demographic subgroup summaries
            #     self._add_demographic_summaries(feature_name, combined_summary_lines)
            
            # combined_summary = "<br>".join(combined_summary_lines)
            # attachments.append(
            #     Attachment(
            #         name=None,
            #         _data=f"Highlight-Score: {combined_summary}",
            #         _type=AttachmentType.String
            #     )
            # )

            # Add individual plots for each combined feature
            # Organize plots by base feature name
            base_features = set()
            for feature_key in self.metric.combined_feature_results.keys():
                # Extract base feature name (without SEX1 suffix)
                if '_SEX1_' in feature_key:
                    base_name = feature_key.rsplit('_SEX1_', 1)[0]
                elif '_AGE1_' in feature_key:
                    base_name = feature_key.rsplit('_AGE1_', 1)[0]
                else:
                    base_name = feature_key
                base_features.add(base_name)
            
            # Process each base feature and its subgroups
            for base_feature in sorted(base_features):
                # Add explanation for this use case
                if base_feature in use_case_explanations:
                    attachments.append(
                        Attachment(
                            name=None,
                            _data=f"<br>{use_case_explanations[base_feature]}<br><br>",
                            _type=AttachmentType.String
                        )
                    )
                
                # Add overall plot
                self._add_plot_attachment(attachments, base_feature, '', 'Overall')

                # Add SEX1 subgroup plots
                self._add_demographic_plots(attachments, base_feature, 'SEX1')

                # Add AGE1 subgroup plots
                self._add_demographic_plots(attachments, base_feature, 'AGE1')
        
        # Create packet and add to UI
        # print(f"Debug: Creating packet with {len(attachments)} attachments")
        packet = UtilityScorePacket(
            self.metric.NAME,
            None,
            attachments
        )
        self.r_ui_d.add(packet)
        # print(f"Debug: Packet added to UI with attachments")
    
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
    
    def _add_demographic_summaries(self, feature_name, combined_summary_lines):
        """Add demographic subgroup summaries for a feature."""
        # SEX1 subgroups
        sex_subgroups = [(k, k.split('_')[-1]) for k in self.metric.combined_feature_results.keys() 
                         if k.startswith(f"{feature_name}_SEX1_")]
        
        for subgroup_key, sex_value in sorted(sex_subgroups):
            sub_results = self.metric.combined_feature_results[subgroup_key]
            sub_bal_acc_target = sub_results.get('balanced_accuracy_target', 0)
            sub_bal_acc_synthetic = sub_results.get('balanced_accuracy_synthetic', 0)
            sub_degradation = sub_results.get('balanced_accuracy_degradation', 0)
            
            sex_label = 'Male' if sex_value == '1' else 'Female' if sex_value == '2' else f'SEX1={sex_value}'
            combined_summary_lines.append(
                f"    • {sex_label}: {sub_bal_acc_target:.3f} → {sub_bal_acc_synthetic:.3f} (Δ{sub_degradation:+.3f})<br>"
            )
        
        # AGE1 subgroups
        age_subgroups = [(k, k.split('_')[-1]) for k in self.metric.combined_feature_results.keys()
                          if k.startswith(f"{feature_name}_AGE1_")]
        
        # Get age labels from data dictionary
        age_labels = self._get_age_labels()
        
        for subgroup_key, age_value in sorted(age_subgroups):
            sub_results = self.metric.combined_feature_results[subgroup_key]
            sub_bal_acc_target = sub_results.get('balanced_accuracy_target', 0)
            sub_bal_acc_synthetic = sub_results.get('balanced_accuracy_synthetic', 0)
            sub_degradation = sub_results.get('balanced_accuracy_degradation', 0)
            
            age_label = age_labels.get(age_value, f'Age_{age_value}')
            combined_summary_lines.append(
                f"    • {age_label}: {sub_bal_acc_target:.3f} → {sub_bal_acc_synthetic:.3f} (Δ{sub_degradation:+.3f})<br>"
            )
    
    def _add_plot_attachment(self, attachments, base_feature, suffix, label):
        """Add a single plot attachment."""
        if suffix:
            plot_filename = f'combined_feature_{base_feature.lower()}_{suffix}.png'
        else:
            plot_filename = f'combined_feature_{base_feature.lower()}.png'

        plot_path = Path(self.metric.o_path, plot_filename)
        if plot_path.exists():
            rel_path = "/".join(list(plot_path.parts)[-2:])
            display_name = base_feature.replace('_', ' ')
            image_name = plot_filename.replace('.png', '')
            
            attachments.append(
                Attachment(
                    name=f'{display_name} Analysis ({label})',
                    _data=[{strs.IMAGE_NAME: image_name, strs.PATH: rel_path}],
                    _type=AttachmentType.ImageLinks
                )
            )
        else:
            print(f"Warning: Plot not found for {base_feature} {label} at {plot_path}")
    
    def _add_demographic_plots(self, attachments, base_feature, demographic_col):
        """Add demographic subgroup plots for a feature."""
        # Find subgroup results for this demographic

        subgroups = [(k, k.split('_')[-1]) for k in self.metric.combined_feature_results.keys() 
                     if k.startswith(f"{base_feature}_{demographic_col}_")]
        
        # Define labels based on demographic column
        if demographic_col == 'SEX1':
            label_map = {'1': 'Male', '2': 'Female'}
            suffix_template = 'sex{}'
        elif demographic_col == 'AGE1':
            label_map = self._get_age_labels()
            suffix_template = 'age1_{}'
        else:
            label_map = {}
            suffix_template = '{}'

        for subgroup_key, demo_value in sorted(subgroups):
            suffix = suffix_template.format(demo_value)
            label = label_map.get(demo_value, f'{demographic_col}={demo_value}')
            self._add_plot_attachment(attachments, base_feature, suffix, label)