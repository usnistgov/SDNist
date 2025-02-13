from typing import Tuple

from sdnist.report import Dataset, ReportData, ReportUIData
from sdnist.report.plots import ApparentMatchDistributionPlot
from sdnist.metrics.disco import KDiscoEvaluator
from sdnist.metrics.unique_exact_matches import unique_exact_matches
from sdnist.report.report_data import PrivacyScorePacket, Attachment, AttachmentType
from sdnist.report.score.paragraphs import *
from sdnist.strs import *
from sdnist.utils import *
from sdnist.load import TestDatasetName


def privacy_score(
    dataset: Dataset, ui_data: ReportUIData, report_data, log: SimpleLogger
) -> Tuple[ReportUIData, ReportData]:
    ds: Dataset = dataset
    r_ui_d: ReportUIData = ui_data
    rd = report_data

    log.msg("Unique Exact Matches", level=3)
    (
        t_rec_matched,
        perc_t_rec_matched,
        unique_target_records,
        perc_unique_target_records,
    ) = unique_exact_matches(ds.t_target_data, ds.t_synthetic_data)
    perc_t_rec_matched = perc_t_rec_matched
    uem_para1_a = Attachment(
        name=None, _data=unique_exact_match_para_1, _type=AttachmentType.String
    )

    feat_space_str = "{:0.3e}".format(ds.feature_space)
    target_matched_a = Attachment(
        name="Target Data Properties",
        _data=f"Feature space size (possible combinations): "
        f"-Highlight-{feat_space_str}-Highlight-<br>"
        f"Number of unique records in Target Data: "
        f"-Highlight-{unique_target_records} "
        f"({perc_unique_target_records}%-Highlight-)",
        _type=AttachmentType.String,
    )
    deid_matched_a = Attachment(
        name="Deidentified Data Properties",
        _data=f"Number of unique Target Data records exactly "
        f"matched in Deid. Data: "
        f"-Highlight-{t_rec_matched} "
        f"({perc_t_rec_matched}%)-Highlight-",
        _type=AttachmentType.String,
    )
    r_ui_d.add(
        PrivacyScorePacket(
            "Unique Exact Matches",
            None,
            [
                uem_para1_a,
                target_matched_a,
                deid_matched_a,
            ],
        )
    )
    rd.add(
        "unique_exact_matches",
        {
            "records matched in target data": t_rec_matched,
            "percent records matched in target data": perc_t_rec_matched,
            "unique target records": unique_target_records,
            "percent unique target records": perc_unique_target_records,
        },
    )

    log.end_msg()
    quasi_idf = []  # list of quasi-identifier features
    excluded = []  # list of excluded features from apparent match computation
    use_apparent_match = True
    if ds.test == TestDatasetName.sbo_target:
        quasi_idf = ["SEX1", "FIPST", "SECTOR", "VET1", "RACE1"]
    else:
        quasi_idf = ["SEX", "MSP", "RAC1P", "OWN_RENT", "EDU", "PUMA",
                     "INDP_CAT", "HISP"]
    quasi_idf = list(set(ds.features).intersection(set(quasi_idf)))
    if len(quasi_idf) == 0:
        log.msg(
            "No quasi-identifier feature found in the dataset. Skipping Apparent Match Distribution.",
            level=2,
            timed=False,
            msg_type="warn",
        )
        use_apparent_match = False

    if use_apparent_match and ds.test != TestDatasetName.sbo_target:
        # Apparent Match Distribution Packet
        log.msg("Apparent Match Distribution", level=3)

        amd_para_a = Attachment(
            name=None, _data=app_match_para, _type=AttachmentType.String
        )
        # Quasi-identifier list as attachment
        quasi_para_a = Attachment(
            name="Quasi-Identifiers", _data=quasi_idf_para, _type=AttachmentType.String
        )
        quasi_list_atch = Attachment(
            name=None, _data=", ".join(quasi_idf), _type=AttachmentType.String
        )

        excluded = []
        amd_plot = ApparentMatchDistributionPlot(
            ds.c_synthetic_data,
            ds.c_target_data,
            r_ui_d.output_directory,
            quasi_idf,
            excluded,
        )
        amd_plot_paths = amd_plot.save()
        rd.add("apparent_match_distribution", amd_plot.report_data)

        rel_cdp_saved_file_paths = [
            "/".join(list(p.parts)[-2:]) for p in amd_plot_paths
        ]

        # Total rows matched on quasi-identifiers as attachment
        rec_matched = amd_plot.quasi_matched_df.shape[0]
        rec_percent = round(rec_matched / ds.c_target_data.shape[0] * 100, 2)

        rec_mat_para_a = Attachment(
            name="Records Matched on Quasi-Identifiers",
            _data=rec_matched_para,
            _type=AttachmentType.String,
        )
        total_quasi_matched = Attachment(
            name=None,
            _data=f"Number of Target Data records exactly matched "
            f"in Deid. Data on Quasi-Identifiers: "
            f"-Highlight-{rec_matched} ({rec_percent}%)-Highlight-",
            _type=AttachmentType.String,
        )
        # Apparent match distribution plot as attachment
        adp_para_a = Attachment(
            name="Percentage Similarity of the Matched Records",
            _data=percn_matched_para,
            _type=AttachmentType.String,
        )
        adp = Attachment(
            name=None,
            _data=[
                {IMAGE_NAME: Path(p).stem, PATH: p} for p in rel_cdp_saved_file_paths
            ],
            _type=AttachmentType.ImageLinks,
        )

        r_ui_d.add(
            PrivacyScorePacket(
                "Apparent Match Distribution",
                None,
                [
                    amd_para_a,
                    quasi_para_a,
                    quasi_list_atch,
                    rec_mat_para_a,
                    total_quasi_matched,
                    adp_para_a,
                    adp,
                ],
            )
        )
        log.end_msg()

    stable_quasi_identifiers = ["RAC1P", "SEX"]

    can_compute_kdisco = set(stable_quasi_identifiers).issubset(set(ds.features))

    if ds.test != TestDatasetName.sbo_target and can_compute_kdisco:
        # DiSCO Score Attachment
        log.msg("DiSCO Score", level=3)

        disco_evaluator = KDiscoEvaluator(
            gt_df=dataset.d_target_data.copy(),
            syn_df=dataset.d_synthetic_data.copy(),
            stable_identifiers=stable_quasi_identifiers,
            k=2,
            output_directory=os.path.join(r_ui_d.output_directory, "kdisco")
        )
        disco_evaluator.compute_k_disco()

        disco_evaluator.plot_disco_results("barplot")
        disco_evaluator.plot_disco_minus_dio_heatmap("heatmap")
        disco_result_plot_outfile = disco_evaluator.disco_plot_filename
        disco_heatmap_plot_outfile = disco_evaluator.heatmap_plot_filename
        disco_result_csv_outfile = disco_evaluator.disco_result_outfile
        disco_heatmap_csv_outfile = disco_evaluator.disco_heatmap_result_outfile
        disco_para_a = Attachment(
            name=None, _data=disco_explainer_a, _type=AttachmentType.String
        )
        disco_para_b = Attachment(
            name=None, _data=disco_explainer_b, _type=AttachmentType.String
        )
        disco_plot_a = Attachment(
            name=None,
            _data=[
                {IMAGE_NAME: "Disco Bar Plot", PATH: relative_path(disco_result_plot_outfile)},
            ],
            _type=AttachmentType.ImageLinks,
        )
        disco_plot_b = Attachment(
            name=None,
            _data=[{IMAGE_NAME: "Disco Heatmap", PATH: relative_path(disco_heatmap_plot_outfile)}],
            _type=AttachmentType.ImageLinks,
        )

        r_ui_d.add(
            PrivacyScorePacket(
                "DiSCO Privacy Score", None, [disco_para_a, disco_para_b, disco_plot_a, disco_plot_b]
            )
        )
        rd.add(
            "DiSCO",
            {
                "stable_identifiers": disco_evaluator.stable_identifiers,
                "average_disco": disco_evaluator.average_disco(),
                "k": disco_evaluator.k,
                "disco_heatmap_png": relative_path(disco_heatmap_plot_outfile),
                "disco_bar_plot_png": relative_path(disco_result_plot_outfile),
                "disco_result_data": relative_path(disco_result_csv_outfile),
                "disco_heatmap_result_data": relative_path(disco_heatmap_csv_outfile)
            },
        )
        log.end_msg()

    return r_ui_d, rd
