from sdnist.meta_report.common import *

motivation_para = "Is Epsilon 10 weak privacy or strong privacy?  As " \
                  "far as the formal guarantee goes, [something].  " \
                  "But how different algorithms behave on the diverse data is different"

def add_motivation(meta_report_ui_data: ReportUIData, config_name: str):
    m_ui_data = meta_report_ui_data
    attachments = []
    motivation_paras = []
    if config_name == 'e_10':
        from sdnist.meta_report.configs import \
            e_10_motivation_paras as motivation_paras
    # elif config_name == 'tumult':
    #     from sdnist.meta_report.configs import \
    #         tumult_motivation_paras as motivation_paras
    elif config_name == 'sdcmicro_mst_tumult':
        from sdnist.meta_report.configs import \
            sdcmicro_mst_tumult_motivation_paras as motivation_paras
    elif config_name == 'syncity':
        from sdnist.meta_report.configs import \
            syncity_motivation_paras as motivation_paras
    elif config_name == 'sdv_gaussian_copulas':
        from sdnist.meta_report.configs import \
            sdv_gaussian_copulas_motivation_paras as motivation_paras
    elif config_name == 'sdv_ctgan':
        from sdnist.meta_report.configs import \
            sdv_ctgan_motivation_paras as motivation_paras
    elif config_name == 'cbs_nl':
        from sdnist.meta_report.configs import \
            cbs_nl_motivation_paras as motivation_paras
    elif config_name == 'sdv_copulas':
        from sdnist.meta_report.configs import \
            sdv_copulas_motivation_paras as motivation_paras
    # elif config_name == 'mostly_ai':
    #     from sdnist.meta_report.configs import \
    #         mostly_ai_motivation_paras as motivation_paras
    elif config_name == 'blizzard_wizard':
        from sdnist.meta_report.configs import \
            blizzard_wizard_motivation_paras as motivation_paras
    elif config_name == 'community_data':
        from sdnist.meta_report.configs import \
            community_data_motivation_paras as motivation_paras
    elif config_name == 'ccaim':
        from sdnist.meta_report.configs import \
            ccaim_motivation_paras as motivation_paras
    # elif config_name == 'lostinthenoise':
    #     from sdnist.meta_report.configs import \
    #         lostinthenoise_motivation_paras as motivation_paras
    elif config_name == 'sarus':
        from sdnist.meta_report.configs import \
            sarus_motivation_paras as motivation_paras
    elif config_name == 'sdv_copula_blizzard_wizard_community_data':
        from sdnist.meta_report.configs import \
            sdv_copula_blizzard_wizard_community_data_motivation_paras as motivation_paras
    elif config_name == 'sdv_gaussian_copulas_tumult':
        from sdnist.meta_report.configs import \
            sdv_gaussian_copulas_tumult_motivation_paras as motivation_paras
    elif config_name == "sdv":
        from sdnist.meta_report.configs.libraries import \
            sdv_motivation_paras as motivation_paras
    elif config_name == "geneticsd":
        from sdnist.meta_report.configs.libraries import \
            geneticsd_motivation_paras as motivation_paras
    elif config_name == "lostinthenoise":
        from sdnist.meta_report.configs.libraries import \
            lostinthenoise_motivation_paras as motivation_paras
    elif config_name == "sarussdg":
        from sdnist.meta_report.configs.libraries import \
            sarussdg_motivation_paras as motivation_paras
    elif config_name == "mostlyai":
        from sdnist.meta_report.configs.libraries import \
            mostlyai_motivation_paras as motivation_paras
    elif config_name == "rsynthpop":
        from sdnist.meta_report.configs.libraries import \
            rsynthpop_motivation_paras as motivation_paras
    elif config_name == "sdcmicro":
        from sdnist.meta_report.configs.libraries import \
            sdcmicro_motivation_paras as motivation_paras
    elif config_name == "smartnoise":
        from sdnist.meta_report.configs.libraries import \
            smartnoise_motivation_paras as motivation_paras
    elif config_name == "subsample":
        from sdnist.meta_report.configs.libraries import \
            subsample_motivation_paras as motivation_paras
    elif config_name == "synthcity":
        from sdnist.meta_report.configs.libraries import \
            synthcity_motivation_paras as motivation_paras
    elif config_name == "tumult":
        from sdnist.meta_report.configs.libraries import \
            tumult_motivation_paras as motivation_paras
    elif config_name == "custom_1":
        from sdnist.meta_report.configs import \
            custom_1_motivation_paras as motivation_paras

    #  create attachment for each motivation para
    print('Motivations:')
    for m_para in motivation_paras:
        m_a = Attachment(name=None,
                         _data=m_para,
                         _type=AttachmentType.String)
        attachments.append(m_a)
        print(m_para)
        print()

    scr_pck = ScorePacket(metric_name='',
                          attachment=attachments)
    scr_pck.evaluation_type = EvaluationType.Motivation
    m_ui_data.add(scr_pck)