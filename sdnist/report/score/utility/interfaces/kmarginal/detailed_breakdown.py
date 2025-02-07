from typing import Dict, Tuple

from sdnist.metrics.pearson_correlation import \
    PearsonCorrelationDifference

from sdnist.report.score.paragraphs import *
from sdnist.report.score.utility.interfaces.univariates import \
    UnivariatesReport
from sdnist.report.dataset import Dataset
from sdnist.report.report_data import \
    ReportData, ReportUIData, Attachment, AttachmentType
from sdnist.report.plots import PearsonCorrelationPlot


import sdnist.strs as strs
from sdnist.utils import *


def worst_kmarginal_score_breakdown(worst_scores: List,
                                    dataset: Dataset,
                                    ui_data: ReportUIData,
                                    report_data: ReportData,
                                    feature: str) -> Tuple[List[Attachment], Dict[str, any]]:
    ds = dataset
    r_ui_d = ui_data
    rd = report_data
    k_marg_break_rd = dict()   # k marginal breakdown worst performing puma report

    rev_bin_mapping = {v: k for k, v in
                       ds.bin_mappings[feature].items()}

    wsh = pd.DataFrame(worst_scores)
    # wsh[feature] = wsh[feature].apply(lambda x: rev_bin_mapping[x])
    wpf = []
    if str(wsh.loc[0, feature]).startswith('['):
        wsh[feature] = wsh[feature].apply(lambda x: rev_bin_mapping[list(x)[0]])
        wpf = wsh[feature].unique().tolist()[:5]  # worst performing feature values
    t_o = dataset.d_target_data.copy()
    s_o = dataset.d_synthetic_data.copy()

    t = t_o[dataset.d_target_data[feature].isin(wpf)]
    s = s_o[dataset.d_synthetic_data[feature].isin(wpf)]

    out_dir = Path(r_ui_d.output_directory, 'kmarg_detail')
    if not out_dir.exists():
        os.mkdir(out_dir)

    univariate_report = UnivariatesReport(ds, r_ui_d, rd, 3,
                                          out_dir = out_dir,
                                          stable_feature=feature,
                                          worst_stable_feature_values=wpf)
    univariate_report.compute(level=3)
    u_as = univariate_report.add_to_ui()

    k_marg_break_rd[f'univariate'] = univariate_report.up.report_data(level=3)
    k_marg_break_rd[f'k_marginal_scores'] = \
        relative_path(save_data_frame(wsh,
                                      out_dir,
                                      f'worst'),
                      level=2)

    corr_features = ds.corr_features
    unavailable_features = set(corr_features) - set(s_o.columns)
    corr_features = list(set(corr_features) - unavailable_features)
    pcd = PearsonCorrelationDifference(t, s,
                                       corr_features)
    pcd.compute()

    pcp = PearsonCorrelationPlot(pcd.pp_corr_diff, out_dir)
    pcp_saved_file_paths = pcp.save(path_level=3)
    k_marg_break_rd['correlation_difference'] = {
        "pearson_correlation_difference": pcp.report_data
    }

    rel_pcp_saved_file_paths = ["/".join(list(p.parts)[-3:])
                                for p in pcp_saved_file_paths]

    # attachment for records in each data for worst performing feature
    a_para_rt = Attachment(name=f'Record Counts in {len(wpf)} '
                                + feature + ' with least fidelity',
                           _data=rec_count_worst_para.replace(strs.STABLE_FEATURE, feature),
                           _type=AttachmentType.String)
    a_rt = Attachment(name=None,
                      _data=[{"Dataset": "Target", "Record Counts": t.shape[0]},
                             {"Dataset": "Deidentified", "Record Counts": s.shape[0]}],
                      _type=AttachmentType.Table)

    a_para_pc = Attachment(name=f"Pearson Correlation Coefficient Difference of "
                                f"least fidelity " + feature,
                           _data=pear_corr_worst_para.replace(strs.STABLE_FEATURE, feature),
                           _type=AttachmentType.String)
    a_pc = Attachment(name=None,
                      _data=[{strs.IMAGE_NAME: Path(p).stem, strs.PATH: p}
                             for p in rel_pcp_saved_file_paths],
                      _type=AttachmentType.ImageLinks)
    attachments = [a_para_rt, a_rt] + u_as + [a_para_pc, a_pc]
    return attachments, k_marg_break_rd
