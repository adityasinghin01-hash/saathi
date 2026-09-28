"""Fixed, fictional records for the local demo. No patient record is real."""

import random
from datetime import UTC, date, datetime, timedelta

LABEL = "Synthetic demo data"
ANCHOR = date(2026, 9, 28)
STAMP = datetime(2026, 9, 28, 8, tzinfo=UTC).isoformat().replace("+00:00", "Z")


def seed_if_empty(store):
    if store.list("facility"):
        return
    rng = random.Random(42)

    def add(kind, row):
        store.put(kind, {**row, "synthetic_label": LABEL})

    facilities = [
        ("phc-1", "Sundarpur PHC", "सुंदरपुर प्राथमिक स्वास्थ्य केंद्र", "PHC", "North", 28.95, 77.68),
        ("phc-2", "Nayagaon PHC", "नयागांव प्राथमिक स्वास्थ्य केंद्र", "PHC", "North", 28.98, 77.71),
        ("phc-3", "Amarpur PHC", "अमरपुर प्राथमिक स्वास्थ्य केंद्र", "PHC", "North", 29.01, 77.65),
        ("phc-4", "Shantipur PHC", "शांतिपुर प्राथमिक स्वास्थ्य केंद्र", "PHC", "South", 28.87, 77.73),
        ("phc-5", "Navgram PHC", "नवग्राम प्राथमिक स्वास्थ्य केंद्र", "PHC", "South", 28.84, 77.67),
        ("phc-6", "Udaypur PHC", "उदयपुर प्राथमिक स्वास्थ्य केंद्र", "PHC", "South", 28.90, 77.62),
        ("store-1", "Suryanagar District Store", "सूर्यनगर जिला भंडार", "district_store", "Central", 28.93, 77.69),
    ]
    for id, name, name_hi, kind, block, lat, lng in facilities:
        add("facility", {"id": id, "name": name, "name_hi": name_hi,
                             "type": kind, "block": block,
                             "district": "Suryanagar", "lat": lat, "lng": lng})

    drugs = [
        ("metformin", "Metformin", "मेटफॉर्मिन", "500 mg"),
        ("glimepiride", "Glimepiride", "ग्लिमेपिराइड", "1 mg"),
        ("amlodipine", "Amlodipine", "एम्लोडिपिन", "5 mg"),
        ("telmisartan", "Telmisartan", "टेल्मिसार्टन", "40 mg"),
    ]
    for id, name, name_hi, strength in drugs:
        add("drug", {"id": id, "name": name, "name_hi": name_hi,
                         "form": "tablet", "strength": strength, "unit": "tablet",
                         "demand_rule": "max"})

    pharmacists = [("Sunita", "सुनीता"), ("Anil", "अनिल"), ("Farah", "फ़राह"),
                   ("Mahesh", "महेश"), ("Kavita", "कविता"), ("Naveen", "नवीन")]
    for number in range(1, 7):
        name, name_hi = pharmacists[number - 1]
        add("user", {"id": f"pharmacist-{number}", "role": "pharmacist",
                         "name": name, "name_hi": name_hi,
                         "facility_id": f"phc-{number}",
                         "language": "hi", "phone_masked": f"XXXXXX{number:04d}"})
    ashas = [("Rekha", "रेखा"), ("Poonam", "पूनम")]
    for number in range(1, 3):
        name, name_hi = ashas[number - 1]
        add("user", {"id": f"asha-{number}", "role": "asha", "name": name,
                         "name_hi": name_hi,
                         "facility_id": f"phc-{number}", "language": "hi",
                         "phone_masked": f"XXXXXX{number+10:04d}"})
    add("user", {"id": "officer-1", "role": "district_officer", "name": "Dr. Mehra",
                     "name_hi": "डॉ. मेहरा",
                     "facility_id": "store-1", "language": "en", "phone_masked": "XXXXXX0099"})

    # Keep this roster fixed so the demo's patient and user names remain in sync.
    patient_profiles = [
        ("Ramesh", "रमेश", 54, "M"),
        ("Shabana Khan", "शबाना ख़ान", 58, "F"),
        ("Sunita Yadav", "सुनीता यादव", 47, "F"),
        ("Iqbal Ansari", "इक़बाल अंसारी", 63, "M"),
        ("Mahendra Singh", "महेंद्र सिंह", 69, "M"),
        ("Saira Bano", "सायरा बानो", 52, "F"),
        ("Nirmala Devi", "निर्मला देवी", 61, "F"),
        ("Salim Qureshi", "सलीम कुरैशी", 44, "M"),
        ("Rajesh Verma", "राजेश वर्मा", 43, "M"),
        ("Farida Begum", "फ़रीदा बेगम", 70, "F"),
        ("Poonam Gupta", "पूनम गुप्ता", 55, "F"),
        ("Yusuf Ali", "यूसुफ़ अली", 49, "M"),
        ("Om Prakash Tiwari", "ओम प्रकाश तिवारी", 72, "M"),
        ("Nazma Parveen", "नज़मा परवीन", 38, "F"),
        ("Kavita Chauhan", "कविता चौहान", 41, "F"),
        ("Imran Siddiqui", "इमरान सिद्दीक़ी", 57, "M"),
        ("Suresh Pal", "सुरेश पाल", 59, "M"),
        ("Amina Khatoon", "अमीना ख़ातून", 66, "F"),
        ("Meena Kumari", "मीना कुमारी", 48, "F"),
        ("Arif Khan", "आरिफ़ ख़ान", 53, "M"),
        ("Brij Mohan Sharma", "बृज मोहन शर्मा", 65, "M"),
        ("Rekha Saini", "रेखा सैनी", 45, "F"),
        ("Nasreen Bano", "नसरीन बानो", 62, "F"),
        ("Firoz Alam", "फ़िरोज़ आलम", 39, "M"),
        ("Harish Tyagi", "हरीश त्यागी", 50, "M"),
        ("Savitri Jatav", "सावित्री जाटव", 75, "F"),
        ("Anita Mishra", "अनीता मिश्रा", 36, "F"),
        ("Rashid Ansari", "राशिद अंसारी", 68, "M"),
        ("Devendra Kumar", "देवेंद्र कुमार", 64, "M"),
        ("Rubina Qureshi", "रुबीना कुरैशी", 46, "F"),
        ("Pushpa Maurya", "पुष्पा मौर्य", 73, "F"),
        ("Wasim Akhtar", "वसीम अख़्तर", 42, "M"),
        ("Manoj Srivastava", "मनोज श्रीवास्तव", 56, "M"),
        ("Rukhsana Begum", "रुख़साना बेगम", 60, "F"),
        ("Sushila Rawat", "सुशीला रावत", 67, "F"),
        ("Nadeem Ali", "नदीम अली", 51, "M"),
        ("Satish Chandra", "सतीश चंद्र", 40, "M"),
        ("Geeta Kashyap", "गीता कश्यप", 71, "F"),
        ("Khadija Parveen", "ख़दीजा परवीन", 37, "F"),
        ("Javed Siddiqui", "जावेद सिद्दीक़ी", 74, "M"),
        ("Yogesh Saxena", "योगेश सक्सेना", 54, "M"),
        ("Lata Tomar", "लता तोमर", 59, "F"),
        ("Zohra Khatoon", "ज़ोहरा ख़ातून", 43, "F"),
        ("Naseer Ahmad", "नसीर अहमद", 65, "M"),
        ("Vinod Yadav", "विनोद यादव", 52, "M"),
        ("Usha Verma", "उषा वर्मा", 35, "F"),
        ("Kamla Lodhi", "कमला लोधी", 69, "F"),
        ("Shahid Hussain", "शाहिद हुसैन", 47, "M"),
        ("Raghubir Singh", "रघुबीर सिंह", 75, "M"),
        ("Shanti Devi", "शांति देवी", 63, "F"),
        ("Salma Khan", "सलमा ख़ान", 50, "F"),
        ("Pradeep Gupta", "प्रदीप गुप्ता", 38, "M"),
        ("Kailash Pal", "कैलाश पाल", 58, "M"),
        ("Rani Chauhan", "रानी चौहान", 72, "F"),
        ("Saeeda Bano", "सईदा बानो", 56, "F"),
        ("Danish Alam", "दानिश आलम", 45, "M"),
        ("Ashok Maurya", "अशोक मौर्य", 70, "M"),
        ("Vidya Jatav", "विद्या जाटव", 42, "F"),
        ("Hina Akhtar", "हिना अख़्तर", 64, "F"),
        ("Ajay Mishra", "अजय मिश्रा", 55, "M"),
    ]
    for number, (name, name_hi, age, sex) in enumerate(patient_profiles, start=1):
        facility_number = (number - 1) % 6 + 1
        patient_id = f"patient-{number:03d}"
        condition = "T2D" if number % 2 else "HTN"
        asha_id = f"asha-{(number - 1) % 2 + 1}"
        add("patient", {"id": patient_id,
                            "name": name, "name_hi": name_hi,
                            "age": age, "sex": sex,
                            "conditions": [condition], "facility_id": f"phc-{facility_number}",
                            "asha_id": asha_id, "language": "hi"})
        add("user", {"id": f"patient-user-{number:03d}", "role": "patient",
                         "name": name, "name_hi": name_hi,
                         "facility_id": f"phc-{facility_number}",
                         "patient_id": patient_id, "language": "hi", "phone_masked": f"XXXXXX{number:04d}"})
        drug_id = "metformin" if condition == "T2D" else "amlodipine"
        add("prescription", {"id": f"rx-{number:03d}-1", "patient_id": patient_id,
                                 "drug_id": drug_id, "dose_per_day": 1 if number % 3 else 2,
                                 "days_supply": 30, "start_date": "2026-06-01",
                                 "confirmed_by_staff": True, "active": True})
        if number % 3 == 0:
            add("prescription", {"id": f"rx-{number:03d}-2", "patient_id": patient_id,
                                     "drug_id": "glimepiride" if condition == "T2D" else "telmisartan",
                                     "dose_per_day": 1, "days_supply": 30, "start_date": "2026-06-01",
                                     "confirmed_by_staff": True, "active": True})

    stockout_periods = {
        ("phc-1", "metformin"): [(20, 25), (80, 89)],
        ("phc-3", "amlodipine"): [(40, 45)],
        ("phc-5", "telmisartan"): [(70, 74)],
    }
    metformin_stock = {"phc-1": 0, "phc-3": 280, "phc-4": 28,
                       "phc-5": 110, "phc-6": 25}
    for facility_id, *_ in facilities:
        for drug_id, _, _, _ in drugs:
            if facility_id == "store-1":
                quantity = 1500
            elif drug_id == "metformin" and facility_id in metformin_stock:
                quantity = metformin_stock[facility_id]
            else:
                quantity = 120 + rng.randrange(60)
            batches = []
            if quantity:
                for part in range(2):
                    batch = {"id": f"batch-{facility_id}-{drug_id}-{part+1}",
                                 "facility_id": facility_id, "drug_id": drug_id,
                                 "quantity": quantity // 2 if part == 0 else quantity - quantity // 2,
                                 "expiry_date": (ANCHOR + timedelta(days=120 + 30 * part)).isoformat()}
                    add("batch", batch)
                    batches.append(batch)
            add("stock_snapshot", {"id": f"stock-{facility_id}-{drug_id}",
                                       "facility_id": facility_id, "drug_id": drug_id,
                                       "on_hand": quantity, "batches": batches, "recorded_at": STAMP,
                                       "recorded_by": "synthetic-seed", "source": "manual"})
            for day in range(90):
                current = ANCHOR - timedelta(days=89 - day)
                censored = any(start <= day <= end for start, end in stockout_periods.get(
                    (facility_id, drug_id), []))
                if facility_id == "phc-1" and drug_id == "metformin":
                    on_hand = 0 if censored else 48 + day % 20
                else:
                    on_hand = 0 if censored or quantity == 0 else quantity
                add("daily_stock", {"id": f"daily-stock-{facility_id}-{drug_id}-{current}",
                                    "facility_id": facility_id, "drug_id": drug_id,
                                    "date": current.isoformat(), "on_hand": on_hand})
                if facility_id == "store-1":
                    continue
                censored = on_hand == 0
                if censored:
                    add("stockout_day", {"id": f"stockout-{facility_id}-{drug_id}-{current}",
                                             "facility_id": facility_id, "drug_id": drug_id,
                                             "date": current.isoformat()})
                add("dispensing", {"id": f"disp-{facility_id}-{drug_id}-{current}",
                                       "facility_id": facility_id, "drug_id": drug_id, "patient_id": None,
                                       "quantity": 0 if censored else rng.choice([0, 1, 2, 3, 4]),
                                       "dispensed_at": f"{current.isoformat()}T12:00:00Z"})
