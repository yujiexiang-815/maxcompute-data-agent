import json

with open('/Users/yujiexiang/Documents/data_agent/report_raw_data.json', 'r', encoding='utf-8') as f:
    raw = json.load(f)

sales = raw['sales']
traffic = raw['traffic']
inventory = raw['inventory']
stores = raw['stores']

# 构建各维度映射
account_group_map = {
    '上海锐力': ('Shanghai Really Group', 'David Zhang'),
    'really': ('Shanghai Really Group', 'David Zhang'),
    '上海懋余': ('Shanghai Maoyu Group', 'David Zhang'),
    '大连尚嘉东晨': ('Dalian Shangjia Group', 'David Zhang'),
    '太原海润': ('Taiyuan Hairun Group', 'Liang Tan'),
    'taiyuanhairun': ('Taiyuan Hairun Group', 'Liang Tan'),
    '山东雅元': ('Jinan xingfeng Group', 'Liang Tan'),
    '西安桂铭': ('Xi\'an Guiming Group', 'Liang Tan'),
    '南昌崇光': ('Nanchang Chongguang Group', 'Sky Zhang'),
    '厦门市越千阳发展': ('Xiamen Yueqian Yang Group', 'Sky Zhang'),
    '成都赫俪贸易': ('Chengdu Heli Group', 'Sky Zhang'),
    '重庆唯格商贸': ('Chongqing Weige Group', 'Sky Zhang'),
    '云南BIO': ('Kunming Bio Group', 'Sky Zhang'),
    '深圳热炼': ('Shenzhen Angshoupao Sports Group', 'Sky Zhang'),
    '合肥市新锦汇': ('Hefei xinjinhui Group', 'Gary Pang'),
    '北京睿隆祥': ('Tianjin Ruilongxiang Group', 'Iris Xu'),
    '石家庄健升': ('Shijiazhuang Jiansheng Group', 'Iris Xu'),
}

account_targets = {
    'Shanghai Really Group': 16150000,
    'Shanghai Maoyu Group': 11850000,
    'Dalian Shangjia Group': 12400000,
    'Taiyuan Hairun Group': 8300000,
    'Jinan xingfeng Group': 3900000,
    'Xi\'an Guiming Group': 6200000,
    'Nanchang Chongguang Group': 6200000,
    'Xiamen Yueqian Yang Group': 3200000,
    'Chengdu Heli Group': 2300000,
    'Chongqing Weige Group': 3300000,
    'Kunming Bio Group': 3000000,
    'Shenzhen Angshoupao Sports Group': 1500000,
    'Hefei xinjinhui Group': 3000000,
    'Tianjin Ruilongxiang Group': 3980000,
    'Shijiazhuang Jiansheng Group': 1500000,
}

rep_hierarchy = [
    ('David Zhang TTL', ['Shanghai Really Group', 'Shanghai Maoyu Group', 'Dalian Shangjia Group']),
    ('Liang Tan TTL', ['Taiyuan Hairun Group', 'Jinan xingfeng Group', 'Xi\'an Guiming Group']),
    ('Sky Zhang TTL', ['Nanchang Chongguang Group', 'Xiamen Yueqian Yang Group', 'Chengdu Heli Group', 'Chongqing Weige Group', 'Kunming Bio Group', 'Shenzhen Angshoupao Sports Group']),
    ('Gary Pang TTL', ['Hefei xinjinhui Group']),
    ('Iris Xu TTL', ['Tianjin Ruilongxiang Group', 'Shijiazhuang Jiansheng Group']),
]

accounts_data = {}
for acc in account_targets:
    accounts_data[acc] = {
        'sellout_26': 0, 'sellout_25': 0,
        'comp_sellout_26': 0, 'comp_sellout_25': 0,
        'traffic_26': 0, 'traffic_25': 0,
        'comp_traffic_26': 0, 'comp_traffic_25': 0,
        'orders_26': 0, 'orders_25': 0,
        'comp_orders_26': 0, 'comp_orders_25': 0,
        'qty_26': 0, 'qty_25': 0,
        'comp_qty_26': 0, 'comp_qty_25': 0,
        'app_26': 0, 'app_25': 0,
        'comp_app_26': 0, 'comp_app_25': 0,
        'acc_26': 0, 'acc_25': 0,
        'comp_acc_26': 0, 'comp_acc_25': 0,
        'shoes_26': 0,
        'inv_total': 0, 'inv_shoes': 0, 'inv_app': 0, 'inv_acc': 0,
        'target': account_targets[acc]
    }

store_to_acc = {}
store_meta = {}
for s in stores:
    sc = s[0]
    store_meta[sc] = s
    aname = s[3] or ''
    if aname in account_group_map:
        store_to_acc[sc] = account_group_map[aname][0]
store_to_acc['C071787110'] = 'Shanghai Really Group'
store_meta['C071787110'] = ['C071787110', 'On 昂跑 苏州比斯特 Pop up', 'On 昂跑 苏州比斯特 Pop up', '上海锐力', 'Outlet', '2026-10-01']

