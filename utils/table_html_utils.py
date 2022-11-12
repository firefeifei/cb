from utils import db_utils
from utils.db_utils import get_record, from_db
from utils.html_utils import add_nav_html, default_edit_link_maker
from utils.trade_utils import rebuild_bond_code


def generate_simple_table_html(cur, html, is_login_user=False, edit_link_maker=None):
    table = db_utils.from_db(cur)

    if table.rowcount == 0:
        return html

    return html + build_table_html(table, is_login_user=is_login_user, edit_link_maker=edit_link_maker)


def build_table_html(table, remark_fields=[],
                     remark_strategy_1=lambda name, value: value.startswith('-'),
                     remark_strategy_2=lambda name, value: True,
                     ignore_fields=[],
                     is_login_user=False,
                     field_links={},
                     table_rows_size=10,
                     table_width=None,
                     support_selected_operation=None,  # 对应显示操作名称和后台的操作url. {'name':'删除', 'url', '/delete_selected_bond.html'}
                     head_column_link_maker=None,
                     edit_link_maker=None,
                     ):
    new_remark_fields = ['盈亏', '到期收益率', '溢价率', '可转债涨跌', '正股涨跌']
    new_remark_fields.extend([] if remark_fields is None else remark_fields)
    options = table._get_options({})
    rows = table._get_rows(options)
    table_height_style_content = ''
    if table_width is not None:
        table_height_style_content = 'width: ' + str(table_width)

    if len(rows) > table_rows_size:
        table_height_style_content = ',height: ' + str(50*10) + 'px' #'style:' + str(50*15) + 'px'

    table_height_style = """style=" """ + table_height_style_content + """ " """

    ignore_fields.extend(['nid', 'id', 'hold_id', 'bond_code', 'stock_code', '持有', '持有成本', 'cb_mov2_id', '_sign'])
    lines = []
    linebreak = "<br>"

    lines.append("<div class='outer_table'>")
    lines.append("<div class='inner_table' " + table_height_style + ">")
    lines.append("<form>")
    lines.append("<table>")

    # Headers
    lines.append("    <thead>")
    lines.append("        <tr>")

    for name in table._field_names:
        if ignore_fields.count(name) > 0:
            continue

        lines.append(
            "            <th>%s</th>" % name.replace("\n", linebreak)
        )
    if support_selected_operation is not None:
        lines.append("<th style='width:30px'><a href='#' onclick='delete_selected_bond();return false'>" + support_selected_operation['name'] + "</a></th>")
    lines.append("        </tr>")
    lines.append("    </thead>")

    # Data
    lines.append("    <tbody>")
    # formatted_rows = table._format_rows(rows, options)
    for row in rows:
        lines.append("        <tr>")
        record = get_record(table, row)
        for name, value in record.items():
            if ignore_fields.count(name) > 0:
                continue

            if value is not None:
                value = str(value)
            else:
                value = ''

            remark_color = ''
            if new_remark_fields.count(name) > 0:
                if remark_strategy_1(name, value):
                    remark_color = 'class="remarked-down"'
                elif remark_strategy_2(name, value):
                    remark_color = 'class="remarked-up"'

            if len(field_links) > 0 and id is not None:
                for key, func in field_links.items():
                    if name == key:
                        value = func(value, record)

            prefix, prefix_append, suffix = generate_head_column_html(name, is_login_user, record,
                                                                      head_column_link_maker=head_column_link_maker,
                                                                      edit_link_maker=edit_link_maker)
            if prefix is None and prefix_append is None and suffix is None:
                continue

            if name == '名称':
                bond_code = record.get('bond_code')
                if bond_code.startswith('123'):
                    value = '<font color=red>*</font>' + value

            lines.append(
                ("            <td " + remark_color + ">" + prefix + "{}" + prefix_append + "" + suffix + "</td>").format(value.replace("\n", linebreak)
                # fixme 重构成函数变量
                .replace('转债标的 ', '')
                .replace('标准普尔 ', '')
                .replace('富时罗素 ', '')
                .replace('上证380 ', '')
                .replace('央视50_ ', '')
                .replace('中证500 ', '')
                .replace('深成500 ', '')
                .replace('融资融券 ', '')
                .replace('上证180_ ', '')
                .replace('HS300_ ', '')
                .replace('MSCI中国 ', '')
                .replace('深股通 ', '')
                .replace('创业板综 ', '')
                .replace('沪股通 ', '')
                ))
        if support_selected_operation is not None:
            lines.append("        <td><input type='checkbox' name='select_bond' value='" + str(record.get('id')) + "'></td>")
        lines.append("        </tr>")
    lines.append("    </tbody>")
    lines.append("</table>")
    lines.append("</form>")
    lines.append("</div>")
    lines.append("</div>")
    if support_selected_operation is not None:
        lines.append("""
            <script  type="text/javascript">        
                function delete_selected_bond(){
                    if (confirm("确认要删除选中的选项?")){
                        var id_array=new Array(); 
                        $("input[name='select_bond']:checked").each(function(){  
                            id_array.push($(this).val());//向数组中添加元素  
                        });  
                        var ids=id_array.join(',');//将数组元素连接起来以构建一个字符串
                        $.get(\"""" + support_selected_operation['url'] + """/"+ids+"/", function(data, status){
                            if (status == 'success'){
                                alert("操作成功!")
                                // 删除页面元素
                                $("input[name='select_bond']:checked").each(function(){  
                                    $(this)[0].parentElement.parentElement.remove()
                                }); 
                            }else{
                                alert("服务端操作异常.")
                            }
                        })  
                    }
                }
            </script>
        """)

    return "\n".join(lines)


