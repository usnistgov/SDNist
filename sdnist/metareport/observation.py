from sdnist.metareport.common import *

observation_para = "" \
                  "<ul style=\"margin-top:0px\"><li>" \
                  "<b>Family Focused Correlations:</b> See that these features a" \
                  "re challenging for some approaches but not others.</li>" \
                  "<li><b>Industry Focused Correlations:</b> Even though this is a " \
                  "larger data space, see that.</li>" \
                  "<li><b>Simple DP Histogram:</b>  See that it looks like poor " \
                  "correlations, high privacy, but it's also low privacy.</li>" \
                  "</ul>"


def add_observation(metareport_ui_data: ReportUIData, config_name: str):
    m_ui_data = metareport_ui_data
    attachments = []

    observations_paras = []
    if config_name == 'e_10':
        from sdnist.metareport.configs import \
            e_10_observation_paras as observations_paras
    # elif config_name == 'tumult':
    #     from sdnist.metareport.configs import \
    #         tumult_observation_paras as observations_paras
    elif config_name == 'sdcmicro_mst_tumult':
        from sdnist.metareport.configs import \
            sdcmicro_mst_tumult_observation_paras as observations_paras
    elif config_name == 'syncity':
        from sdnist.metareport.configs import \
            syncity_observation_paras as observations_paras
    elif config_name == 'sdv_gaussian_copulas':
        from sdnist.metareport.configs import \
            sdv_gaussian_copulas_observation_paras as observations_paras
    elif config_name == 'sdv_ctgan':
        from sdnist.metareport.configs import \
            sdv_ctgan_observation_paras as observations_paras
    elif config_name == 'cbs_nl':
        from sdnist.metareport.configs import \
            cbs_nl_observation_paras as observations_paras
    elif config_name == 'sdv_copulas':
        from sdnist.metareport.configs import \
            sdv_copulas_observation_paras as observations_paras
    # elif config_name == 'mostly_ai':
    #     from sdnist.metareport.configs import \
    #         mostly_ai_observation_paras as observations_paras
    elif config_name == 'blizzard_wizard':
        from sdnist.metareport.configs import \
            blizzard_wizard_observation_paras as observations_paras
    elif config_name == 'community_data':
        from sdnist.metareport.configs import \
            community_data_observation_paras as observations_paras
    elif config_name == 'ccaim':
        from sdnist.metareport.configs import \
            ccaim_observation_paras as observations_paras
    # elif config_name == 'lostinthenoise':
    #     from sdnist.metareport.configs import \
    #         lostinthenoise_observation_paras as observations_paras
    elif config_name == 'sarus':
        from sdnist.metareport.configs import \
            sarus_observation_paras as observations_paras
    elif config_name == 'sdv_copula_blizzard_wizard_community_data':
        from sdnist.metareport.configs import \
            sdv_copula_blizzard_wizard_community_data_observation_paras as observations_paras
    elif config_name == "sdv":
        from sdnist.metareport.configs.libraries import \
            sdv_observation_paras as observations_paras
    elif config_name == "geneticsd":
        from sdnist.metareport.configs.libraries import \
            geneticsd_observation_paras as observations_paras
    elif config_name == "lostinthenoise":
        from sdnist.metareport.configs.libraries import \
            lostinthenoise_observation_paras as observations_paras
    elif config_name == "sarussdg":
        from sdnist.metareport.configs.libraries import \
            sarussdg_observation_paras as observations_paras
    elif config_name == "mostlyai":
        from sdnist.metareport.configs.libraries import \
            mostlyai_observation_paras as observations_paras
    elif config_name == "rsynthpop":
        from sdnist.metareport.configs.libraries import \
            rsynthpop_observation_paras as observations_paras
    elif config_name == "sdcmicro":
        from sdnist.metareport.configs.libraries import \
            sdcmicro_observation_paras as observations_paras
    elif config_name == "smartnoise":
        from sdnist.metareport.configs.libraries import \
            smartnoise_observation_paras as observations_paras
    elif config_name == "subsample":
        from sdnist.metareport.configs.libraries import \
            subsample_observation_paras as observations_paras
    elif config_name == "synthcity":
        from sdnist.metareport.configs.libraries import \
            synthcity_observation_paras as observations_paras
    elif config_name == "tumult":
        from sdnist.metareport.configs.libraries import \
            tumult_observation_paras as observations_paras
    elif config_name == "custom_1":
        from sdnist.metareport.configs import \
            custom_1_observation_paras as observations_paras
    elif config_name == "anonossdk":
        from sdnist.metareport.configs.libraries import \
            anonossdk_observation_paras as observations_paras
    elif config_name == "ydata":
        from sdnist.metareport.configs.libraries import \
            ydata_observation_paras as observations_paras
    elif config_name == "aim":
        from sdnist.metareport.configs.libraries import \
            aim_observation_paras as observations_paras
    elif config_name == 'ydata_synthetic':
        from sdnist.metareport.configs.libraries import \
            ydata_synth_observation_paras as observations_paras
    elif config_name == 'smote':
        from sdnist.metareport.configs.libraries import \
            smote_observation_paras as observations_paras
    elif config_name == 'aim_msp':
        from sdnist.metareport.configs.libraries import \
            aim_mst_observation_paras as observations_paras


    print('Observations')
    #  create attachment for each observations para
    for m_para in observations_paras:
        m_a = Attachment(name=None,
                         _data=m_para,
                         _type=AttachmentType.String)
        attachments.append(m_a)
        print(m_para)
        print()

    scr_pck = ScorePacket(metric_name='',
                              attachment=attachments)
    scr_pck.evaluation_type = EvaluationType.Observations
    m_ui_data.add(scr_pck)