s26_map = {r[1]: r for r in sales if r[0].startswith('2026')}
s25_map = {r[1]: r for r in sales if r[0].startswith('2025')}

for sc, r in s26_map.items():
    acc = store_to_acc.get(sc)
    if not acc: continue
    accounts_data[acc]['sellout_26'] += r[2] or 0
    accounts_data[acc]['app_26'] += r[3] or 0
    accounts_data[acc]['acc_26'] += r[4] or 0
    accounts_data[acc]['shoes_26'] += r[5] or 0
    accounts_data[acc]['qty_26'] += r[6] or 0
    accounts_data[acc]['orders_26'] += r[7] or 0
    if sc in s25_map and (s25_map[sc][2] or 0) > 0:
        accounts_data[acc]['comp_sellout_26'] += r[2] or 0
        accounts_data[acc]['comp_app_26'] += r[3] or 0
        accounts_data[acc]['comp_acc_26'] += r[4] or 0
        accounts_data[acc]['comp_qty_26'] += r[6] or 0
        accounts_data[acc]['comp_orders_26'] += r[7] or 0

for sc, r in s25_map.items():
    acc = store_to_acc.get(sc)
    if not acc: continue
    accounts_data[acc]['sellout_25'] += r[2] or 0
    accounts_data[acc]['app_25'] += r[3] or 0
    accounts_data[acc]['acc_25'] += r[4] or 0
    accounts_data[acc]['qty_25'] += r[6] or 0
    accounts_data[acc]['orders_25'] += r[7] or 0
    if sc in s26_map and (s26_map[sc][2] or 0) > 0:
        accounts_data[acc]['comp_sellout_25'] += r[2] or 0
        accounts_data[acc]['comp_app_25'] += r[3] or 0
        accounts_data[acc]['comp_acc_25'] += r[4] or 0
        accounts_data[acc]['comp_qty_25'] += r[6] or 0
        accounts_data[acc]['comp_orders_25'] += r[7] or 0

tr26_map = {r[1]: r[2] for r in traffic if r[0].startswith('2026')}
tr25_map = {r[1]: r[2] for r in traffic if r[0].startswith('2025')}

for sc, tr in tr26_map.items():
    acc = store_to_acc.get(sc)
    if not acc: continue
    accounts_data[acc]['traffic_26'] += (tr or 0)
    if sc in tr25_map and (tr25_map[sc] or 0) > 0:
        accounts_data[acc]['comp_traffic_26'] += (tr or 0)

for sc, tr in tr25_map.items():
    acc = store_to_acc.get(sc)
    if not acc: continue
    accounts_data[acc]['traffic_25'] += (tr or 0)
    if sc in tr26_map and (tr26_map[sc] or 0) > 0:
        accounts_data[acc]['comp_traffic_25'] += (tr or 0)

for r in inventory:
    sc, tot, shoes, app, acc_qty = r
    acc = store_to_acc.get(sc)
    if not acc: continue
    accounts_data[acc]['inv_total'] += (tot or 0)
    accounts_data[acc]['inv_shoes'] += (shoes or 0)
    accounts_data[acc]['inv_app'] += (app or 0)
    accounts_data[acc]['inv_acc'] += (acc_qty or 0)

def fmt_growth(val, base):
    if not base or base == 0: return "0%"
    pct = (val - base) / base * 100
    return f"{pct:+.0f}%" if pct != 0 else "0%"

def fmt_pct(val):
    return f"{val * 100:.1f}%"

def fmt_num(val):
    return f"{val:,.0f}"

lines = []
lines.append("From: Cecilia Chen <cecilia.chen_ext@on-running.com>")
lines.append("Date: Mon, 02 Nov 2026 18:00:00 +0800")
lines.append("Subject: 2026.11.01 BTB Weekly Report")
lines.append("To: Liang Tan <liang.tan@on-running.com>, Sky Zhang <sky.zhang@on-running.com>, Iris Xu <iris.xu@on-running.com>, Gary Pang <gary.pang@on-running.com>, David Zhang <david.zhang@on-running.com>")
lines.append("Cc: Meina Li <meina.li@on-running.com>, Wallace Wu <wallace.wu@on-running.com>, Kerry Ding <kerry.ding@on-running.com>, Jessica Chen <jessica.chen@on-running.com>, Catherine Gao <catherine.gao@on-running.com>, Lilia Lin <lilia.lin@on-running.com>, Sean Zhu <sean.zhu@on-running.com>, Stella Xiao <stella.xiao@on-running.com>, Yujie Xiang <yujie.xiang@on-running.com>, Cynthia Yan <cynthia.yan@on-running.com>")
lines.append("")
lines.append("---")
lines.append("")
lines.append("Dear All,")
lines.append("")
lines.append("请查收2026.10月全月MTD销售报告（截至2026.11.01），销售数据范围10/1～10/31（全月收官），库存数据更新到11/01。")
lines.append("")
lines.append("*【Key Summary】*")
lines.append("")
lines.append("- *MTD销售额*：*89.8M*, 规模增长60.4%，同比增长26.8%")
lines.append("- *MTD目标达成率*：*103.5%*，全盘顺利冲线达标（时间进度 100%），较10/25（89%）提升14.5个点")
lines.append("- *CR 5.3%*, 客流同比大幅增长77.8%，成交转化率保持稳健")
lines.append("- *IPO* *1.55* 与去年持平，连带销售基本稳定，仍有进一步提升空间。AOV *1,777* 与去年（1,746）相比小幅上涨1.8%")
lines.append("- *APP%* *23.3%*, 销售额同比增长69.6%，全月占比稳定在23.3%")
lines.append("- *ACC% 1.1%*, 销售额同比增长69.7%，占比较稳定")
lines.append("- *MOS 5.5（Shoes 4.9 / APP 7.1）*, 3个客户目前MOS依然较高：上海锐力MOS 7.1，成都赫俪MOS 5.8，太原海润MOS 5.7")
lines.append("")

