#!/usr/bin/env python3
"""
extract_gtow.py
────────────────────────────────────────────────────────
从录屏视频（.mp4 / .mkv …）里批量 OCR 出 GTO Wizard
聚合报告的「翻牌-IP/OOP 数值」并导出 Excel。

USAGE
    python extract_gtow.py input.mp4 [-o output.xlsx]
                                     [--fps 1]
                                     [--lang eng]

依赖
    pip install opencv-python pytesseract pandas tqdm
    # 并保证系统已安装 Tesseract OCR，可在 PATH 中找到
"""

import cv2, pytesseract, pandas as pd, re, argparse, pathlib, sys
from tqdm import tqdm

def main():
    ag = argparse.ArgumentParser(description="Extract GTOW aggregate report from screen-recording.")
    ag.add_argument("video", help="录屏文件（.mp4 / .mkv …）")
    ag.add_argument("-o", "--output", help="输出 .xlsx（默认与视频同名）")
    ag.add_argument("--fps", type=int, default=1, help="每秒抽多少帧做 OCR（默认 1）")
    ag.add_argument("--lang", default="eng", help="Tesseract 语言包（默认 eng）")
    args = ag.parse_args()

    cap = cv2.VideoCapture(args.video)
    if not cap.isOpened():
        sys.exit("❌  无法打开视频")

    vfps = cap.get(cv2.CAP_PROP_FPS) or 30   # 有些录屏不写 FPS，给个兜底
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    rows = []
    for i in tqdm(range(total), unit="frame"):
        ok, frame = cap.read()
        if not ok:
            break
        # 只保留每秒的第 n 帧
        if i % int(vfps / args.fps):
            continue
        text = pytesseract.image_to_string(frame, lang=args.lang)
        for line in text.splitlines():
            # 例：'AcKd5  46.1  53.9'
            m = re.match(
                r'\s*([2-9TJQKA][cdhs][2-9TJQKA][cdhs][2-9TJQKA][cdhs])'
                r'\s+([\d.]+)\s+([\d.]+)',
                line,
            )
            if m:
                rows.append(m.groups())

    cap.release()

    if not rows:
        sys.exit("⚠️  没识别到任何行，检查视频分辨率 / OCR 语言包。")

    df = (pd.DataFrame(rows, columns=["flop", "OOP_EQR", "IP_EQR"])
            .drop_duplicates())
    outfile = pathlib.Path(args.output) if args.output else pathlib.Path(args.video).with_suffix(".xlsx")
    df.to_excel(outfile, index=False)
    print(f"\n✅  导出 {len(df)} 行 → {outfile}")

if __name__ == "__main__":
    main()