def generate_table_html(type, cur, html, need_title=True, ext_field_names=None, rows=None,
                        remark_fields=[],
                        nav_html_list=None,
                        tables=None,
                        subtitle='',
                        ignore_fields=[],
                        field_links={},
                        is_login_user=False,
                        head_column_link_maker=None):
    table, html = generate_table_html_with_data(type, cur, html, need_title, ext_field_names, rows,
                                                remark_fields, nav_html_list, tables, subtitle, ignore_fields,
                                                field_links, is_login_user,
                                                head_column_link_maker=head_column_link_maker)
    return html


def generate_table_html_with_data(type, cur, html, need_title=True, ext_field_names=None, rows=None,
                                  remark_fields=[],
                                  nav_html_list=None,
                                  tables=None,
                                  subtitle='',
                                  ignore_fields=[],
                                  field_links={},
                                  is_login_user=False,
                                  table_width=None,
                                  head_column_link_maker=None
                                  ):

    table = from_db(cur, ext_field_names, rows)

    if table.rowcount == 0:
        return table, html

    if tables is not None:
        tables[type] = table

    add_nav_html(nav_html_list, type)

    title = ''
    title_suffix = ''
    if need_title:
        # 首行加两个换行, 避免被但导航栏遮挡
        title = """
            <div id=\"""" + type + """\">""" + """
                <br><br><center><font size='4'><b> =========""" + type + """=========</b></font></center>""" \
               + ('' if len(subtitle) == 0 else """<center> """ + subtitle + """</center>""") + """<br>"""
        title_suffix = """</div>"""

    return table, html + title + \
           build_table_html(table, remark_fields, ignore_fields=ignore_fields,
                            is_login_user=is_login_user, field_links=field_links, table_width=table_width,
                            head_column_link_maker=head_column_link_maker) + \
           title_suffix


def generate_head_column_html(field, is_login_user, record, head_column_link_maker=None,
                              edit_link_maker=None):
    # 标题增加链接
    # 可转债: https://quote.eastmoney.com/bond/sz128051.html
    # 正股: https://quote.eastmoney.com/sz002741.html
    prefix = ''
    prefix_append = ''
    suffix = ''
    if head_column_link_maker is not None and head_column_link_maker(record, field) is not None:
        return "<a href='" + head_column_link_maker(record, field) + "'>", "</a>", ""
    elif field == '名称':
        bond_code = record.get('bond_code')
        if bond_code is None:
            return None, None, None
        new_bond_code = rebuild_bond_code(bond_code)
        nid = record['nid']
        stock_code = record['stock_code']
        market = 'sz'
        if bond_code.startswith('11'):
            market = 'sh'
        prefix = "<a href = 'javascript:void(0)' onclick=\"popWin.showWin('1200','600', '" + new_bond_code +"');return false\"" + ">"

        prefix_append += "</a>&nbsp;<a target='_blank' href='http://www.ninwin.cn/index.php?m=cb&c=detail&a=detail&id=" + str(
            nid) + "'><img src='/static/img/nw.png' alt='宁稳网' title='宁稳网查看转债信息' width='14' height='14' class='site-link'/></a>"

        prefix_append += "&nbsp;<a target = '_blank' href = 'https://xueqiu.com/S/" + market + bond_code + "'><img src='/static/img/xueqiu.png' alt='雪球' title='雪球查看转债讨论' width='14' height='14' class='site-link'/></a>"

        # https://xueqiu.com/S/SH600998
        suffix = "<br/>"
        if stock_code is not None:
            suffix += "<a target='_blank' href='https://quote.eastmoney.com/" + market + stock_code + ".html'><img src='/static/img/eastmoney.png' alt='东方财富' title='东方财富查看正股信息' width='14' height='14' class='next-site-link'/></a> "
            suffix += "<a target='_blank' href='http://doctor.10jqka.com.cn/" + stock_code + "/'><img src='/static/img/ths.png' alt='同花顺' title='同花顺正股诊断' width='14' height='14' class='next-site-link'/></a>"

        # http://www.ninwin.cn/index.php?m=cb&c=graph_k&a=graph_k&id=157
        suffix += "&nbsp;<a target='_blank' href='http://www.ninwin.cn/index.php?m=cb&c=graph_k&a=graph_k&id=" + str(
            nid) + "'><img src='/static/img/trend.png' alt='走势图' title='宁稳网查看转债&正股走势(非会员20次/天)' width='14' height='14' class='next-site-link'/></a>"

        if is_login_user:
            hold_id = record.get('hold_id', None)
            id = record.get('id', None)
            if edit_link_maker is None:
                edit_link_maker = default_edit_link_maker

            suffix += edit_link_maker(id, hold_id, bond_code)
            suffix += "&nbsp;<a href='/view_my_trade_history.html/"+bond_code+"/'><img src='/static/img/detail.png' alt='交易明细' title='交易明细' width='14' height='14' class='next-site-link'/></a>"
    return prefix, prefix_append, suffix