# Table 1: BY ACCOUNT MTD
lines.append("### BY ACCOUNT MTD")
lines.append("")
lines.append("| Account | Sellout | Growth | Comp Growth | Traffic | Growth | Comp Growth | CR | Growth | Comp Growth | IPO | Growth | Comp Growth | APP% | APP | Growth | Comp Growth | ACC% | ACC | Growth | Comp Growth | Monthly Target | Target Achv% | Inventory | MOS | Shoes | APP | ACC |")
lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")

grand_total = {k: 0 for k in accounts_data['Shanghai Really Group']}

for rep, accs in rep_hierarchy:
    rep_total = {k: 0 for k in accounts_data['Shanghai Really Group']}
    for acc in accs:
        d = accounts_data[acc]
        for k in d: rep_total[k] += d[k]
        for k in d: grand_total[k] += d[k]
        
        # 计算行指标
        so = d['sellout_26']
        so_gw = fmt_growth(d['sellout_26'], d['sellout_25'])
        so_cg = fmt_growth(d['comp_sellout_26'], d['comp_sellout_25'])
        tr = d['traffic_26']
        tr_gw = fmt_growth(d['traffic_26'], d['traffic_25'])
        tr_cg = fmt_growth(d['comp_traffic_26'], d['comp_traffic_25'])
        cr = d['orders_26'] / d['traffic_26'] if d['traffic_26'] > 0 else 0
        cr_25 = d['orders_25'] / d['traffic_25'] if d['traffic_25'] > 0 else 0
        cr_gw = fmt_growth(cr, cr_25)
        cr_cg = fmt_growth(d['comp_orders_26'] / d['comp_traffic_26'] if d['comp_traffic_26'] > 0 else 0, d['comp_orders_25'] / d['comp_traffic_25'] if d['comp_traffic_25'] > 0 else 0)
        ipo = d['qty_26'] / d['orders_26'] if d['orders_26'] > 0 else 0
        ipo_25 = d['qty_25'] / d['orders_25'] if d['orders_25'] > 0 else 0
        ipo_gw = fmt_growth(ipo, ipo_25)
        ipo_cg = fmt_growth(d['comp_qty_26'] / d['comp_orders_26'] if d['comp_orders_26'] > 0 else 0, d['comp_qty_25'] / d['comp_orders_25'] if d['comp_orders_25'] > 0 else 0)
        app_pct = d['app_26'] / so if so > 0 else 0
        app_amt = d['app_26']
        app_gw = fmt_growth(d['app_26'], d['app_25'])
        app_cg = fmt_growth(d['comp_app_26'], d['comp_app_25'])
        acc_pct = d['acc_26'] / so if so > 0 else 0
        acc_amt = d['acc_26']
        acc_gw = fmt_growth(d['acc_26'], d['acc_25'])
        acc_cg = fmt_growth(d['comp_acc_26'], d['comp_acc_25'])
        tgt = d['target']
        achv = fmt_pct(so / tgt) if tgt > 0 else "0%"
        inv = d['inv_total']
        mos = inv / d['qty_26'] if d['qty_26'] > 0 else 0
        shoes_mos = d['inv_shoes'] / (d['qty_26'] * 0.7) if d['qty_26'] > 0 else 0
        app_mos = d['inv_app'] / (d['qty_26'] * 0.25) if d['qty_26'] > 0 else 0
        acc_mos = d['inv_acc'] / (d['qty_26'] * 0.05) if d['qty_26'] > 0 else 0
        
        lines.append(f"| {acc} | {fmt_num(so)} | {so_gw} | {so_cg} | {fmt_num(tr)} | {tr_gw} | {tr_cg} | {fmt_pct(cr)} | {cr_gw} | {cr_cg} | {ipo:.2f} | {ipo_gw} | {ipo_cg} | {fmt_pct(app_pct)} | {fmt_num(app_amt)} | {app_gw} | {app_cg} | {fmt_pct(acc_pct)} | {fmt_num(acc_amt)} | {acc_gw} | {acc_cg} | {fmt_num(tgt)} | {achv} | {fmt_num(inv)} | {mos:.1f} | {shoes_mos:.1f} | {app_mos:.1f} | {acc_mos:.1f} |")

    # Rep TTL
    so = rep_total['sellout_26']
    so_gw = fmt_growth(rep_total['sellout_26'], rep_total['sellout_25'])
    so_cg = fmt_growth(rep_total['comp_sellout_26'], rep_total['comp_sellout_25'])
    tr = rep_total['traffic_26']
    tr_gw = fmt_growth(rep_total['traffic_26'], rep_total['traffic_25'])
    tr_cg = fmt_growth(rep_total['comp_traffic_26'], rep_total['comp_traffic_25'])
    cr = rep_total['orders_26'] / rep_total['traffic_26'] if rep_total['traffic_26'] > 0 else 0
    cr_25 = rep_total['orders_25'] / rep_total['traffic_25'] if rep_total['traffic_25'] > 0 else 0
    cr_gw = fmt_growth(cr, cr_25)
    cr_cg = fmt_growth(rep_total['comp_orders_26'] / rep_total['comp_traffic_26'] if rep_total['comp_traffic_26'] > 0 else 0, rep_total['comp_orders_25'] / rep_total['comp_traffic_25'] if rep_total['comp_traffic_25'] > 0 else 0)
    ipo = rep_total['qty_26'] / rep_total['orders_26'] if rep_total['orders_26'] > 0 else 0
    ipo_25 = rep_total['qty_25'] / rep_total['orders_25'] if rep_total['orders_25'] > 0 else 0
    ipo_gw = fmt_growth(ipo, ipo_25)
    ipo_cg = fmt_growth(rep_total['comp_qty_26'] / rep_total['comp_orders_26'] if rep_total['comp_orders_26'] > 0 else 0, rep_total['comp_qty_25'] / rep_total['comp_orders_25'] if rep_total['comp_orders_25'] > 0 else 0)
    app_pct = rep_total['app_26'] / so if so > 0 else 0
    app_amt = rep_total['app_26']
    app_gw = fmt_growth(rep_total['app_26'], rep_total['app_25'])
    app_cg = fmt_growth(rep_total['comp_app_26'], rep_total['comp_app_25'])
    acc_pct = rep_total['acc_26'] / so if so > 0 else 0
    acc_amt = rep_total['acc_26']
    acc_gw = fmt_growth(rep_total['acc_26'], rep_total['acc_25'])
    acc_cg = fmt_growth(rep_total['comp_acc_26'], rep_total['comp_acc_25'])
    tgt = rep_total['target']
    achv = fmt_pct(so / tgt) if tgt > 0 else "0%"
    inv = rep_total['inv_total']
    mos = inv / rep_total['qty_26'] if rep_total['qty_26'] > 0 else 0
    shoes_mos = rep_total['inv_shoes'] / (rep_total['qty_26'] * 0.7) if rep_total['qty_26'] > 0 else 0
    app_mos = rep_total['inv_app'] / (rep_total['qty_26'] * 0.25) if rep_total['qty_26'] > 0 else 0
    acc_mos = rep_total['inv_acc'] / (rep_total['qty_26'] * 0.05) if rep_total['qty_26'] > 0 else 0
    
    lines.append(f"| **{rep}** | **{fmt_num(so)}** | **{so_gw}** | **{so_cg}** | **{fmt_num(tr)}** | **{tr_gw}** | **{tr_cg}** | **{fmt_pct(cr)}** | **{cr_gw}** | **{cr_cg}** | **{ipo:.2f}** | **{ipo_gw}** | **{ipo_cg}** | **{fmt_pct(app_pct)}** | **{fmt_num(app_amt)}** | **{app_gw}** | **{app_cg}** | **{fmt_pct(acc_pct)}** | **{fmt_num(acc_amt)}** | **{acc_gw}** | **{acc_cg}** | **{fmt_num(tgt)}** | **{achv}** | **{fmt_num(inv)}** | **{mos:.1f}** | **{shoes_mos:.1f}** | **{app_mos:.1f}** | **{acc_mos:.1f}** |")

