from datetime import date, timedelta

date1 = date(2026, 10, 2)
date2 = date(2026, 10, 5)

current_date = date1
count = 0
while current_date < date2:
    if current_date.strftime("%A") not in ('Saturday', 'Sunday'):
        count += 1
    current_date = current_date + timedelta(days=1)

print(count)