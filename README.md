# AIE314 / AIE315 · Topic 4 — ปริมาณการเดินทางและผู้โดยสาร

คำถาม
1. ปริมาณการใช้บริการขนส่ง วันธรรมดา vs วันหยุดสุดสัปดาห์ — สมาชิก A
2. ต้นปี 2569 (1 ม.ค.–11 มี.ค.) เทียบช่วงเดียวกันของ 2568 + ผลของวิธีจัดการค่าว่าง/ค่าศูนย์ — สมาชิก B
3. ผู้โดยสารระหว่างประเทศ ขาเข้า vs ขาออก ตามรูปแบบการเดินทาง — สมาชิก C

แผนงานฉบับเต็ม: `AIE314_Topic4_Project_Plan.pdf`

## ติดตั้ง

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## วิธีรัน

**ทางเดียวจบ (ใช้ก่อนส่งงาน):** สร้าง prepared CSV และรูปทั้งหมดจากไฟล์ดิบ

```bash
python src/run_all.py --strict   # สร้าง prepared CSV 7 ไฟล์ + รูป 9 รูป (exit 0 = ครบ)
pytest                           # 35 tests ต้องผ่านทั้งหมด
```

**ดูผลพร้อมคำอธิบาย:** เปิด `jupyter lab` แล้วรันทีละ notebook ด้วย **Restart Kernel & Run All**

| ลำดับ | Notebook | เรียกโค้ดจาก | ผลลัพธ์ |
|---|---|---|---|
| 1 | `00_data_understanding.ipynb` | `prep` | สำรวจข้อมูล, Data Dictionary, Feature Selection |
| 2 | `01_cleaning.ipynb` | `prep`, `plots` | `passengers_clean_long.csv`, `service_catalog.csv`, `quality_log.csv`, `01_quality_heatmap.png` |
| 3 | `02_q1_weekday_weekend.ipynb` | `q1_weekday` | `q1_daily_features.csv`, `q1_*.png` |
| 4 | `03_q2_yoy_2568_2569.ipynb` | `q2_yoy` | `q2_yoy_comparison.csv`, `q2_missing_sensitivity.csv`, `q2_*.png` |
| 5 | `04_q3_international.ipynb` | `q3_intl` | `q3_international_monthly.csv`, `q3_*.png` |

## โครงสร้างโค้ด

**หลักการ:** logic ทั้งหมดอยู่ใน `src/*.py` (import ได้, test ได้, diff อ่านง่าย) · notebook มีแค่ markdown อธิบาย + เรียกฟังก์ชัน + แสดงผล เพื่อเป็นหลักฐานให้ผู้ตรวจ

```
src/
  prep.py        โหลด + ทำความสะอาด + build_all()                       (A) ✅
  features.py    feature ที่ใช้หลายข้อ: calendar, safe_pct_change, monthly  ✅
  plots.py       สไตล์กราฟร่วม, ฟอนต์ไทย, save_fig                       (C) ✅
  q1_weekday.py  ข้อ 1                                                   (A) ✅
  q2_yoy.py      ข้อ 2 + สถานการณ์ S1–S5                                 (B) ✅
  q3_intl.py     ข้อ 3                                                   (C) ✅
  run_all.py     รันทั้ง pipeline
tests/           pytest: test_prep, test_features, test_q1_weekday, test_q2_yoy, test_q3_intl
notebooks/       00–04 (บาง)
```

**สถานะ:** โค้ดครบทั้ง 3 ข้อแล้ว ช่องการตีความใน notebook 02–04 เป็น**ร่าง** (มีป้าย ✍️) ที่เขียนจากผลจริง
แต่ละคนต้องอ่านทวนข้อของตัวเองและข้ออื่น เพราะทุกคนต้องตอบคำถามได้ทั้ง 3 ข้อในวันนำเสนอ

**ถ้าจะแก้โค้ด:** แก้ใน `src/` → `pytest` → Restart & Run All notebook → `run_all.py --strict` แล้ว commit ทั้งโค้ด, CSV และรูปพร้อมกัน

## โครงสร้างโฟลเดอร์

```
AIE314_Topic4/
├── data/raw/          ไฟล์ต้นฉบับ (ห้ามแก้ไข)
├── data/prepared/     ไฟล์ที่โค้ดสร้าง (ส่งทุกไฟล์)
├── src/  tests/  notebooks/
├── fonts/            Sarabun (SIL OFL) สำหรับภาษาไทยในกราฟ — plots.setup_style() โหลดให้อัตโนมัติ
├── figures/           กราฟทั้งหมด (สร้างจากโค้ดเท่านั้น)
├── report/            โครงรายงาน + รายงาน PDF ฉบับส่ง
└── slides/            โครงสไลด์ + สไลด์ฉบับส่ง
```

## Prepared Datasets