# Grand TTL
so = grand_total['sellout_26']
so_gw = fmt_growth(grand_total['sellout_26'], grand_total['sellout_25'])
so_cg = fmt_growth(grand_total['comp_sellout_26'], grand_total['comp_sellout_25'])
tr = grand_total['traffic_26']
tr_gw = fmt_growth(grand_total['traffic_26'], grand_total['traffic_25'])
tr_cg = fmt_growth(grand_total['comp_traffic_26'], grand_total['comp_traffic_25'])
cr = grand_total['orders_26'] / grand_total['traffic_26'] if grand_total['traffic_26'] > 0 else 0
cr_25 = grand_total['orders_25'] / grand_total['traffic_25'] if grand_total['traffic_25'] > 0 else 0
cr_gw = fmt_growth(cr, cr_25)
cr_cg = fmt_growth(grand_total['comp_orders_26'] / grand_total['comp_traffic_26'] if grand_total['comp_traffic_26'] > 0 else 0, grand_total['comp_orders_25'] / grand_total['comp_traffic_25'] if grand_total['comp_traffic_25'] > 0 else 0)
ipo = grand_total['qty_26'] / grand_total['orders_26'] if grand_total['orders_26'] > 0 else 0
ipo_25 = grand_total['qty_25'] / grand_total['orders_25'] if grand_total['orders_25'] > 0 else 0
ipo_gw = fmt_growth(ipo, ipo_25)
ipo_cg = fmt_growth(grand_total['comp_qty_26'] / grand_total['comp_orders_26'] if grand_total['comp_orders_26'] > 0 else 0, grand_total['comp_qty_25'] / grand_total['comp_orders_25'] if grand_total['comp_orders_25'] > 0 else 0)
app_pct = grand_total['app_26'] / so if so > 0 else 0
app_amt = grand_total['app_26']
app_gw = fmt_growth(grand_total['app_26'], grand_total['app_25'])
app_cg = fmt_growth(grand_total['comp_app_26'], grand_total['comp_app_25'])
acc_pct = grand_total['acc_26'] / so if so > 0 else 0
acc_amt = grand_total['acc_26']
acc_gw = fmt_growth(grand_total['acc_26'], grand_total['acc_25'])
acc_cg = fmt_growth(grand_total['comp_acc_26'], grand_total['comp_acc_25'])
tgt = grand_total['target']
achv = fmt_pct(so / tgt) if tgt > 0 else "0%"
inv = grand_total['inv_total']
mos = inv / grand_total['qty_26'] if grand_total['qty_26'] > 0 else 0
shoes_mos = grand_total['inv_shoes'] / (grand_total['qty_26'] * 0.7) if grand_total['qty_26'] > 0 else 0
app_mos = grand_total['inv_app'] / (grand_total['qty_26'] * 0.25) if grand_total['qty_26'] > 0 else 0
acc_mos = grand_total['inv_acc'] / (grand_total['qty_26'] * 0.05) if grand_total['qty_26'] > 0 else 0

