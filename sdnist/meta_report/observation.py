from sdnist.meta_report.common import *

observation_para = "" \
                  "<ul style=\"margin-top:0px\"><li>" \
                  "<b>Family Focused Correlations:</b> See that these features a" \
                  "re challenging for some approaches but not others.</li>" \
                  "<li><b>Industry Focused Correlations:</b> Even though this is a " \
                  "larger data space, see that.</li>" \
                  "<li><b>Simple DP Histogram:</b>  See that it looks like poor " \
                  "correlations, high privacy, but it's also low privacy.</li>" \
                  "</ul>"

def add_observation(meta_report_ui_data: ReportUIData, config_name: str):
    m_ui_data = meta_report_ui_data
    attachments = []

    observations_paras = []
    if config_name == 'e_10':
        from sdnist.meta_report.configs import \
            e_10_observation_paras as observations_paras
    elif config_name == 'tumult':
        from sdnist.meta_report.configs import \
            tumult_observation_paras as observations_paras
    elif config_name == 'sdcmicro_mst_tumult':
        from sdnist.meta_report.configs import \
            sdcmicro_mst_tumult_observation_paras as observations_paras
    elif config_name == 'syncity':
        from sdnist.meta_report.configs import \
            syncity_observation_paras as observations_paras
    elif config_name == 'sdv_gaussian_copulas':
        from sdnist.meta_report.configs import \
            sdv_gaussian_copulas_observation_paras as observations_paras
    elif config_name == 'sdv_ctgan':
        from sdnist.meta_report.configs import \
            sdv_ctgan_observation_paras as observations_paras
    elif config_name == 'cbs_nl':
        from sdnist.meta_report.configs import \
            cbs_nl_observation_paras as observations_paras
    elif config_name == 'sdv_copulas':
        from sdnist.meta_report.configs import \
            sdv_copulas_observation_paras as observations_paras
    elif config_name == 'mostly_ai':
        from sdnist.meta_report.configs import \
            mostly_ai_observation_paras as observations_paras
    elif config_name == 'blizzard_wizard':
        from sdnist.meta_report.configs import \
            blizzard_wizard_observation_paras as observations_paras
    elif config_name == 'community_data':
        from sdnist.meta_report.configs import \
            community_data_observation_paras as observations_paras
    elif config_name == 'ccaim':
        from sdnist.meta_report.configs import \
            ccaim_observation_paras as observations_paras
    elif config_name == 'lostinthenoise':
        from sdnist.meta_report.configs import \
            lostinthenoise_observation_paras as observations_paras
    elif config_name == 'sarus':
        from sdnist.meta_report.configs import \
            sarus_observation_paras as observations_paras

    #  create attachment for each observations para
    for m_para in observations_paras:
        m_a = Attachment(name=None,
                         _data=m_para,
                         _type=AttachmentType.String)
        attachments.append(m_a)

    scr_pck = ScorePacket(metric_name='',
                              attachment=attachments)
    scr_pck.evaluation_type = EvaluationType.Observations
    m_ui_data.add(scr_pck)