# AIE314 / AIE315 · Topic 4 — ปริมาณการเดินทางและผู้โดยสาร

โครงงานกลุ่ม (3 คน) · ส่งภายใน **พฤ. 3 ธ.ค. 2569** (เป้าหมายภายในทีม พ. 2 ธ.ค.) · นำเสนอ **ศ. 4 ธ.ค. 2569**

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

## ลำดับการรัน (ต้องรันตามลำดับ)

เปิด Jupyter จากโฟลเดอร์โปรเจกต์ (`jupyter lab`) แล้วรันแต่ละ notebook ด้วย **Restart Kernel & Run All**

| ลำดับ | Notebook | ผลลัพธ์ |
|---|---|---|
| 1 | `notebooks/00_data_understanding.ipynb` | สำรวจข้อมูล, Data Dictionary, Feature Selection (ไม่สร้างไฟล์) |
| 2 | `notebooks/01_cleaning.ipynb` | `passengers_clean_long.csv`, `service_catalog.csv`, `quality_log.csv`, `figures/01_quality_heatmap.png` |
| 3 | `notebooks/02_q1_weekday_weekend.ipynb` | `q1_daily_features.csv`, `figures/q1_*.png` |
| 4 | `notebooks/03_q2_yoy_2568_2569.ipynb` | `q2_yoy_comparison.csv`, `q2_missing_sensitivity.csv`, `figures/q2_*.png` |
| 5 | `notebooks/04_q3_international.ipynb` | `q3_international_monthly.csv`, `figures/q3_*.png` |

ตรวจการรันซ้ำทั้งหมดในคำสั่งเดียว (ใช้ก่อนส่งงาน):

```bash
cd notebooks
for nb in 0*.ipynb; do jupyter nbconvert --to notebook --execute --inplace "$nb"; done
```

## โครงสร้างโฟลเดอร์

```
AIE314_Topic4/
├── data/
│   ├── raw/          ไฟล์ต้นฉบับ (ห้ามแก้ไข)
│   └── prepared/     ไฟล์ที่โค้ดสร้าง (ส่งทุกไฟล์)
├── src/prep.py       ฟังก์ชันร่วมสำหรับโหลดและทำความสะอาดข้อมูล (ทุก notebook import)
├── notebooks/        00–04
├── figures/          กราฟทั้งหมดที่ใช้ในรายงานและสไลด์ (สร้างจาก notebook เท่านั้น)
├── report/           โครงรายงาน + รายงาน PDF ฉบับส่ง
└── slides/           โครงสไลด์ + สไลด์ฉบับส่ง
```

## Prepared Datasets

| ไฟล์ | สร้างโดย | 1 แถว = | ใช้ตอบข้อ |
|---|---|---|---|
| `passengers_clean_long.csv` | 01 | 1 บริการ × 1 วัน (ทั้งสองปี) พร้อม flag คุณภาพ | 1, 2, 3 |
| `service_catalog.csv` | 01 | 1 บริการ (43 รายการ): หน่วย, ทิศ, ยอดรวม, เหตุผลที่ตัด | 1, 2, 3 |
| `quality_log.csv` | 01 | 1 ปี: จำนวนแถว/ค่าว่าง/ค่าซ้ำ/ค่าศูนย์ ก่อน→หลัง | รายงานส่วนที่ 2 |
| `q1_daily_features.csv` | 02 | TODO | 1 |
| `q2_yoy_comparison.csv` | 03 | TODO | 2 |
| `q2_missing_sensitivity.csv` | 03 | TODO | 2 |
| `q3_international_monthly.csv` | 04 | TODO | 3 |

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

## กติกาของทีม

- หนึ่งคนหนึ่ง notebook · แก้ `src/prep.py` หลัง M2 (22 พ.ย.) เฉพาะเมื่อทั้งทีมตกลงกันแล้ว
- ทุกตัวเลขหรือกราฟในรายงานและสไลด์ต้องมาจาก output ของ notebook
- ใช้ relative path เท่านั้น · บันทึกกราฟด้วย `prep.save_fig()`
- ตรวจงานไขว้: A ตรวจข้อ 2 · B ตรวจข้อ 3 · C ตรวจข้อ 1