lines.append(f"| **BTB Mono Store Total** | **{fmt_num(so)}** | **{so_gw}** | **{so_cg}** | **{fmt_num(tr)}** | **{tr_gw}** | **{tr_cg}** | **{fmt_pct(cr)}** | **{cr_gw}** | **{cr_cg}** | **{ipo:.2f}** | **{ipo_gw}** | **{ipo_cg}** | **{fmt_pct(app_pct)}** | **{fmt_num(app_amt)}** | **{app_gw}** | **{app_cg}** | **{fmt_pct(acc_pct)}** | **{fmt_num(acc_amt)}** | **{acc_gw}** | **{acc_cg}** | **{fmt_num(tgt)}** | **{achv}** | **{fmt_num(inv)}** | **{mos:.1f}** | **{shoes_mos:.1f}** | **{app_mos:.1f}** | **{acc_mos:.1f}** |")

lines.append("")
lines.append("---")
lines.append("")

# Table 2: BY STORE TIER & KEY STORE REVIEW
lines.append("*【By Store Tier & Key Store Review】*")
lines.append("")
lines.append("- *Chapter:* 沈阳万象城 MTD 全月完成*473.6万*，同比增长29.2%，达成率94.7%，月末冲刺缩小缺口")
lines.append("- *A+:* 整体达成率为88.2%，虽仍受北京SKP拖累，但较10/25（76%）回升12.2个点。*北京SKP：*销售额158.2万，同比去年下跌18%，达成率为71.8%，排名有所回升。*（重点关注）*")
lines.append("- *A:* 同比增长31.2%，目标达成率105.1%，超额达成月度目标。")
lines.append("- *B:* 同比增长34.8%，目标达成率108.3%，整体表现优异。")
lines.append("- *Outlet:* 10.1新开POP-UP店铺苏州比斯特，全月完成*403万*业绩（达成率134.3%），稳居MTD销售额排名第二的店铺。")
lines.append("")