| ไฟล์ | สร้างโดย | 1 แถว = | ใช้ตอบข้อ |
|---|---|---|---|
| `passengers_clean_long.csv` | 01 | 1 บริการ × 1 วัน (ทั้งสองปี) พร้อม flag คุณภาพ | 1, 2, 3 |
| `service_catalog.csv` | 01 | 1 บริการ (43 รายการ): หน่วย, ทิศ, ยอดรวม, เหตุผลที่ตัด | 1, 2, 3 |
| `quality_log.csv` | 01 | 1 ปี: จำนวนแถว/ค่าว่าง/ค่าซ้ำ/ค่าศูนย์ ก่อน→หลัง | รายงานส่วนที่ 2 |
| `q1_daily_features.csv` | 02 / `q1_weekday` | 1 บริการ × 1 วัน ปี 2568: วันในสัปดาห์, is_weekend, เดือน, dow_index (13,664 แถว) | 1 |
| `q2_yoy_comparison.csv` | 03 / `q2_yoy` | 1 บริการ: ค่าเฉลี่ยต่อวัน 68/69, % และจำนวนที่เปลี่ยน, coverage, อันดับ (วิธีหลัก S2, 38 แถว) | 2 |
| `q2_missing_sensitivity.csv` | 03 / `q2_yoy` | 1 บริการ × 1 วิธี (S1–S5): ตารางเดียวกับข้างบนต่อวิธี (191 แถว) | 2 |
| `q3_international_monthly.csv` | 04 / `q3_intl` | 1 mode × 1 เดือน ปี 2568: ขาเข้า, ขาออก, net_flow, arr_dep_ratio, MoM %, mode_share (48 แถว) | 3 |

### คอลัมน์ของ `passengers_clean_long.csv`

| คอลัมน์ | ความหมาย |
|---|---|
| `date`, `year_be` | วันที่ (ค.ศ.) และปี พ.ศ. |
| `mode` | road / water / rail / air |
| `purpose` | intercity / intracity / international |
| `public_private`, `agency` | จากไฟล์ต้นฉบับ |
| `service` | ชื่อบริการ (แก้ชื่อที่สะกดต่างกันแล้ว) |
| `port`, `direction` | ชื่อท่า และ arrival / departure / none (แยกจากคำว่า ขาเข้า/ขาออกประเทศ) |
| `unit` | คน / คัน |
| `is_aggregate` | True = “รถยนต์ทุกประเภท” ซึ่งรวมรถ 4 ล้อไว้แล้ว ห้ามบวกซ้ำ |
| `exclude_reason` | ว่าง = ใช้ได้ · `unit=คัน` · `all-zero series` |
| `value` | ปริมาณต่อวัน (NaN = ไม่มีข้อมูล — **ไม่ได้เติมค่า**) |
| `missing_flag`, `zero_flag` | value เป็น NaN / เป็น 0 |
| `zero_run_len`, `zero_long_run` | ความยาวช่วงศูนย์ติดกัน และ True ถ้า ≥ 7 วัน (ถือว่าหยุดรายงาน) |
| `had_duplicate` | แถวนี้เคยมีแถวซ้ำที่ถูกตัดออก |

ใช้ `prep.load_clean()` เพื่ออ่านไฟล์นี้ให้ได้ชนิดข้อมูลที่ถูกต้อง และ `prep.passenger_rows(df)` เพื่อเลือกเฉพาะแถวที่เป็นผู้โดยสารและใช้ได้

## ภาษาไทยในกราฟ

matplotlib ไม่รองรับการจัดตำแหน่งสระ/วรรณยุกต์แบบ OpenType (GPOS) ฟอนต์ของ macOS เช่น Thonburi จึงแสดง**สระลอย**
โปรเจกต์นี้แนบฟอนต์ Sarabun ไว้ใน `fonts/` และ `plots.setup_style()` จะลงทะเบียนให้เอง ทุกเครื่องจึงได้กราฟหน้าตาเดียวกัน
**ห้ามตั้ง `font.family` เองใน notebook** ให้เรียก `plots.setup_style()` เท่านั้น

## กติกาของทีม

- หนึ่งคนหนึ่งไฟล์ `src/qN_*.py` + notebook ของตัวเอง · แก้ `src/prep.py`, `features.py`, `plots.py` หลัง M2 (22 พ.ย.) เฉพาะเมื่อทั้งทีมตกลงกันแล้ว
- ทุกตัวเลขหรือกราฟในรายงานและสไลด์ต้องมาจาก output ของ notebook
- ใช้ relative path เท่านั้น · บันทึกกราฟด้วย `plots.save_fig()` · ก่อนส่งงาน `run_all.py --strict` และ `pytest` ต้องผ่าน
- ตรวจงานไขว้: A ตรวจข้อ 2 · B ตรวจข้อ 3 · C ตรวจข้อ 1
