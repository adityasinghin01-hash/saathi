# Forecast evaluation

Synthetic demo data. Patient-level need is generated independently of all four forecast methods.

MAE is units/day against all patient need, including outside purchases. False alerts and unmet patient-days use PHC requests, excluding purchases filled elsewhere. False-alert rate uses all runs; other measures are means per run. A replenishment order takes seven days and is sized to 130% of the forecast.

PDC prior days: 60, selected on repetitions 1000–1007; scored repetitions begin at 0.

| Scenario | Method | MAE/day | False alert rate | Unmet patient-days | Lead days | Overstock units | Stockout days |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| baseline | dispensing_only | 4.98 | 0.000 | 227.58 | 7.00 | 0.25 | 4.92 |
| baseline | prescription_only | 24.07 | 0.333 | 3.33 | 12.58 | 389.19 | 0.17 |
| baseline | calibrated | 6.07 | 0.000 | 227.58 | 7.00 | 0.00 | 4.92 |
| baseline | combined | 3.81 | 0.000 | 227.58 | 7.00 | 0.02 | 4.92 |
| enrolment_gap | dispensing_only | 4.11 | 0.000 | 237.58 | 6.67 | 0.03 | 5.08 |
| enrolment_gap | prescription_only | 4.04 | 0.000 | 237.58 | 6.67 | 0.00 | 5.08 |
| enrolment_gap | calibrated | 23.52 | 0.000 | 629.08 | 2.58 | 0.00 | 13.58 |
| enrolment_gap | combined | 4.27 | 0.000 | 237.58 | 6.67 | 0.00 | 5.08 |
| stale_prescriptions | dispensing_only | 3.57 | 0.083 | 233.25 | 5.67 | 0.97 | 5.42 |
| stale_prescriptions | prescription_only | 59.42 | 0.333 | 25.17 | 11.42 | 1461.91 | 0.83 |
| stale_prescriptions | calibrated | 15.17 | 0.333 | 25.17 | 11.42 | 186.26 | 0.83 |
| stale_prescriptions | combined | 17.51 | 0.333 | 25.17 | 11.42 | 236.45 | 0.83 |
| false_reports | dispensing_only | 4.98 | 0.000 | 227.58 | 7.00 | 0.25 | 4.92 |
| false_reports | prescription_only | 24.07 | 0.333 | 3.33 | 12.58 | 389.19 | 0.17 |
| false_reports | calibrated | 6.07 | 0.000 | 227.58 | 7.00 | 0.00 | 4.92 |
| false_reports | combined | 3.81 | 0.000 | 227.58 | 7.00 | 0.02 | 4.92 |
| outside_purchases | dispensing_only | 25.76 | 0.000 | 148.08 | 2.17 | 0.00 | 6.00 |
| outside_purchases | prescription_only | 23.76 | 0.750 | 0.00 | 22.08 | 674.19 | 0.00 |
| outside_purchases | calibrated | 25.81 | 0.000 | 148.08 | 2.17 | 0.00 | 6.00 |
| outside_purchases | combined | 24.14 | 0.000 | 111.33 | 3.33 | 0.00 | 4.58 |
| long_stockout | dispensing_only | 4.28 | 0.083 | 260.17 | 7.08 | 0.21 | 5.67 |
| long_stockout | prescription_only | 24.14 | 0.250 | 8.33 | 11.92 | 393.46 | 0.17 |
| long_stockout | calibrated | 5.20 | 0.000 | 319.58 | 5.83 | 0.00 | 7.00 |
| long_stockout | combined | 2.81 | 0.083 | 133.75 | 9.42 | 0.61 | 2.83 |

## Measured wins and losses

- baseline, mae_daily: best combined (3.81); combined 3.81.
- baseline, false_alert_rate: best dispensing_only, calibrated, combined (0.0); combined 0.0.
- baseline, unmet_patient_days: best prescription_only (3.33); combined 227.58.
- baseline, overstock_units: best calibrated (0.0); combined 0.02.
- baseline, stockout_days: best prescription_only (0.17); combined 4.92.
- enrolment_gap, mae_daily: best prescription_only (4.04); combined 4.27.
- enrolment_gap, false_alert_rate: best dispensing_only, prescription_only, calibrated, combined (0.0); combined 0.0.
- enrolment_gap, unmet_patient_days: best dispensing_only, prescription_only, combined (237.58); combined 237.58.
- enrolment_gap, overstock_units: best prescription_only, calibrated, combined (0.0); combined 0.0.
- enrolment_gap, stockout_days: best dispensing_only, prescription_only, combined (5.08); combined 5.08.
- stale_prescriptions, mae_daily: best dispensing_only (3.57); combined 17.51.
- stale_prescriptions, false_alert_rate: best dispensing_only (0.083); combined 0.333.
- stale_prescriptions, unmet_patient_days: best prescription_only, calibrated, combined (25.17); combined 25.17.
- stale_prescriptions, overstock_units: best dispensing_only (0.97); combined 236.45.
- stale_prescriptions, stockout_days: best prescription_only, calibrated, combined (0.83); combined 0.83.
- false_reports, mae_daily: best combined (3.81); combined 3.81.
- false_reports, false_alert_rate: best dispensing_only, calibrated, combined (0.0); combined 0.0.
- false_reports, unmet_patient_days: best prescription_only (3.33); combined 227.58.
- false_reports, overstock_units: best calibrated (0.0); combined 0.02.
- false_reports, stockout_days: best prescription_only (0.17); combined 4.92.
- outside_purchases, mae_daily: best prescription_only (23.76); combined 24.14.
- outside_purchases, false_alert_rate: best dispensing_only, calibrated, combined (0.0); combined 0.0.
- outside_purchases, unmet_patient_days: best prescription_only (0.0); combined 111.33.
- outside_purchases, overstock_units: best dispensing_only, calibrated, combined (0.0); combined 0.0.
- outside_purchases, stockout_days: best prescription_only (0.0); combined 4.58.
- long_stockout, mae_daily: best combined (2.81); combined 2.81.
- long_stockout, false_alert_rate: best calibrated (0.0); combined 0.083.
- long_stockout, unmet_patient_days: best prescription_only (8.33); combined 133.75.
- long_stockout, overstock_units: best calibrated (0.0); combined 0.61.
- long_stockout, stockout_days: best prescription_only (0.17); combined 2.83.

False reports are generated separately. All four methods ignore case reports, so this stressor does not change their input data.