lines.append("### BY STORE TIER MTD")
lines.append("")
lines.append("| Store Tier | #Store | Sellout | Growth | Comp Growth | Traffic | Growth | Comp Growth | CR | Growth | Comp Growth | IPO | Growth | Comp Growth | APP% | APP | Growth | Comp Growth | ACC% | ACC | Growth | Comp Growth | Monthly Target | Target Achv% |")
lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
lines.append("| Chapter | 1 | 4,735,941 | +29% | +29% | 43,150 | +1% | +1% | 6.1% | +2% | +2% | 1.25 | +2% | +2% | 24.8% | 1,175,220 | +68% | +68% | 0.4% | 18,930 | +6% | +6% | 5,000,000 | 94.7% |")
lines.append("| A+ | 6 | 14,012,850 | +28% | +18% | 119,850 | +29% | +12% | 6.0% | +4% | +12% | 1.48 | -3% | -4% | 21.5% | 3,015,220 | +35% | +27% | 1.4% | 192,540 | +49% | +42% | 15,880,000 | 88.2% |")
lines.append("| A | 32 | 55,078,210 | +85% | +31% | 610,250 | +72% | +4% | 4.3% | +4% | +14% | 1.56 | +6% | +5% | 23.5% | 12,943,210 | +95% | +37% | 1.1% | 618,220 | +112% | +53% | 52,400,000 | 105.1% |")
lines.append("| B | 11 | 11,374,422 | +5% | +35% | 136,520 | +54% | +38% | 4.2% | -25% | -10% | 1.52 | -10% | -8% | 24.6% | 2,798,420 | +10% | +52% | 1.4% | 158,210 | +33% | +64% | 10,500,000 | 108.3% |")
lines.append("| Outlet | 1 | 4,030,048 | 0% | 0% | 48,993 | 0% | 0% | 4.8% | 0% | 0% | 2.16 | 0% | 0% | 22.0% | 887,331 | 0% | 0% | 0.1% | 2,775 | 0% | 0% | 3,000,000 | 134.3% |")
lines.append("| **TTL** | **51** | **89,231,471** | **+60%** | **+27%** | **958,763** | **+78%** | **+10%** | **4.6%** | **-9%** | **+1%** | **1.55** | **+2%** | **0%** | **23.3%** | **20,819,401** | **+71%** | **+38%** | **1.1%** | **990,675** | **+76%** | **+50%** | **86,780,000** | **102.8%** |")

lines.append("")
lines.append("### KEY STORE MTD")
lines.append("")
lines.append("| Store Name | Account | Sales Rep | Sellout | Growth | Comp Growth | Traffic | Growth | Comp Growth | CR | Growth | Comp Growth | IPO | Growth | Comp Growth | APP% | APP | Growth | Comp Growth | ACC% | ACC | Growth | Comp Growth | Monthly Target | Target Achv% |")
lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
lines.append("| On 昂跑 沈阳万象城 | Dalian Shangjia Group | David Zhang | 4,735,941 | +29% | +29% | 43,150 | +1% | +1% | 6.1% | +2% | +2% | 1.25 | +2% | +2% | 24.8% | 1,175,220 | +68% | +68% | 0.4% | 18,930 | +6% | +6% | 5,000,000 | 94.7% |")
lines.append("| **Chapter TTL** | | | **4,735,941** | **+29%** | **+29%** | **43,150** | **+1%** | **+1%** | **6.1%** | **+2%** | **+2%** | **1.25** | **+2%** | **+2%** | **24.8%** | **1,175,220** | **+68%** | **+68%** | **0.4%** | **18,930** | **+6%** | **+6%** | **5,000,000** | **94.7%** |")
lines.append("| On 昂跑 杭州万象城 | Shanghai Maoyu Group | David Zhang | 3,649,360 | +18% | +18% | 35,210 | +43% | +43% | 5.7% | -3% | -3% | 1.34 | -13% | -13% | 19.2% | 701,220 | +39% | +39% | 0.8% | 28,150 | +92% | +92% | 3,600,000 | 101.4% |")
lines.append("| On 昂跑 南京德基广场 | Shanghai Really Group | David Zhang | 3,271,820 | +2% | +2% | 24,120 | +2% | +2% | 6.7% | +4% | +4% | 1.50 | +1% | +1% | 19.3% | 631,240 | -3% | -3% | 1.9% | 61,250 | +17% | +17% | 4,000,000 | 81.8% |")
lines.append("| On 昂跑 苏州中心 | Shanghai Really Group | David Zhang | 2,422,610 | +54% | +54% | 15,310 | 0% | 0% | 8.2% | +49% | +49% | 1.47 | +2% | +2% | 20.5% | 496,210 | +147% | +147% | 2.0% | 48,210 | +92% | +92% | 2,600,000 | 93.2% |")
lines.append("| On 昂跑 北京SKP | Shanghai Maoyu Group | David Zhang | 1,582,310 | -18% | -18% | 14,810 | +9% | +9% | 4.6% | -24% | -24% | 1.68 | -2% | -2% | 33.8% | 534,810 | +1% | +1% | 0.9% | 14,210 | -41% | -41% | 2,200,000 | 71.8% |")
lines.append("| On 昂跑 天津万象城 | Tianjin Ruilongxiang Group | Iris Xu | 2,041,120 | +46% | +46% | 15,120 | -10% | -10% | 8.0% | +72% | +72% | 1.43 | 0% | 0% | 22.4% | 457,210 | +28% | +28% | 1.4% | 28,520 | +136% | +136% | 2,380,000 | 85.8% |")
lines.append("| On 昂跑 西安万象城 | Xi'an Guiming Group | Liang Tan | 1,045,630 | 0% | 0% | 15,280 | 0% | 0% | 2.7% | 0% | 0% | 1.89 | 0% | 0% | 18.3% | 191,320 | 0% | 0% | 0.7% | 7,810 | 0% | 0% | 1,100,000 | 95.1% |")
lines.append("| **A+ TTL** | | | **14,012,850** | **+28%** | **+18%** | **119,850** | **+29%** | **+12%** | **6.0%** | **+4%** | **+12%** | **1.48** | **-3%** | **-4%** | **21.5%** | **3,015,220** | **+35%** | **+27%** | **1.4%** | **192,540** | **+49%** | **+42%** | **15,880,000** | **88.2%** |")

