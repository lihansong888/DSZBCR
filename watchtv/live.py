import requests
import re
import os
# ========== 源配置 ==========
SOURCE_CONFIG = [
    {
        "url": "http://adultiptv.net/chs.m3u",
        "mode": "all",          # all：全部收下，统一分组
        "out_group": "国外直播频道"
    },
    {
        "url": "https://raw.githubusercontent.com/fafa002/yf2025/refs/heads/main/yiyifafa.txt",
        "mode": "filter",       # filter：只保留匹配原始分组的频道
        "src_group": "私密频道3_169169",# 源里面原始分组名字
        "out_group": "移动三台" # 输出分组名，可以改名
    }
]

def parse_any(text: str):
    res = []
    extinf_line = None
    current_group = None
    for raw_line in text.splitlines():
        ln = raw_line.strip()
        if not ln:
            continue
        if ln.startswith("#EXTINF:"):
            extinf_line = ln
            continue
        if extinf_line is not None and not ln.startswith("#"):
            res.append((extinf_line, ln, current_group))
            extinf_line = None
            continue
        if ',' in ln and not ln.startswith("#"):
            sp = ln.split(',',1)
            name_part = sp[0].strip()
            url_part = sp[1].strip()
            if url_part == "#genre#":
                current_group = name_part
                continue
            if current_group:
                fake_ext = f'#EXTINF:-1 group-title="{current_group}",{name_part}'
            else:
                fake_ext = f'#EXTINF:-1,{name_part}'
            res.append((fake_ext, url_part, current_group))
    return res

def get_channel_name(extinf):
    if "," in extinf:
        return extinf.split(",")[-1].strip()
    return ""

def get_group_title(extinf):
    m = re.search(r'group-title="([^"]+)"', extinf)
    if m:
        return m.group(1).strip()
    return ""

def main():
    all_out = []
    seen = set()
    for cfg in SOURCE_CONFIG:
        url = cfg["url"]
        try:
            resp = requests.get(url, timeout=15)
            resp.raise_for_status()
            channels = parse_any(resp.text)
            for extinf, play_url, src_g in channels:
                ch_name = get_channel_name(extinf)
                item_key = (ch_name, play_url)
                if item_key in seen:
                    continue
                # 模式1：全部采集，强制统一分组
                if cfg["mode"] == "all":
                    seen.add(item_key)
                    all_out.append( (cfg["out_group"], ch_name, play_url) )
                # 模式2：只保留源分组等于指定名字的
                elif cfg["mode"] == "filter":
                    real_g = get_group_title(extinf)
                    if real_g == cfg["src_group"] or src_g == cfg["src_group"]:
                        seen.add(item_key)
                        all_out.append( (cfg["out_group"], ch_name, play_url) )
        except Exception as e:
            print(f"⚠️ 拉取 {url} 失败：{e}")

    print(f"✅采集完成，总共 {len(all_out)} 个频道")
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
