from sdnist.metareport.common import *


def add_data_dict(data_dict: Dict,
                  m_ui_d: ReportUIData,
                  density_bins_description: Dict):
    # create data dictionary appendix attachments
    dd_as = []
    id_cnt = 0

    for feat in data_dict.keys():
        a_group_id = id_cnt
        id_cnt += 1
        f_desc = data_dict[feat]['description']
        feat_title = f'{feat}: {f_desc}'
        if 'link' in data_dict[feat] and feat == 'INDP':
            data = f"<a href={data_dict[feat]['link']}>" \
                   f"See codes in ACS data dictionary.</a> " \
                   f"Find codes by searching the string: {feat}, in " \
                   f"the ACS data dictionary"
            dd_as.append(Attachment(name=feat_title,
                                    _data=data,
                                    group_id=a_group_id,
                                    _type=AttachmentType.String))

        elif 'values' in data_dict[feat]:
            data = [{f"{feat} Code": k,
                     f"Code Description": v}
                for k, v in data_dict[feat]['values'].items()
            ]
            f_name = feat_title
            if 'link' in data_dict[feat] and feat in ['WGTP', 'PWGTP']:
                s_data = f"<a href={data_dict[feat]['link']}>" \
                       f"See description of weights.</a>"
                dd_as.append(Attachment(name=f_name,
                                        _data=s_data,
                                        group_id=a_group_id,
                                        _type=AttachmentType.String))
                f_name = None
            dd_as.append(Attachment(name=f_name,
                                    _data=data,
                                    group_id=a_group_id,
                                    _type=AttachmentType.Table))
            if feat == 'DENSITY':
                for bin, bdata in density_bins_description.items():
                    bdc = bdata[1].columns.tolist()  # bin data columns
                    # report bin data: bin data format for report
                    rbd = [{c: row[j] for j, c in enumerate(bdc)}
                           for i, row in bdata[1].iterrows()]
                    dd_as.append(Attachment(name=None,
                                            _data=f'<b>Density Bin: {bin} | Bin Range: {bdata[0]}</b>',
                                            group_id=a_group_id,
                                            _type=AttachmentType.String))
                    dd_as.append(Attachment(name=None,
                                            _data=rbd,
                                            group_id=a_group_id,
                                            _type=AttachmentType.Table))

    m_ui_d.add(ScorePacket(metric_name='Data Dictionary',
                           score=None,
                           attachment=dd_as))