lines.append("")
lines.append("---")
lines.append("")

# Relo Store Review
lines.append("*【Relo Store Review】*")
lines.append("")
lines.append("- *7家店铺为2025年年底至2026重新开业的店铺*")
lines.append("- *西安 SKP：*同比大幅增长55.3%，达成率为112.4%，整体业绩与服装业绩表现优异，实现全月超额达成。")
lines.append("- *重庆万象城：*同比大幅增长158.9%，全月达成率107.4%，APP 与 ACC 表现持续强劲，连带率1.33仍有进一步提升空间。")
lines.append("- *南京德基：*同比增长2%，目标达成率81.8%（较10/25的69%大幅回升），APP销售较去年下跌3%左右。*（持续关注）*")
lines.append("- *武汉武商广场：*同比增长45.8%，达成率116.8%，表现突出。")
lines.append("")

lines.append("### RELO STORE MTD")
lines.append("")
lines.append("| Store Name | Account | Sales Rep | Store Tier | Reopening Date | Sellout | Growth | Comp Growth | IPO | Growth | Comp Growth | APP% | APP | Growth | Comp Growth | ACC% | ACC | Growth | Comp Growth | Monthly Target | Target Achv% |")
lines.append("| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |")
lines.append("| On 昂跑 沈阳万象城 | Dalian Shangjia Group | David Zhang | Chapter | 2026-05-11 | 4,735,941 | +29% | +29% | 1.25 | +2% | +2% | 24.8% | 1,175,220 | +68% | +68% | 0.4% | 18,930 | +6% | +6% | 5,000,000 | 94.7% |")
lines.append("| On 昂跑 南京德基广场 | Shanghai Really Group | David Zhang | A+ | 2025-12-31 | 3,271,820 | +2% | +2% | 1.50 | +1% | +1% | 19.3% | 631,240 | -3% | -3% | 1.9% | 61,250 | +17% | +17% | 4,000,000 | 81.8% |")
lines.append("| On 昂跑 苏州中心 | Shanghai Really Group | David Zhang | A+ | 2026-07-15 | 2,422,610 | +54% | +54% | 1.47 | +2% | +2% | 20.5% | 496,210 | +147% | +147% | 2.0% | 48,210 | +92% | +92% | 2,600,000 | 93.2% |")
lines.append("| On 昂跑 西安SKP | Xi'an Guiming Group | Liang Tan | A | 2026-01-13 | 1,011,780 | +55% | +55% | 1.45 | +3% | +3% | 18.9% | 191,220 | +22% | +22% | 0.6% | 6,120 | +16% | +16% | 900,000 | 112.4% |")
lines.append("| On 昂跑 成都SKP | Chengdu Heli Group | Sky Zhang | A | 2026-04-08 | 1,549,940 | +22% | +22% | 1.97 | -1% | -1% | 25.8% | 399,820 | +42% | +42% | 1.0% | 16,120 | +22% | +22% | 1,800,000 | 86.1% |")
lines.append("| On 昂跑 重庆万象城 | Chongqing Weige Group | Sky Zhang | B | 2025-11-22 | 1,610,850 | +159% | +159% | 1.33 | +3% | +3% | 24.1% | 388,210 | +235% | +235% | 1.3% | 20,950 | +301% | +301% | 1,500,000 | 107.4% |")
lines.append("| On 昂跑 武汉武商广场 | Nanchang Chongguang Group | Sky Zhang | B | 2025-11-19 | 1,401,430 | +46% | +46% | 1.46 | -8% | -8% | 27.8% | 389,520 | +49% | +49% | 0.9% | 12,610 | +71% | +71% | 1,200,000 | 116.8% |")

lines.append("")
lines.append("---")
lines.append("")

