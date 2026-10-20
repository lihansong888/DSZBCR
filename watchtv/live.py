import requests
import re
import os

# ========== 源配置 ==========
SOURCE_CONFIG = [
    {
        "url": "http://adultiptv.net/chs.m3u",
        "mode": "all",
        "out_group": "欧美直播频道"
    },
    {
        "url": "https://raw.githubusercontent.com/fafa002/yf2025/refs/heads/main/yiyifafa.txt",
        "mode": "filter",
        "src_group": "私密频道3_169169",
        "out_group": "欧美频道2"
    }
]

def parse_any(text: str):
    res = []
    current_group = None
    all_group_names = set()
    for raw_line in text.splitlines():
        ln = raw_line.strip()
        if not ln:
            continue
        # 分组标记行：xxx,#genre#,xxx
        if ",#genre#," in ln:
            parts = ln.split(',')
            current_group = parts[0].strip()
            all_group_names.add(current_group)
            continue
        # 跳过注释行
        if ln.startswith("#"):
            continue
        # 情况A：频道名,链接
        if ',' in ln:
            ch_name, play_url = ln.split(',', 1)
            ch_name = ch_name.strip()
            play_url = play_url.strip()
            res.append((ch_name, play_url, current_group))
        # 情况B：只有播放链接，没有频道名（适配第一个源）
        else:
            ch_name = ln
            play_url = ln
            res.append((ch_name, play_url, current_group))
    print(f"【该源识别到全部分组】：{sorted(all_group_names)}")
    return res

def main():
    all_out = []
    seen = set()
    for cfg in SOURCE_CONFIG:
        url = cfg["url"]
        print(f"\n------正在拉取：{url}------")
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            channel_list = parse_any(resp.text)
            for ch_name, play_url, src_g in channel_list:
                item_key = (ch_name, play_url)
                if item_key in seen:
                    continue

                if cfg["mode"] == "all":
                    seen.add(item_key)
                    all_out.append((cfg["out_group"], ch_name, play_url))
                elif cfg["mode"] == "filter":
                    if src_g == cfg["src_group"]:
                        print(f"✅命中频道：{ch_name}")
                        seen.add(item_key)
                        all_out.append((cfg["out_group"], ch_name, play_url))
        except Exception as e:
            print(f"⚠️ 拉取失败：{e}")

    print(f"\n✅采集完成，总共 {len(all_out)} 个频道")
    out_dir = os.path.dirname(os.path.abspath(__file__))
    output_m3u = ["#EXTM3U"]
    for gname, cname, curl in all_out:
        line = f'#EXTINF:-1 group-title="{gname}",{cname}'
        output_m3u.append(line)
        output_m3u.append(curl)

    m3u8_path = os.path.join(out_dir, "live.m3u8")
    with open(m3u8_path, "w", encoding="utf-8") as f:
        f.write("\n".join(output_m3u))
    print(f"✅已输出 m3u8：{m3u8_path}")

if __name__ == "__main__":
    main()