# Top 5 Stores
lines.append("*【Top 5 stores】*")
lines.append("")
lines.append("*Comparable：*")
lines.append("")
lines.append("| Ranking | Store Name | Opening Date | Sellout | Comp growth | Ranking vs. LY |")
lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")
lines.append("| **1** | On 昂跑 沈阳万象城 | 2024-04-27 | 4,735,941 | +29.2% | -> 0 |")
lines.append("| **2** | On 昂跑 杭州万象城 | 2022-01-01 | 3,649,360 | +18.1% | ↑ 1 |")
lines.append("| **3** | On 昂跑 南京德基广场 | 2023-06-13 | 3,271,820 | +2.0% | ↓ 1 |")
lines.append("| **4** | On 昂跑 长沙国金中心 | 2024-06-01 | 2,930,850 | +26.5% | -> 0 |")
lines.append("| **5** | On 昂跑 西安赛格 | 2021-04-01 | 2,732,382 | +51.6% | ↑ 4 |")
lines.append("")
lines.append("*New:*")
lines.append("")
lines.append("| Ranking | Store Name | Opening Date | Sellout |")
lines.append("| :--- | :--- | :--- | :--- |")
lines.append("| **1** | On 昂跑 苏州比斯特 Pop up | 2026-10-01 | 4,030,048 |")
lines.append("| **2** | On 昂跑 太原茂业 | 2026-09-30 | 2,000,820 |")
lines.append("| **3** | On 昂跑 郑州郑东万象城 | 2025-11-03 | 1,918,100 |")
lines.append("| **4** | On 昂跑 石家庄万象城 | 2026-04-24 | 1,766,000 |")
lines.append("| **5** | On 昂跑 武汉万象城 | 2026-02-04 | 1,602,650 |")
lines.append("| **6** | On 昂跑 天津大悦城 | 2025-12-22 | 1,600,620 |")
lines.append("")
lines.append("- *苏州比斯特 Pop up：*MTD全月突破*403万*，稳居新店第一位且全盘第二位。")
lines.append("- *太原茂业：*全月业绩突破*200万*，在新店中升至第二位。")
lines.append("")

lines.append("---")
lines.append("")

# Key insights
lines.append("*【Key insights】*")
lines.append("")
lines.append("*Sellout*")
lines.append("")
lines.append("- *领先店铺*：南京景枫（+72%），苏州中心（+54%），西安赛格（+52%），郑州正弘城（+51%），重庆万象城（+159%），济南万象城（+88%），合肥银泰（+58%），西安SKP（+55%），此*8*家店铺同比去年均提升超过50%")
lines.append("- *落后店铺*：北京SKP（-18%），北京DT51（-11%），厦门万象城（-4%），深圳平安金融中心（-15%）这4家店铺同比去年仍有所下跌。*（重点关注）*")
lines.append("")
lines.append("*Target Achv%（时间进度100%全月收官）*")
lines.append("")
lines.append("- *领先店铺*：有*26*家店铺最终超额完成本月业绩，其中武汉万象城（160%），苏州比斯特（134%），南京景枫（136%），合肥银泰（124%），武汉武商广场（117%），济南万象城（113%），西安SKP（112%）达成超过*110%*")
lines.append("- *落后店铺*：沈阳恒隆（48%最低），南宁万象城（63%），北京SKP（72%），杭州嘉里中心（72%），北京DT51（74%），杭州IN77（78%），南京德基（82%），此*7*家店铺目标达成率落后于全月进度15个点以上，需要*重点关注*")
lines.append("- *上海懋余（88%），深圳昂首跑（87%），大连尚嘉（83%）*：*3*个客户全月达成率仍未达到100%基准。*（重点关注）*")
lines.append("")
lines.append("*CR & IPO*")
lines.append("")
lines.append("- *需关注以下店铺：*")
lines.append("")
lines.append("  1. *客流下跌同时CR也下跌的店铺*")
lines.append("  2. *客流未猛增但CR下跌的店铺：*北京SKP（CR -24%），深圳平安金融中心（CR -12%），太原万象城（CR -32%）")
lines.append("  3. *IPO和CR同时下降或IPO跌幅超过20%的店铺*：杭州万象城（CR -3% IPO -13%），杭州嘉里中心（CR -28% IPO -5%），南京景枫（CR -25% IPO -7%），厦门SM（CR +6% IPO -6%），重庆北城天街（CR -12% IPO -2%）")
lines.append("")
lines.append("*APP%*")
lines.append("")
lines.append("- *MTD APP%* *23.3%*，销售额同比增长*69.6%*，*40家*店超过目前20%。4家店铺MTD超过30%，分别为合肥银泰（38.1%为全国最高），北京SKP（33.8%），合肥万象城（31.2%），天津大悦城（29.8%）")
lines.append("- *西安赛格10.5%*，占比稳定在10%以上，销售额同比增长超50%")
lines.append("- *APP销售同比下跌超15%：*深圳平安金融中心（-15%）")
lines.append("")
lines.append("具体销售详情和数字请参考附件，如有问题，请随时联系，谢谢！")
lines.append("")
lines.append("Best Regards,")
lines.append("*Cecilia*")

out_path = '/Users/yujiexiang/Documents/data_agent/2026.11.01 BTB Weekly Report.md'
with open(out_path, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print(f"Report successfully written to {out_path} ({len(lines)} lines)")
